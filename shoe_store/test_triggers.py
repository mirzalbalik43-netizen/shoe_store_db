
from __future__ import annotations
import sqlite3
from db_init import get_connection
from db_apply_triggers import apply_triggers


def _copy_to_ram():
    source = get_connection()
    target = sqlite3.connect(':memory:')
    try:
        source.backup(target)
    finally:
        source.close()
    target.execute('PRAGMA foreign_keys=ON')
    return target


def run_tests(verbose=True):
    results=[]
    def case(name, callback):
        try:
            callback()
            results.append((name, True, 'OK'))
        except Exception as error:
            results.append((name, False, f'{type(error).__name__}: {error}'))
        if verbose:
            x=results[-1]
            print(('PASS ' if x[1] else 'FAIL ') + x[0] + ('' if x[1] else ' | '+x[2]))
    def equal(got, expected):
        assert got == expected, f'{got!r} != {expected!r}'
    def truth(val):
        assert val, f'ложное значение: {val!r}'
    def must_fail(callback, message=None):
        try:
            callback()
        except sqlite3.IntegrityError as err:
            if message is not None:
                truth(message in str(err))
            return
        raise AssertionError('Ожидалась sqlite3.IntegrityError')

    with _copy_to_ram() as c:
        case('Включены внешние ключи', lambda: equal(c.execute('PRAGMA foreign_keys').fetchone()[0], 1))
        case('Таблица audit_log существует', lambda: truth(c.execute("SELECT 1 FROM sqlite_master WHERE name='audit_log'").fetchone()))
        case('Десять триггеров', lambda: truth(c.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]>=10))
        before=c.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
        old_price=c.execute('SELECT price FROM products WHERE product_id=1').fetchone()[0]
        c.execute('UPDATE products SET price=? WHERE product_id=1', (old_price + 10,))
        case('Аудит обновления цены', lambda: equal(c.execute('SELECT old_value,new_value FROM audit_log ORDER BY log_id DESC LIMIT 1').fetchone(), (str(old_price), str(old_price+10))))
        case('Ровно одно событие UPDATE цены', lambda: equal(c.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0],before+1))
        c.execute('UPDATE products SET price=price WHERE product_id=1')
        case('Неизменная цена не попадает в аудит', lambda: equal(c.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0],before+1))
        c.execute('UPDATE products SET price=? WHERE product_id=1', (old_price,))

        c.execute('UPDATE users SET first_name=first_name || ? WHERE user_id=1', ('2',))
        touched=c.execute('SELECT updated_at FROM users WHERE user_id=1').fetchone()[0]
        case('updated_at устанавливается автоматически', lambda: truth(bool(touched) and len(touched)>15))
        c.execute("UPDATE users SET updated_at='2000-01-01' WHERE user_id=1")
        case('Нет рекурсии на обновлении updated_at', lambda: equal(c.execute('SELECT updated_at FROM users WHERE user_id=1').fetchone()[0], '2000-01-01'))
        case('Запрет удаления клиента с заказом', lambda: must_fail(lambda:c.execute('DELETE FROM users WHERE user_id=1'), 'Нельзя удалить пользователя с активными заказами'))
        newuser = c.execute("INSERT INTO users(last_name,first_name,login,role_id) VALUES('Тест','Новый','test_no_order',3)").lastrowid
        c.execute('DELETE FROM users WHERE user_id=?', (newuser,))
        case('Можно удалить клиента без заказов', lambda: equal(c.execute('SELECT COUNT(*) FROM users WHERE user_id=?',(newuser,)).fetchone()[0],0))
        case('Запрет отрицательной складской позиции', lambda: must_fail(
            lambda:c.execute('INSERT INTO stock_items(product_id,size_id,quantity_available) VALUES(1,5,-2)'), 'Количество не может быть отрицательным'))

        stock_id=1
        start=c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0]
        oid=c.execute('INSERT INTO orders(user_id) VALUES(1)').lastrowid
        price=c.execute('SELECT price FROM products WHERE product_id=1').fetchone()[0]
        c.execute('INSERT INTO order_items(order_id,stock_item_id,quantity,price) VALUES(?,?,?,?)',(oid,stock_id,2,price))
        case('AFTER INSERT списывает ровно два товара', lambda: equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start-2))
        case('Запрет продажи сверх остатка', lambda: must_fail(
            lambda:c.execute('INSERT INTO order_items(order_id,stock_item_id,quantity,price) VALUES(?,?,?,?)',(oid,2,100000,price)),
            'Недостаточно товара на складе'))
        case('Отказ не изменяет вторую складскую позицию', lambda: equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=2').fetchone()[0],12))
        c.execute('UPDATE order_items SET quantity=3 WHERE order_id=?',(oid,))
        case('UPDATE количества списывает только разницу', lambda: equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start-3))
        case('Нельзя увеличить количество сверх остатка', lambda: must_fail(
            lambda:c.execute('UPDATE order_items SET quantity=100000 WHERE order_id=?',(oid,)),
            'Недостаточно товара на складе'))
        c.execute('UPDATE order_items SET quantity=1 WHERE order_id=?',(oid,))
        case('Уменьшение количества возвращает разницу', lambda: equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start-1))
        c.execute('DELETE FROM orders WHERE order_id=?',(oid,))
        case('CASCADE удалил позиции тестового заказа', lambda: equal(c.execute('SELECT count(*) FROM order_items WHERE order_id=?',(oid,)).fetchone()[0],0))
        case('Удаление заказа восстановило остаток', lambda: equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start))
        case('Аудит удаления заказа',lambda: equal(c.execute("SELECT operation FROM audit_log WHERE table_name='orders' AND record_id=? ORDER BY log_id DESC LIMIT 1",(oid,)).fetchone()[0],'DELETE'))

        # Поддержка старых операций дней 9 и 10 после установки триггеров.
        from app_functions import place_order, cancel_order
        from procedures_functions import create_order
        order_before=c.execute('SELECT COALESCE(MAX(order_id),0) FROM orders').fetchone()[0]
        case('День 9: place_order с новым триггером',lambda: truth(place_order(c,1,1,1,2)))
        case('День 9: нет двойного списания',lambda:equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start-2))
        latest=c.execute('SELECT MAX(order_id) FROM orders').fetchone()[0]
        case('День 9: cancel_order',lambda: truth(cancel_order(c,latest)))
        case('День 9: нет двойного возврата',lambda: equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start))
        case('День 10: create_order',lambda:truth(create_order(c,1,stock_id,3)))
        case('День 10: списано ровно три товара',lambda:equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start-3))
        case('День 10: отказ без изменения остатка',lambda:equal(create_order(c,1,stock_id,10**6),False))
        case('День 10: остаток после отказа',lambda:equal(c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',(stock_id,)).fetchone()[0],start-3))
        c.execute('DELETE FROM orders WHERE order_id=?',(c.execute('SELECT MAX(order_id) FROM orders').fetchone()[0],))
        case('Целостность после операций',lambda:equal(c.execute('PRAGMA integrity_check').fetchone()[0],'ok'))
        case('Все внешние ключи целы',lambda:equal(c.execute('PRAGMA foreign_key_check').fetchall(),[]))
        c.rollback()

    with _copy_to_ram() as c:
        before=c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
        apply_triggers(c)
        case('Повторное применение миграции без дубликатов',lambda:equal(c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0],before))
        case('Лог сохранился при повторном применении',lambda:truth(c.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0] >= 5))

    if verbose:
        print(f'ИТОГ: {sum(x[1] for x in results)}/{len(results)}')
    return results


if __name__=='__main__':
    rows=run_tests()
    raise SystemExit(0 if all(row[1] for row in rows) else 1)
