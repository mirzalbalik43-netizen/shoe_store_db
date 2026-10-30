
import argparse
import sqlite3
from pathlib import Path
from db_init import PROJECT_DIR, get_connection, drop_all_tables, create_tables
from db_seed import seed_database

DEFAULT_TEST_DB = PROJECT_DIR / 'db' / 'shoe_store_test.sqlite'


def run_tests(db_path=DEFAULT_TEST_DB, write_report=True):
    drop_all_tables(db_path)
    create_tables(db_path)
    conn = get_connection(db_path)
    seed_database(conn)
    results=[]
    try:
        def reject(name, sql, params=()):
            conn.execute('SAVEPOINT check_case')
            try:
                try:
                    conn.execute(sql, params)
                    actual, ok = 'Недопустимая операция прошла', False
                except sqlite3.IntegrityError as exc:
                    actual, ok = f'IntegrityError: {exc}', True
                results.append((name,'Отказ (IntegrityError)',actual,ok))
            finally:
                conn.execute('ROLLBACK TO check_case')
                conn.execute('RELEASE check_case')

        def accept(name, sql, validate=None):
            conn.execute('SAVEPOINT check_case')
            try:
                try:
                    cursor=conn.execute(sql)
                    actual='Операция выполнена'
                    ok=validate(conn,cursor) if validate else True
                    if not ok: actual='Условие результата не выполнено'
                except Exception as exc:
                    actual=f'{type(exc).__name__}: {exc}'
                    ok=False
                results.append((name,'Разрешённая операция',actual,ok))
            finally:
                conn.execute('ROLLBACK TO check_case')
                conn.execute('RELEASE check_case')

        reject('UNIQUE users.login',
               "INSERT INTO users(last_name,first_name,login,role_id) VALUES('Тест','А','admin',1)")
        reject('NOT NULL users.last_name',
               "INSERT INTO users(first_name,login,role_id) VALUES('А','test_01',1)")
        reject('CHECK users.login короче 3',
               "INSERT INTO users(last_name,first_name,login,role_id) VALUES('А','Б','ab',1)")
        reject('CHECK users.login длиннее 20',
               "INSERT INTO users(last_name,first_name,login,role_id) VALUES('А','Б','abcdefghijklmnopqrstu',1)")
        reject('CHECK products.price = -100',
               "INSERT INTO products(category,manufacturer,product_name,price) VALUES('Обувь','Тест','Bad',-100)")
        reject('CHECK products.price >= 1000000',
               "INSERT INTO products(category,manufacturer,product_name,price) VALUES('Обувь','Тест','Bad',1000000)")
        reject('CHECK products.product_name пустой',
               "INSERT INTO products(category,manufacturer,product_name,price) VALUES('Обувь','Тест','  ',99)")
        reject('CHECK stock_items.quantity_available < 0',
               'INSERT INTO stock_items(product_id,size_id,quantity_available) VALUES(5,5,-5)')
        reject('CHECK order_items.quantity = 0',
               'INSERT INTO order_items(order_id,stock_item_id,quantity,price) VALUES(3,1,0,100)')
        reject('CHECK order_items.price <= 0',
               'INSERT INTO order_items(order_id,stock_item_id,quantity,price) VALUES(3,1,1,-1)')
        reject('CHECK sizes.size_value = 100',
               'INSERT INTO sizes(size_value) VALUES(100)')
        reject('CHECK orders.order_date wrong format',
               "INSERT INTO orders(order_date,user_id) VALUES('15.10.2026',1)")
        reject('CHECK orders.order_date invalid calendar day',
               "INSERT INTO orders(order_date,user_id) VALUES('2026-02-30',1)")
        reject('FOREIGN KEY users.role_id',
               "INSERT INTO users(last_name,first_name,login,role_id) VALUES('А','Б','role_999',9999)")
        reject('FOREIGN KEY stock_items.product_id',
               'INSERT INTO stock_items(product_id,size_id,quantity_available) VALUES(9999,5,2)')
        reject('FOREIGN KEY orders.user_id',
               'INSERT INTO orders(order_date,user_id) VALUES(\'2026-10-14\',9999)')
        reject('ON DELETE RESTRICT roles → users', 'DELETE FROM roles WHERE role_id=1')
        reject('ON DELETE RESTRICT users → orders', 'DELETE FROM users WHERE user_id=1')
        reject('ON DELETE RESTRICT products → stock_items', 'DELETE FROM products WHERE product_id=1')
        reject('ON DELETE RESTRICT sizes → stock_items', 'DELETE FROM sizes WHERE size_id=1')
        reject('ON DELETE RESTRICT stock_items → order_items',
               'DELETE FROM stock_items WHERE stock_item_id=1')
        reject('UNIQUE stock_items(model, size)',
               'INSERT INTO stock_items(product_id,size_id,quantity_available) VALUES(1,1,2)')

        def cascade_validator(c, cur):
            before = c.execute('SELECT count(*) FROM order_items WHERE order_id=1').fetchone()[0]
            if before != 2: return False
            c.execute('DELETE FROM orders WHERE order_id=1')
            remaining = c.execute('SELECT count(*) FROM order_items WHERE order_id=1').fetchone()[0]
            return remaining == 0
        accept('ON DELETE CASCADE orders → order_items', 'SELECT 1', cascade_validator)
        accept('DEFAULT orders.order_date = date(now)', 'INSERT INTO orders(user_id) VALUES(1)',
               lambda c,cur: c.execute('SELECT order_date FROM orders WHERE order_id=?', (cur.lastrowid,)).fetchone()[0] ==
               c.execute("SELECT date('now')").fetchone()[0])
        accept('DEFAULT stock_items.quantity_available=0',
               'INSERT INTO stock_items(product_id,size_id) VALUES(5,5)',
               lambda c,cur: c.execute('SELECT quantity_available FROM stock_items WHERE stock_item_id=?',
                                       (cur.lastrowid,)).fetchone()[0] == 0)
        accept('REAL size_value=36.5', 'INSERT INTO sizes(size_value) VALUES(36.5)',
               lambda c,cur: abs(c.execute('SELECT size_value FROM sizes WHERE size_id=?',
                                             (cur.lastrowid,)).fetchone()[0]-36.5)<1e-8)
        accept('products.image_path допускает NULL',
               "INSERT INTO products(category,manufacturer,product_name,price) VALUES('Мужская','Тест','Без изображения',500)")
        if write_report:
            lines=['# УП.11 №4 — Результаты проверки ограничений','',
                   f'Тестовая SQLite-база: `{Path(db_path).name}`. Сначала созданы 7 таблиц и внесены учебные записи. '
                   'Каждый опыт выполнен внутри SAVEPOINT и полностью отменён; основная база не изменялась.','',
                   '| Ограничение | Ожидалось | Получено | Статус |','|---|---|---|---|']
            lines += [f'| {name} | {expect} | {actual.replace("|","\\|").replace("\n"," ")} | {"ПРОЙДЕНО" if ok else "ОШИБКА"} |'
                      for name,expect,actual,ok in results]
            lines += ['',f'**Итого: {sum(int(r[3]) for r in results)} из {len(results)} проверок пройдено.**','']
            (PROJECT_DIR/'docs'/'04_constraints_test.md').write_text('\n'.join(lines),encoding='utf-8')
        return results
    finally:
        conn.close()


