
from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from itertools import count
from pathlib import Path
import math
import re
import sqlite3

from db_init import get_connection

_SAVEPOINT_NUMBERS = count(1)


def _valid_positive_integer(value):
    return type(value) is int and value > 0


def _valid_money(value):
    """Преобразование корректного конечного числа в Decimal."""
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        dec = Decimal(str(value))
    except InvalidOperation:
        return None
    return dec if dec.is_finite() else None


def calc_order_total(price, quantity):
    """Цена * число единиц, нуль для quantity <= 0 или неверных аргументов."""
    price_dec = _valid_money(price)
    if price_dec is None or price_dec < 0 or not _valid_positive_integer(quantity):
        return 0.0
    return round(float(price_dec * quantity), 2)


def get_category_count(conn: sqlite3.Connection, category_name):
    """Число моделей выбранной категории; SQL-параметр предотвращает инъекции."""
    if not isinstance(category_name, str) or not category_name.strip():
        return 0
    row = conn.execute('SELECT COUNT(*) FROM products WHERE category = ?',
                       (category_name.strip(),)).fetchone()
    return int(row[0])


def format_phone(phone):
    """89991234567 -> +7 (999) 123-45-67. Иное содержимое не изменяет."""
    if not isinstance(phone, str):
        return phone if phone is None else str(phone)
    text = phone.strip()
    # Принимаем только исходный телефон из 11 цифр без разделителей.
    if not re.fullmatch(r'[78]\d{10}', text):
        return phone
    digits = '7' + text[1:]
    return f'+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}'


def register_functions(conn: sqlite3.Connection):
    """Создать SQL UDF только на данном соединении. Не изменяет файл БД."""
    conn.create_function('calculate_total', 2, calc_order_total, deterministic=True)
    # В SQLite функция получает соединение через замыкание. Во время SELECT
    # используем отдельный cursor conn.execute(...), а не исходный cursor.
    conn.create_function('count_in_category', 1,
                         lambda category: get_category_count(conn, category))
    conn.create_function('format_phone', 1, format_phone, deterministic=True)
    return conn


@contextmanager
def _atomic(conn: sqlite3.Connection):
    """Один коммит / откат; при внешней транзакции изолированный SAVEPOINT."""
    if conn.in_transaction:
        savepoint = f'up11_proc_{next(_SAVEPOINT_NUMBERS)}'
        conn.execute(f'SAVEPOINT {savepoint}')
        try:
            yield
        except BaseException:
            conn.execute(f'ROLLBACK TO SAVEPOINT {savepoint}')
            conn.execute(f'RELEASE SAVEPOINT {savepoint}')
            raise
        else:
            conn.execute(f'RELEASE SAVEPOINT {savepoint}')
    else:
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            conn.rollback()
            raise
        else:
            conn.commit()


def _require_fk(conn: sqlite3.Connection):
    if conn.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
        raise ValueError('Для операций требуется PRAGMA foreign_keys = ON')


def _decrease_stock(conn: sqlite3.Connection, stock_item_id: int, quantity: int):
    """Атомарное списание. Вызывается ВНУТРИ активной транзакции."""
    if not _valid_positive_integer(stock_item_id) or not _valid_positive_integer(quantity):
        raise ValueError('ID позиции и количество должны быть положительными целыми')
    result = conn.execute('''
        UPDATE stock_items
        SET quantity_available = quantity_available - ?
        WHERE stock_item_id = ? AND quantity_available >= ?
    ''', (quantity, stock_item_id, quantity))
    if result.rowcount != 1:
        raise ValueError('Недостаточно товара на складе или позиция не существует')


def update_stock(conn: sqlite3.Connection, stock_item_id, quantity_sold):
    """Проверить и списать остаток с откатом при ошибке.

    ValueError выходит наружу, что позволяет обработать проблему в приложении.
    """
    _require_fk(conn)
    with _atomic(conn):
        _decrease_stock(conn, stock_item_id, quantity_sold)
    return True


