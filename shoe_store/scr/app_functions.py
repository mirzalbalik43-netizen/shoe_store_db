
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from numbers import Real
import sqlite3

from db_init import DB_PATH, get_connection


def _as_number(value):
    """Только числовые входные значения, исключая bool/строки/NaN/Inf."""
    import math
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    val = float(value)
    return val if math.isfinite(val) else None


def calc_discount(price, discount_percent):
    """Итоговая цена после скидки 0..100%; None/нечисловые значения -> 0.0."""
    p, d = _as_number(price), _as_number(discount_percent)
    if p is None or d is None:
        return 0.0
    return round(p * (1 - max(0.0, min(100.0, d)) / 100), 2)


def pluralize_items(count):
    """Например: 1 товар, 2 товара, 5 товаров, 21 товар."""
    n = _as_number(count)
    if n is None or not n.is_integer() or n < 0:
        return '0 товаров'
    n = int(n)
    if 11 <= n % 100 <= 14:
        word = 'товаров'
    elif n % 10 == 1:
        word = 'товар'
    elif 2 <= n % 10 <= 4:
        word = 'товара'
    else:
        word = 'товаров'
    return f'{n} {word}'


def _clean_name(value):
    if not isinstance(value, str):
        return ''
    # Поддержка имён с дефисом и буквами разного регистра.
    return ' '.join('-'.join(part.capitalize() for part in token.split('-'))
                    for token in value.strip().split())


def format_full_name(last, first, middle):
    """Фамилия И.О. Если нет фамилии или имени, вернуть 'Аноним'."""
    surname, name, patronymic = _clean_name(last), _clean_name(first), _clean_name(middle)
    if not surname or not name:
        return 'Аноним'
    return f'{surname} {name[0]}.{patronymic[0] + "." if patronymic else ""}'


def get_client_tier(total_spent):
    """Границы диапазонов: 5000, 20000, 50000, 100000 включены сверху."""
    amount = _as_number(total_spent)
    if amount is None or amount < 0:
        return 'Без статуса'
    if amount < 5000:
        return 'Новичок'
    if amount < 20000:
        return 'Бронза'
    if amount < 50000:
        return 'Серебро'
    if amount <= 100000:
        return 'Золото'
    return 'Платина'


def get_client_loyalty_days(first_order_date_str):
    """Число полных календарных дней от YYYY-MM-DD до сегодня."""
    if not isinstance(first_order_date_str, str) or not first_order_date_str.strip():
        return 0
    try:
        first = date.fromisoformat(first_order_date_str.strip())
    except ValueError:
        return 0
    return max(0, (date.today() - first).days)


def register_functions(conn: sqlite3.Connection):
    """Регистрация пяти пользовательских scalar-функций на данном соединении."""
    conn.create_function('calc_discount', 2, calc_discount, deterministic=True)
    conn.create_function('pluralize_items', 1, pluralize_items, deterministic=True)
    conn.create_function('format_full_name', 3, format_full_name, deterministic=True)
    conn.create_function('get_client_tier', 1, get_client_tier, deterministic=True)
    # Зависит от текущей даты, поэтому НЕ deterministic
    conn.create_function('get_client_loyalty_days', 1, get_client_loyalty_days)
    return conn


class _ProcedureAbort(Exception):
    """Ожидаемый отказ бизнес-правил; исходная транзакция откатывается."""


def _begin_atomic(conn):
    """BEGIN IMMEDIATE для отдельной операции, SAVEPOINT для вложенной."""
    if conn.in_transaction:
        # Удобно для кода вызывающей программы с уже активной транзакцией.
        conn.execute('SAVEPOINT shoe_store_proc')
        return False
    conn.execute('BEGIN IMMEDIATE')
    return True


def _finish_atomic(conn, outer: bool, success: bool):
    if outer:
        if success:
            conn.commit()
        else:
            conn.rollback()
    else:
        if success:
            conn.execute('RELEASE SAVEPOINT shoe_store_proc')
        else:
            conn.execute('ROLLBACK TO SAVEPOINT shoe_store_proc')
            conn.execute('RELEASE SAVEPOINT shoe_store_proc')


def _valid_id(value):
    return type(value) is int and value > 0