def test_unique_login():
    return next(x for x in run_tests(write_report=False) if x[0]=='UNIQUE users.login')[3]

def test_not_null_last_name():
    return next(x for x in run_tests(write_report=False) if x[0]=='NOT NULL users.last_name')[3]

def test_check_price():
    return next(x for x in run_tests(write_report=False) if x[0]=='CHECK products.price = -100')[3]

def test_check_quantity():
    return next(x for x in run_tests(write_report=False) if x[0]=='CHECK stock_items.quantity_available < 0')[3]

def test_foreign_key():
    return next(x for x in run_tests(write_report=False) if x[0]=='FOREIGN KEY users.role_id')[3]

def test_on_delete_restrict():
    return next(x for x in run_tests(write_report=False) if x[0]=='ON DELETE RESTRICT roles → users')[3]

def test_on_delete_cascade():
    return next(x for x in run_tests(write_report=False) if x[0]=='ON DELETE CASCADE orders → order_items')[3]

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',type=Path,default=DEFAULT_TEST_DB)
    args=parser.parse_args()
    outcomes=run_tests(args.db)
    for name,_,message,passed in outcomes:
        print('PASS' if passed else 'FAIL', name, '-', message)
    print(f'Всего: {sum(int(r[3]) for r in outcomes)}/{len(outcomes)}')
    if not all(r[3] for r in outcomes):
        raise SystemExit(1)
