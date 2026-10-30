
from __future__ import annotations
import argparse
from pathlib import Path
import sqlite3
from db_init import DB_PATH, get_connection

SQL_PATH = Path(__file__).resolve().parent.parent / 'db' / 'triggers.sql'


def apply_triggers(conn: sqlite3.Connection):
    cols = {row[1] for row in conn.execute('PRAGMA table_info(users)')}
    if 'updated_at' not in cols:
        conn.execute('ALTER TABLE users ADD COLUMN updated_at TEXT')
        conn.commit()
    conn.executescript(SQL_PATH.read_text(encoding='utf-8'))
    conn.commit()
    return [row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")]


def demo_log(conn: sqlite3.Connection):
    """5 честных аудиторских событий, без изменения исходных значений.

    Не повторяем демо, если в логе уже есть пять событий.
    """
    if conn.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0] >= 5:
        return 0
    try:
        conn.execute('BEGIN IMMEDIATE')
        price1 = conn.execute('SELECT price FROM products WHERE product_id=1').fetchone()[0]
        price2 = conn.execute('SELECT price FROM products WHERE product_id=2').fetchone()[0]
        conn.execute('UPDATE products SET price=? WHERE product_id=1', (round(price1+1,2),))
        conn.execute('UPDATE products SET price=? WHERE product_id=1', (price1,))
        conn.execute('UPDATE products SET price=? WHERE product_id=2', (round(price2+1,2),))
        conn.execute('UPDATE products SET price=? WHERE product_id=2', (price2,))
        # Удалить тестовый заказ можно только после добавления позиции в него.
        user_id = conn.execute('SELECT user_id FROM users ORDER BY user_id LIMIT 1').fetchone()[0]
        stock = conn.execute('SELECT stock_item_id FROM stock_items WHERE quantity_available>=1 ORDER BY stock_item_id LIMIT 1').fetchone()[0]
        order = conn.execute('INSERT INTO orders (user_id) VALUES (?)', (user_id,)).lastrowid
        conn.execute('INSERT INTO order_items (order_id,stock_item_id,quantity,price) '
                     'SELECT ?, s.stock_item_id, 1, p.price FROM stock_items s '
                     'JOIN products p ON p.product_id=s.product_id WHERE s.stock_item_id=?',
                     (order,stock))
        conn.execute('DELETE FROM orders WHERE order_id=?', (order,))
        conn.commit()
        return 5
    except Exception:
        conn.rollback()
        raise


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--db', type=Path, default=DB_PATH)
    parser.add_argument('--demo-log', action='store_true')
    args=parser.parse_args()
    with get_connection(args.db) as conn:
        triggers = apply_triggers(conn)
        if args.demo_log:
            demo_log(conn)
        errors = conn.execute('PRAGMA foreign_key_check').fetchall()
        assert not errors, errors
        print(f'Схема обновлена: {len(triggers)} триггеров, журнал: '
              f'{conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]} записей')


if __name__ == '__main__':
    main()