def create_order(conn: sqlite3.Connection, user_id, stock_item_id, quantity):
    """Создать заказ, зафиксировать цену, списать остаток атомарно.

    Возвращает True при успехе; False при нехватке товара, неверном вводе,
    несуществующих записях или проблеме SQLite. Чужую транзакцию не фиксирует.
    """
    if not all(_valid_positive_integer(v) for v in (user_id, stock_item_id, quantity)):
        return False
    try:
        _require_fk(conn)
        with _atomic(conn):
            if conn.execute('SELECT 1 FROM users WHERE user_id=?', (user_id,)).fetchone() is None:
                raise ValueError('Клиент не найден')
            stock = conn.execute('''
                SELECT s.stock_item_id, p.price
                FROM stock_items s JOIN products p ON p.product_id=s.product_id
                WHERE s.stock_item_id=?
            ''', (stock_item_id,)).fetchone()
            if stock is None:
                raise ValueError('Товарная позиция не найдена')
            # На новой схеме остаток списывается AFTER INSERT триггером.
            # Без триггера сохраняем прежнее поведение (обратная совместимость).
            has_trigger = conn.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' "
                                       "AND name='trg_order_items_after_insert_stock'").fetchone()
            if has_trigger:
                available = conn.execute(
                    'SELECT quantity_available FROM stock_items WHERE stock_item_id=?',
                    (stock_item_id,)).fetchone()[0]
                if available < quantity:
                    raise ValueError('Недостаточно товара на складе')
            else:
                _decrease_stock(conn, stock_item_id, quantity)
            cursor = conn.execute(
                'INSERT INTO orders (order_date, user_id) VALUES (?, ?)',
                (date.today().isoformat(), user_id))
            conn.execute('''
                INSERT INTO order_items(order_id, stock_item_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (cursor.lastrowid, stock_item_id, quantity, stock[1]))
        return True
    except (sqlite3.Error, ValueError, TypeError, OverflowError):
        return False


def get_sales_report(conn: sqlite3.Connection, start_date, end_date):
    """Отчет за включительный диапазон ISO YYYY-MM-DD без записи в базу."""
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except (ValueError, TypeError):
        raise ValueError('Даты должны быть в формате YYYY-MM-DD') from None
    if start > end:
        raise ValueError('Начальная дата позже конечной')
    total = conn.execute('''
        SELECT COALESCE(SUM(oi.quantity * oi.price), 0)
        FROM orders AS o
        JOIN order_items AS oi ON oi.order_id=o.order_id
        WHERE o.order_date BETWEEN ? AND ?
    ''', (start.isoformat(), end.isoformat())).fetchone()[0]
    return (f'С {start.isoformat()} по {end.isoformat()} '
            f'продано товаров на сумму {float(total):.2f} руб.')


def get_demo_query_results(conn):
    """Три SQL-примера практики (в том числе телефоны из CTE, не из users)."""
    register_functions(conn)
    statements = [
        ("Суммы позиций заказа", '''
            SELECT oi.order_id,
                   ROUND(SUM(calculate_total(oi.price, oi.quantity)), 2) AS total
            FROM order_items oi GROUP BY oi.order_id ORDER BY oi.order_id
        '''),
        ("Количество товаров по категориям", '''
            SELECT categories.category, count_in_category(categories.category) AS product_count
            FROM (SELECT DISTINCT category FROM products) categories
            ORDER BY categories.category
        '''),
        ("Форматирование телефонов клиентов (учебные входные данные)", '''
            WITH demo_phones(user_id, phone) AS (
                VALUES (1, '89991234567'), (2, '89161234567'), (3, 'не указан')
            )
            SELECT u.user_id, u.last_name, u.first_name,
                   demo_phones.phone AS original_phone,
                   format_phone(demo_phones.phone) AS formatted_phone
            FROM users u LEFT JOIN demo_phones ON demo_phones.user_id=u.user_id
            ORDER BY u.user_id
        ''')
    ]
    results=[]
    for label,sql in statements:
        cur=conn.execute(sql)
        results.append((label, [d[0] for d in cur.description], [tuple(r) for r in cur.fetchall()]))
    return results


def demo():
    """Безопасная демонстрация, все изменения только в RAM-копии БД."""
    original=get_connection()
    memory=sqlite3.connect(':memory:')
    try:
        original.backup(memory)
        memory.execute('PRAGMA foreign_keys=ON')
        for label, columns, rows in get_demo_query_results(memory):
            print(f'\n{label}: {columns}')
            for r in rows[:5]: print(' ', r)
        stock_before=memory.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=1').fetchone()[0]
        print('\nСоздать заказ:', create_order(memory,1,1,1))
        stock_after=memory.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=1').fetchone()[0]
        print('Остаток до / после:', stock_before, stock_after)
        print('Отказ при огромной продаже:',create_order(memory,1,1,1000000))
        print(get_sales_report(memory,'2020-01-01','2030-12-31'))
    finally:
        memory.close()
        original.close()
    print('Основная shoe_store.sqlite не изменена.')


if __name__ == '__main__':
    demo()
