
import sqlite3
from db_init import TABLES, get_connection, init_db
from db_seed import seed_database
from db_naming_check import check_database


def run_tests():
    results = []
    conn = get_connection(':memory:')
    try:
        init_db(conn)
        seed_database(conn)
        def expect_integrity(name, statement, params=()):
            conn.execute('SAVEPOINT testcase')
            ok, info = False, ''
            try:
                conn.execute(statement, params)
                info = 'Неожиданно разрешена недопустимая операция'
            except sqlite3.IntegrityError as e:
                ok, info = True, str(e)
            finally:
                conn.execute('ROLLBACK TO testcase')
                conn.execute('RELEASE testcase')
            results.append((name, 'PASS' if ok else 'FAIL', info))

        def expect_ok(name, condition, details=''):
            results.append((name, 'PASS' if condition else 'FAIL', details))

        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master "
              "WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        expect_ok('Созданы ровно 7 таблиц', tables == set(TABLES), ', '.join(sorted(tables)))
        expect_ok('Все имена соответствуют правилам',
                  all(not e for _, _, e in check_database(conn)))
        fkcols = {'users': ['role_id'], 'orders': ['user_id'],
                  'stock_items': ['product_id','size_id'],
                  'order_items': ['order_id','stock_item_id']}
        for table, columns in fkcols.items():
            refs = {row[3] for row in conn.execute(f'PRAGMA foreign_key_list("{table}")')}
            expect_ok('FK ' + table, set(columns) == refs, str(refs))
            indexes = [tuple(r) for r in conn.execute(f'PRAGMA index_list("{table}")')]
            indexed_columns = set()
            for ix in indexes:
                indexed_columns.update(r[2] for r in conn.execute(f'PRAGMA index_info("{ix[1]}")'))
            expect_ok('Индексы FK ' + table, set(columns) <= indexed_columns, str(indexed_columns))

        expect_integrity('Уникальность login',
            "INSERT INTO users(last_name,first_name,login,role_id) VALUES('Тест','Тест','admin',1)")
        expect_integrity('Логин 2 символа',
            "INSERT INTO users(last_name,first_name,login,role_id) VALUES('Тест','Тест','ab',1)")
        expect_integrity('Логин 21 символ',
            "INSERT INTO users(last_name,first_name,login,role_id) VALUES('Тест','Тест',?,1)",
            ('a'*21,))
        expect_integrity('NOT NULL фамилия',
            "INSERT INTO users(first_name,login,role_id) VALUES('Тест','tempuser',1)")
        expect_integrity('Внешний ключ роли',
            "INSERT INTO users(last_name,first_name,login,role_id) VALUES('Тест','Тест','newuser',999)")
        expect_integrity('Пустое имя товара',
            "INSERT INTO products(category,subcategory,manufacturer,product_name,image_path,price) "
            "VALUES('Обувь','Кеды','Фабрика','  ','img.jpg',100)")
        product_sql = ("INSERT INTO products(category,subcategory,manufacturer,product_name,image_path,price) "
                       "VALUES('Обувь','Кеды','Фабрика','Новая модель','img.jpg',?)")
        expect_integrity('Отрицательная цена', product_sql, (-100,))
        expect_integrity('Цена >= 1 000 000', product_sql, (1000000,))
        expect_integrity('Текст вместо цены', product_sql, ('bad-price',))
        expect_integrity('Отрицательное количество на складе',
            'INSERT INTO stock_items(product_id,size_id,quantity_available) VALUES(1,4,-5)')
        expect_integrity('Размер 100', 'INSERT INTO sizes(size_value) VALUES(100)')
        expect_integrity('Размер 20', 'INSERT INTO sizes(size_value) VALUES(20)')
        expect_integrity('Количество товара в заказе = 0',
            'INSERT INTO order_items(order_id,stock_item_id,quantity,price) VALUES(1,3,0,100)')
        expect_integrity('Цена единицы в заказе = 0',
            'INSERT INTO order_items(order_id,stock_item_id,quantity,price) VALUES(1,3,1,0)')
        expect_integrity('Дата не в ISO',
            "INSERT INTO orders(order_date,user_id) VALUES('12.10.2026',1)")
        expect_integrity('Некалендарная дата',
            "INSERT INTO orders(order_date,user_id) VALUES('2026-02-30',1)")
        expect_integrity('FK позиции заказа',
            'INSERT INTO order_items(order_id,stock_item_id,quantity,price) VALUES(1,999,1,100)')
        expect_integrity('RESTRICT удаление роли', 'DELETE FROM roles WHERE role_id=1')
        expect_integrity('RESTRICT удаление пользователя', 'DELETE FROM users WHERE user_id=1')
        expect_integrity('RESTRICT удаление товара', 'DELETE FROM products WHERE product_id=1')
        expect_integrity('RESTRICT удаление размера', 'DELETE FROM sizes WHERE size_id=1')
        expect_integrity('RESTRICT удаление складской позиции',
                         'DELETE FROM stock_items WHERE stock_item_id=1')

        conn.execute('SAVEPOINT cascaded')
        try:
            conn.execute('DELETE FROM orders WHERE order_id=1')
            no_children = (conn.execute('SELECT count(*) FROM order_items WHERE order_id=1')
                           .fetchone()[0] == 0)
            expect_ok('CASCADE удаление позиций с заказом', no_children)
        finally:
            conn.execute('ROLLBACK TO cascaded')
            conn.execute('RELEASE cascaded')

        conn.execute('SAVEPOINT defaultdate')
        try:
            order_id = conn.execute('INSERT INTO orders(user_id) VALUES(1)').lastrowid
            d = conn.execute('SELECT order_date FROM orders WHERE order_id=?', (order_id,)).fetchone()[0]
            expect_ok('Дата заказа DEFAULT', len(d) == 10 and d[4] == '-' and d[7] == '-', d)
        finally:
            conn.execute('ROLLBACK TO defaultdate')
            conn.execute('RELEASE defaultdate')

        conn.execute('SAVEPOINT viewcheck')
        try:
            count = conn.execute('SELECT total_quantity FROM v_products_with_stock WHERE product_id=1').fetchone()[0]
            expect_ok('Представление v_products_with_stock', count == 26, f'ожидалось 26, получено {count}')
            totals = conn.execute('SELECT total_amount FROM v_orders_full WHERE order_id=1').fetchone()[0]
            expect_ok('Представление v_orders_full', abs(totals - 7598.90) < .001, str(totals))
        finally:
            conn.execute('ROLLBACK TO viewcheck')
            conn.execute('RELEASE viewcheck')
        expect_ok('PRAGMA foreign_keys = ON', conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1)
        expect_ok('PRAGMA foreign_key_check', not conn.execute('PRAGMA foreign_key_check').fetchall())
        expect_ok('PRAGMA integrity_check', conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
        return results
    finally:
        conn.close()


if __name__ == '__main__':
    checks = run_tests()
    for name, state, details in checks:
        print(f'[{state}] {name}' + (f' — {details}' if details else ''))
    passed = sum(state == 'PASS' for _, state, _ in checks)
    print(f'ИТОГ: {passed}/{len(checks)} успешно')
    raise SystemExit(0 if passed == len(checks) else 1)
