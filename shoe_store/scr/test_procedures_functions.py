
from __future__ import annotations

import sqlite3
from procedures_functions import (
    calc_order_total, get_category_count, format_phone, register_functions,
    create_order, update_stock, get_sales_report, get_demo_query_results
)
from db_init import get_connection


def _copy_to_ram():
    source = get_connection()
    dest = sqlite3.connect(':memory:')
    try:
        source.backup(dest)
    finally:
        source.close()
    dest.execute('PRAGMA foreign_keys = ON')
    return dest


def run_tests(verbose=True):
    checks=[]
    def case(title, callback):
        try:
            callback()
            checks.append((title,True,'OK'))
        except Exception as exc:
            checks.append((title,False,f'{type(exc).__name__}: {exc}'))
        if verbose:
            row=checks[-1]
            print(('PASS' if row[1] else 'FAIL')+' '+row[0]+('' if row[1] else ' | '+row[2]))
    def equal(got,want):
        assert got==want, f'фактически {got!r}, ожидалось {want!r}'
    def truth(got):
        assert got, f'ожидалась истина, получили {got!r}'
    def false(got):
        assert not got, f'ожидался отказ, получили {got!r}'
    def must_fail(fn,error=ValueError):
        try:
            fn()
        except error:
            return
        raise AssertionError(f'Ожидалась ошибка {error}')

    cases=[
        ('Цена * количество',(100,3),300.0),
        ('Нулевое количество',(100,0),0.0),
        ('Отрицательное количество',(100,-1),0.0),
        ('None цена',(None,2),0.0),
        ('None количество',(100,None),0.0),
        ('Неверная строковая цена',('100',3),0.0),
        ('Неверное количество строкой',(100,'3'),0.0),
        ('Отрицательная цена',(-100,2),0.0),
        ('NaN цена',(float('nan'),2),0.0),
        ('Дробная цена',(10.25,3),30.75),
    ]
    for name, inp, want in cases:
        case(name,lambda x=inp,y=want: equal(calc_order_total(*x),y))
    phones=[
        ('Телефон 8','89991234567','+7 (999) 123-45-67'),
        ('Телефон 7','79991234567','+7 (999) 123-45-67'),
        ('Некорректный короткий','12345','12345'),
        ('Буквы','не указан','не указан'),
        ('None',None,None),
        ('Пропуск внутри','8 9991234567','8 9991234567'),
    ]
    for name,arg,expected in phones:
        case(name,lambda x=arg,y=expected: equal(format_phone(x),y))

    with _copy_to_ram() as db:
        # КАТЕГОРИИ и SQL UDF
        category=db.execute('SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY category LIMIT 1').fetchone()
        case('Количество в категории',lambda: equal(get_category_count(db,category[0]),category[1]))
        case('Несуществующая категория',lambda: equal(get_category_count(db,'НЕТ_КАТЕГОРИИ'),0))
        case('None категория',lambda: equal(get_category_count(db,None),0))
        case('SQL инъекция отклонена',lambda: equal(get_category_count(db,"' OR 1=1 --"),0))
        register_functions(db)
        case('SQL calculate_total',lambda: equal(db.execute('SELECT calculate_total(100,3)').fetchone()[0],300))
        case('SQL count_in_category',lambda: equal(db.execute('SELECT count_in_category(?)',(category[0],)).fetchone()[0],category[1]))
        case('SQL format_phone',lambda: equal(db.execute("SELECT format_phone('89991234567')").fetchone()[0],'+7 (999) 123-45-67'))
        queries=get_demo_query_results(db)
        case('Три демонстрационных запроса',lambda: equal(len(queries),3))
        case('Категории UDF подсчитаны',lambda: truth(len(queries[1][2])>=1))
        case('Номера привязаны к пользователям',lambda: equal(len(queries[2][2]),3))
        case('Тестовые телефоны не меняют структуру users',lambda: false(any(row[1]=='phone' for row in db.execute('PRAGMA table_info(users)'))))

        def stock():
            return db.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=1').fetchone()[0]
        def orders_count():
            return db.execute('SELECT count(*) FROM orders').fetchone()[0]
        def order_items_count():
            return db.execute('SELECT count(*) FROM order_items').fetchone()[0]
        starting_stock=stock()
        starting_orders=orders_count()
        starting_items=order_items_count()
        case('Изначальный товар имеется',lambda: truth(starting_stock>1))
        case('Создать заказ',lambda: truth(create_order(db,1,1,2)))
        case('Остаток уменьшился',lambda: equal(stock(),starting_stock-2))
        case('Заказ добавлен',lambda: equal(orders_count(),starting_orders+1))
        case('Строка заказа добавлена',lambda: equal(order_items_count(),starting_items+1))
        new_order=db.execute('SELECT max(order_id) FROM orders').fetchone()[0]
        price=db.execute('SELECT price FROM products WHERE product_id=(SELECT product_id FROM stock_items WHERE stock_item_id=1)').fetchone()[0]
        case('Зафиксирована историческая цена',lambda: equal(db.execute('SELECT price FROM order_items WHERE order_id=?',(new_order,)).fetchone()[0],price))
        case('Нельзя купить слишком много',lambda: false(create_order(db,1,1,10**6)))
        case('Неизвестный клиент',lambda: false(create_order(db,999999,1,1)))
        case('Неизвестная позиция',lambda: false(create_order(db,1,999999,1)))
        case('Отрицательная покупка',lambda: false(create_order(db,1,1,-1)))
        case('Неверный тип покупки',lambda: false(create_order(db,1,1,'2')))
        case('Откаты сохранили число заказов',lambda: equal(orders_count(),starting_orders+1))
        case('Откаты сохранили остаток',lambda: equal(stock(),starting_stock-2))
        case('Отчет за все даты',lambda: truth('продано товаров на сумму' in get_sales_report(db,'2020-01-01','2035-01-01')))
        case('Ошибка обратных дат',lambda: must_fail(lambda:get_sales_report(db,'2035-01-01','2020-01-01')))
        case('Ошибка даты-строки',lambda: must_fail(lambda:get_sales_report(db,'not-a-date','2030-01-01')))
        case('Отсутствие продаж вне диапазона',lambda: truth(get_sales_report(db,'1990-01-01','1990-12-31').endswith('0.00 руб.')))
        case('Отдельная процедура списания',lambda: truth(update_stock(db,1,1)))
        case('Списание уменьшило остаток',lambda: equal(stock(),starting_stock-3))
        case('Нет ухода в минус',lambda: must_fail(lambda:update_stock(db,1,10**6)))
        case('Ошибка списка не изменила остаток',lambda: equal(stock(),starting_stock-3))
        case('Нельзя списывать 0',lambda: must_fail(lambda:update_stock(db,1,0)))
        case('Нельзя списывать отрицательное',lambda: must_fail(lambda:update_stock(db,1,-4)))
        case('Нельзя списывать несуществующую позицию',lambda: must_fail(lambda:update_stock(db,999999,1)))
        case('FK после процедур',lambda: equal(db.execute('PRAGMA foreign_key_check').fetchall(),[]))

    with _copy_to_ram() as db:
        before=db.execute('SELECT count(*) FROM orders').fetchone()[0]
        before_stock=db.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=1').fetchone()[0]
        db.execute('BEGIN')
        case('Внешняя транзакция: create_order',lambda: truth(create_order(db,1,1,1)))
        case('Внешняя транзакция остаётся активна',lambda: truth(db.in_transaction))
        case('Новая запись видна внутри',lambda: equal(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],before+1))
        db.rollback()
        case('Внешний rollback откатил заказ',lambda: equal(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],before))
        case('Внешний rollback откатил остаток',lambda: equal(db.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=1').fetchone()[0],before_stock))
        # Принудительная ошибка вставки заказной позиции после списания.
        db.execute('''CREATE TRIGGER deny_day10_insert BEFORE INSERT ON order_items
                      BEGIN SELECT RAISE(ABORT, 'debug rollback'); END''')
        case('Сбой внутри транзакции вызывает False',lambda: false(create_order(db,1,1,1)))
        case('При сбое заказ не вставлен',lambda: equal(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],before))
        case('При сбое склад не списан',lambda: equal(db.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=1').fetchone()[0],before_stock))
        db.execute('DROP TRIGGER deny_day10_insert')
    return checks


def main():
    results=run_tests()
    passed=sum(p for _,p,_ in results)
    print(f'\nРЕЗУЛЬТАТ: {passed}/{len(results)} проверок')
    return 0 if passed==len(results) else 1


if __name__=='__main__':
    raise SystemExit(main())