def place_order(conn: sqlite3.Connection, user_id, product_id, size_id, quantity):
    """Атомарно создать заказ и списать остаток. True при успехе, иначе False.

    Цена фиксируется на момент покупки. Повторная проверка остатка делается
    непосредственно в UPDATE для защиты от двойного списания.
    """
    if not all(_valid_id(v) for v in (user_id, product_id, size_id, quantity)):
        return False
    outer = False
    try:
        if conn.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
            return False
        outer = _begin_atomic(conn)
        user = conn.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if not user:
            raise _ProcedureAbort('Пользователь не найден')
        item = conn.execute('''
            SELECT s.stock_item_id, s.quantity_available, p.price
            FROM stock_items s JOIN products p ON s.product_id = p.product_id
            WHERE s.product_id = ? AND s.size_id = ?
        ''', (product_id, size_id)).fetchone()
        if item is None:
            raise _ProcedureAbort('Товар заданного размера не найден')
        stock_id, available, price = item[0], item[1], item[2]
        if available < quantity:
            raise _ProcedureAbort('Недостаточно товара на складе')
        # Начиная с дня 11 остаток списывает AFTER INSERT триггер.
        # В старой базе без триггеров поддерживается прежняя логика.
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' "
                            "AND name='trg_order_items_after_insert_stock'").fetchone():
            changed = conn.execute('''UPDATE stock_items
                SET quantity_available = quantity_available - ?
                WHERE stock_item_id = ? AND quantity_available >= ?''',
                (quantity, stock_id, quantity))
            if changed.rowcount != 1:
                raise _ProcedureAbort('Недостаточно товара на складе')
        cursor = conn.execute('INSERT INTO orders (order_date, user_id) VALUES (?, ?)',
                              (datetime.now().date().isoformat(), user_id))
        conn.execute('''INSERT INTO order_items (order_id, stock_item_id, quantity, price)
                     VALUES (?, ?, ?, ?)''', (cursor.lastrowid, stock_id, quantity, price))
        _finish_atomic(conn, outer, True)
        return True
    except (sqlite3.Error, _ProcedureAbort, TypeError, ValueError):
        if conn.in_transaction:
            _finish_atomic(conn, outer, False)
        return False


def cancel_order(conn: sqlite3.Connection, order_id):
    """Атомарно отменить заказ, восстановить остатки и удалить позиции."""
    if not _valid_id(order_id):
        return False
    outer = False
    try:
        if conn.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
            return False
        outer = _begin_atomic(conn)
        if not conn.execute('SELECT 1 FROM orders WHERE order_id=?', (order_id,)).fetchone():
            raise _ProcedureAbort('Заказ не найден')
        # В день 11 AFTER DELETE позиции делает восстановление автоматически.
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' "
                            "AND name='trg_order_items_after_delete_stock'").fetchone():
            for stock_id, quantity in conn.execute('''
                  SELECT stock_item_id, SUM(quantity) FROM order_items
                  WHERE order_id=? GROUP BY stock_item_id''', (order_id,)).fetchall():
                upd = conn.execute('''UPDATE stock_items
                      SET quantity_available = quantity_available + ?
                      WHERE stock_item_id=?''', (quantity, stock_id))
                if upd.rowcount != 1:
                    raise _ProcedureAbort('Не удалось восстановить остатки')
        conn.execute('DELETE FROM order_items WHERE order_id=?', (order_id,))
        deleted = conn.execute('DELETE FROM orders WHERE order_id=?', (order_id,))
        if deleted.rowcount != 1:
            raise _ProcedureAbort('Заказ не удалён')
        _finish_atomic(conn, outer, True)
        return True
    except (sqlite3.Error, _ProcedureAbort, TypeError, ValueError):
        if conn.in_transaction:
            _finish_atomic(conn, outer, False)
        return False


def execute_queries(conn, sql_path=None):
    """Выполнить 5 аналитических SQL-запросов и вернуть колонки/строки."""
    file = Path(sql_path) if sql_path else Path(__file__).resolve().parent.parent / 'queries' / '10_advanced_queries.sql'
    text = file.read_text(encoding='utf-8')
    statements = []
    buff = []
    for line in text.splitlines():
        if line.lstrip().startswith('--'):
            continue
        buff.append(line)
        candidate = '\n'.join(buff).strip()
        if candidate and sqlite3.complete_statement(candidate):
            statements.append(candidate)
            buff = []
    if ''.join(buff).strip() or len(statements) != 5:
        raise ValueError(f'Ожидаются 5 законченных SQL-запросов, найдено: {len(statements)}')
    register_functions(conn)
    result = []
    for i, query in enumerate(statements, 1):
        cursor = conn.execute(query)
        result.append((i, [d[0] for d in cursor.description], [tuple(r) for r in cursor.fetchall()]))
    return result


def main():
    with get_connection() as conn:
        for index, columns, rows in execute_queries(conn):
            print(f'Запрос {index}: {len(rows)} строк, колонки: {", ".join(columns)}')
            for row in rows[:5]:
                print('   ', row)
    print('Готово. Данные базы не менялись.')

if __name__ == '__main__':
    main()
