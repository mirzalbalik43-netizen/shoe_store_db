
from datetime import date, timedelta
import sqlite3
from app_functions import (
    calc_discount, pluralize_items, format_full_name,
    get_client_tier, get_client_loyalty_days,
    register_functions, place_order, cancel_order, execute_queries
)
from db_init import get_connection


def _temporary_database():
    original = get_connection()
    try:
        temp = sqlite3.connect(':memory:')
        original.backup(temp)
        temp.row_factory = sqlite3.Row
        temp.execute('PRAGMA foreign_keys = ON')
        return temp
    finally:
        original.close()


def run_tests(verbose=True):
    results = []

    def case(name, check):
        try:
            check()
            results.append((name, True, 'OK'))
        except Exception as exc:
            results.append((name, False, f'{type(exc).__name__}: {exc}'))
        if verbose:
            print(('PASS' if results[-1][1] else 'FAIL') + ' ' + name + ('' if results[-1][1] else ' - ' + results[-1][2]))

    def eq(actual, expected):
        assert actual == expected, f'получено {actual!r}, ожидалось {expected!r}'

    for name, inp, expected in [
        ('Скидка 20%', (1000, 20), 800.0),
        ('Скидка 0%', (1000, 0), 1000.0),
        ('Скидка 100%', (1000, 100), 0.0),
        ('Отрицательная скидка', (1000, -25), 1000.0),
        ('Скидка более 100%', (1000, 150), 0.0),
        ('Дробная скидка', (99.99, 15), 84.99),
        ('Цена None', (None, 20), 0.0),
        ('Скидка None', (100, None), 0.0),
        ('Цена строкой', ('100', 20), 0.0),
        ('Скидка строкой', (100, '20'), 0.0),
        ('NaN', (float('nan'), 20), 0.0),
    ]:
        case(name, lambda x=inp,y=expected: eq(calc_discount(*x),y))

    for n, expected in [(0,'0 товаров'),(1,'1 товар'),(2,'2 товара'),
                        (3,'3 товара'),(4,'4 товара'),(5,'5 товаров'),
                        (11,'11 товаров'),(12,'12 товаров'),(14,'14 товаров'),
                        (21,'21 товар'),(22,'22 товара'),(25,'25 товаров'),
                        (101,'101 товар'),(112,'112 товаров'),(1000,'1000 товаров')]:
        case(f'Склонение {n}', lambda a=n,b=expected: eq(pluralize_items(a),b))
    case('Склонение None', lambda: eq(pluralize_items(None),'0 товаров'))
    case('Склонение нечислового', lambda: eq(pluralize_items('много'),'0 товаров'))

    for name,args,expect in [
        ('ФИО полностью',('ИВАНОВ','ПЕТР','СЕРГЕЕВИЧ'),'Иванов П.С.'),
        ('ФИО без отчества',('ИВАНОВ','ПЕТР',None),'Иванов П.'),
        ('ФИО с пробелами',('  сМиРнОва ',' АННА ', ' олЕгоВна '),'Смирнова А.О.'),
        ('ФИО без фамилии',(None,'Петр','Иванович'),'Аноним'),
        ('ФИО без имени',('Иванов','  ','Иванович'),'Аноним'),
        ('ФИО со строкой другого типа',(123,'Пётр','Иванович'),'Аноним'),
        ('ФИО через дефис',('сИДОрОВ-пЕТРОВ','иВАн',None),'Сидоров-Петров И.'),
    ]:
        case(name, lambda x=args,y=expect: eq(format_full_name(*x),y))

    for val,expect in [(None,'Без статуса'),(-1,'Без статуса'),('1000','Без статуса'),
                       (0,'Новичок'),(4999,'Новичок'),(5000,'Бронза'),
                       (19999,'Бронза'),(20000,'Серебро'),(49999,'Серебро'),
                       (50000,'Золото'),(100000,'Золото'),(100001,'Платина')]:
        case(f'Уровень {val}', lambda x=val,y=expect: eq(get_client_tier(x),y))

    case('Стаж None', lambda: eq(get_client_loyalty_days(None),0))
    case('Стаж неверная дата', lambda: eq(get_client_loyalty_days('2026-99-99'),0))
    case('Стаж сегодня', lambda: eq(get_client_loyalty_days(date.today().isoformat()),0))
    case('Стаж вчера', lambda: eq(get_client_loyalty_days((date.today()-timedelta(days=1)).isoformat()),1))
    case('Стаж в будущем', lambda: eq(get_client_loyalty_days((date.today()+timedelta(days=2)).isoformat()),0))

    with _temporary_database() as db:
        register_functions(db)
        case('SQL-функции зарегистрированы', lambda: eq(db.execute('SELECT pluralize_items(5),calc_discount(100,20)').fetchone()[:],('5 товаров',80.0)))
        q = execute_queries(db)
        case('Пять запросов выполнились', lambda: eq(len(q),5))
        case('Аналитика охватывает 3 клиента',lambda: eq(len(q[4][2]),3))
        case('Скидка SQL корректна', lambda: eq(q[0][2][0][3],2799.92))
        case('Пустое отчество: учебная демонстрация', lambda: (
            db.execute("UPDATE users SET middle_name=NULL WHERE user_id=1"),
            eq(execute_queries(db)[1][2][0][-1],'Аноним')))
        # Убрать demo-изменение перед следующими тестами; временная копия всё равно не затрагивает оригинал.
        db.rollback()

    with _temporary_database() as db:
        def scalar(query, params=()):
            return db.execute(query,params).fetchone()[0]
        starting = scalar('SELECT quantity_available FROM stock_items WHERE stock_item_id=1')
        start_orders = scalar('SELECT COUNT(*) FROM orders')
        start_items = scalar('SELECT COUNT(*) FROM order_items')
        case('Существует товарная позиция',lambda: assert_true(starting > 0))
        case('Создание заказа',lambda: assert_true(place_order(db,1,1,1,2)))
        case('Остатки списаны',lambda: eq(scalar('SELECT quantity_available FROM stock_items WHERE stock_item_id=1'),starting-2))
        case('Число заказов выросло',lambda: eq(scalar('SELECT COUNT(*) FROM orders'),start_orders+1))
        case('Число позиций выросло',lambda: eq(scalar('SELECT COUNT(*) FROM order_items'),start_items+1))
        added = scalar('SELECT MAX(order_id) FROM orders')
        expected_price=scalar('SELECT price FROM products WHERE product_id=1')
        case('Историческая цена зафиксирована',lambda: eq(scalar('SELECT price FROM order_items WHERE order_id=?',(added,)),expected_price))
        case('Несуществующий клиент',lambda: assert_false(place_order(db,999999,1,1,1)))
        case('Несуществующий товар',lambda: assert_false(place_order(db,1,999999,1,1)))
        case('Несуществующий размер',lambda: assert_false(place_order(db,1,1,999999,1)))
        case('Отрицательное количество',lambda: assert_false(place_order(db,1,1,1,-2)))
        case('Слишком большой заказ',lambda: assert_false(place_order(db,1,1,1,1000000)))
        case('Неверный тип количества',lambda: assert_false(place_order(db,1,1,1,'2')))
        case('После отказов остаток прежний',lambda: eq(scalar('SELECT quantity_available FROM stock_items WHERE stock_item_id=1'),starting-2))
        case('После отказов заказов не прибавилось',lambda: eq(scalar('SELECT COUNT(*) FROM orders'),start_orders+1))
        case('Отмена заказа',lambda: assert_true(cancel_order(db,added)))
        case('Восстановление остатка',lambda: eq(scalar('SELECT quantity_available FROM stock_items WHERE stock_item_id=1'),starting))
        case('После отмены число заказов прежнее',lambda: eq(scalar('SELECT COUNT(*) FROM orders'),start_orders))
        case('После отмены число позиций прежнее',lambda: eq(scalar('SELECT COUNT(*) FROM order_items'),start_items))
        case('Отмена отсутствующего заказа',lambda: assert_false(cancel_order(db,999999)))
        case('FK после операций не нарушены',lambda: eq(len(db.execute('PRAGMA foreign_key_check').fetchall()),0))
        # Симулируем SQL-ошибку посреди создания заказа, проверяем откат списания.
        db.execute('''CREATE TRIGGER temp.reject_new_order_item
                      BEFORE INSERT ON order_items
                      BEGIN SELECT RAISE(ABORT, 'test rollback'); END''')
        case('SQL-ошибка приводит к отказу',lambda: assert_false(place_order(db,1,1,1,1)))
        case('При SQL-ошибке списание отменено',lambda: eq(scalar('SELECT quantity_available FROM stock_items WHERE stock_item_id=1'),starting))
        case('При SQL-ошибке лишнего заказа нет',lambda: eq(scalar('SELECT COUNT(*) FROM orders'),start_orders))
        db.execute('DROP TRIGGER temp.reject_new_order_item')
        db.commit()
        # Работа внутри уже открытой транзакции вызывающего кода.
        db.execute('BEGIN')
        case('Заказ внутри внешней транзакции',lambda: assert_true(place_order(db,1,1,1,1)))
        case('Внешняя транзакция остаётся открытой',lambda: assert_true(db.in_transaction))
        db.rollback()
        case('Откат внешней транзакции вернул остаток',lambda: eq(scalar('SELECT quantity_available FROM stock_items WHERE stock_item_id=1'),starting))

    total = sum(ok for _,ok,_ in results)
    if verbose:
        print(f'\nИТОГ UNIT/INTEGRATION: {total}/{len(results)}')
        print('Основная база shoe_store.sqlite не изменена.')
    return results


def assert_true(value):
    assert value is True, f'ожидалось True, получено {value!r}'


def assert_false(value):
    assert value is False, f'ожидалось False, получено {value!r}'

if __name__ == '__main__':
    result=run_tests()
    raise SystemExit(0 if all(x[1] for x in result) else 1)
