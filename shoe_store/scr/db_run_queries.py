import sqlite3
import os


def get_connection():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
    db_path = os.path.join(db_dir, "shoe_store.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_query(conn, title, sql):
    print("=" * 70)
    print(title)
    print("=" * 70)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    max_width = 25

    widths = []
    for i, col in enumerate(columns):
        max_w = len(str(col))
        for row in rows:
            value_len = len(str(row[i]) if row[i] is not None else "None")
            if value_len > max_w:
                max_w = value_len
        if max_w > max_width:
            max_w = max_width
        widths.append(max_w)

    header = " | ".join(str(col)[:widths[i]].ljust(widths[i]) for i, col in enumerate(columns))
    print(header)

    for row in rows:
        line = " | ".join(
            (str(row[i]) if row[i] is not None else "None")[:widths[i]].ljust(widths[i])
            for i in range(len(columns))
        )
        print(line)

    print(f"Всего записей: {len(rows)}")
    print()


def main():
    conn = get_connection()

    run_query(conn, "ЗАПРОС 1. СПИСОК ВСЕХ ПОЛЬЗОВАТЕЛЕЙ С РОЛЯМИ", """
        SELECT u.user_id, u.last_name, u.first_name, u.middle_name, u.login, r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
    """)

    run_query(conn, "ЗАПРОС 2. СПИСОК ВСЕХ ТОВАРОВ", """
        SELECT product_id, product_name, category, manufacturer, price, image_path
        FROM products
    """)

    run_query(conn, "ЗАПРОС 3. СПИСОК ВСЕХ РАЗМЕРОВ", """
        SELECT size_id, size_value
        FROM sizes
        ORDER BY size_value
    """)

    run_query(conn, "ЗАПРОС 4. СПИСОК ВСЕХ ЗАКАЗОВ С ФИО КЛИЕНТОВ", """
        SELECT o.order_id, u.last_name, u.first_name, u.middle_name, o.order_date
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        ORDER BY o.order_date
    """)

    run_query(conn, "ЗАПРОС 5. СПИСОК ВСЕХ ТОВАРНЫХ ПОЗИЦИЙ С НАИМЕНОВАНИЕМ ТОВАРА И РАЗМЕРОМ", """
        SELECT si.stock_item_id, p.product_name, s.size_value, si.quantity
        FROM stock_items si
        JOIN products p ON si.product_id = p.product_id
        JOIN sizes s ON si.size_id = s.size_id
        ORDER BY p.product_name, s.size_value
    """)

    conn.close()


if __name__ == "__main__":
    main()