
from __future__ import annotations
import sqlite3
from db_init import get_connection


def vulnerable_login(conn, login):
    # Пример из задания; НЕ применять к рабочей базе с реальными пользователями.
    return conn.execute(f"SELECT user_id, login FROM users WHERE login = '{login}'").fetchall()


def secure_login(conn, login):
    return conn.execute('SELECT user_id, login FROM users WHERE login = ?', (login,)).fetchall()


def find_products(conn, term):
    return conn.execute('''SELECT product_id, product_name, price FROM products
                           WHERE product_name LIKE ? ORDER BY product_id''',
                        (f'%{term}%',)).fetchall()


def find_user_by_login(conn, login):
    return conn.execute('SELECT user_id, login FROM users WHERE login = ?', (login,)).fetchone()


def find_orders_by_user(conn, user_id):
    return conn.execute('SELECT order_id, order_date FROM orders WHERE user_id = ? ORDER BY order_id',
                        (user_id,)).fetchall()


def run_demo():
    attack = "' OR '1'='1"
    with get_connection() as src:
        c = sqlite3.connect(':memory:')
        try:
            src.backup(c)
            c.execute('PRAGMA foreign_keys=ON')
            normal = vulnerable_login(c, 'admin')
            attacked = vulnerable_login(c, attack)
            safe = secure_login(c, attack)
            product_attack = find_products(c, attack)
            result = {'normal_rows':len(normal),'unsafe_injection_rows':len(attacked),
                      'safe_injection_rows':len(safe), 'safe_product_search_rows':len(product_attack)}
            assert normal and len(attacked) > 1 and not safe and not product_attack
            print('Демо SQL-инъекции (ТОЛЬКО в памяти):', result)
            return result
        finally:
            c.close()


if __name__ == '__main__':
    run_demo()
