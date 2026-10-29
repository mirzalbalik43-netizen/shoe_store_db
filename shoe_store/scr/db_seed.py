import sqlite3
import os


def get_connection():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
    db_path = os.path.join(db_dir, "shoe_store.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM stock_items")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM sizes")
    cursor.execute("DELETE FROM roles")

    cursor.execute("INSERT INTO roles (role_name) VALUES ('администратор')")
    admin_role_id = cursor.lastrowid
    cursor.execute("INSERT INTO roles (role_name) VALUES ('менеджер')")
    manager_role_id = cursor.lastrowid
    cursor.execute("INSERT INTO roles (role_name) VALUES ('авторизованный пользователь')")
    user_role_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO users (last_name, first_name, middle_name, login, role_id) VALUES (?, ?, ?, ?, ?)",
        ('Иванов', 'Иван', 'Иванович', 'admin', admin_role_id)
    )
    admin_user_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO users (last_name, first_name, middle_name, login, role_id) VALUES (?, ?, ?, ?, ?)",
        ('Петров', 'Петр', 'Петрович', 'manager', manager_role_id)
    )
    manager_user_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO users (last_name, first_name, middle_name, login, role_id) VALUES (?, ?, ?, ?, ?)",
        ('Сидоров', 'Сидор', None, 'user', user_role_id)
    )
    user_user_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO products (product_name, category, manufacturer, price, image_path) VALUES (?, ?, ?, ?, ?)",
        ('Кроссовки Nike Air', 'Спортивная', 'Nike', 8990.00, 'images/nike_air.jpg')
    )
    p1 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO products (product_name, category, manufacturer, price, image_path) VALUES (?, ?, ?, ?, ?)",
        ('Туфли классические', 'Классическая', 'Ecco', 12490.00, 'images/ecco_classic.jpg')
    )
    p2 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO products (product_name, category, manufacturer, price, image_path) VALUES (?, ?, ?, ?, ?)",
        ('Ботинки зимние', 'Зимняя', 'Timberland', 15990.00, 'images/timberland_winter.jpg')
    )
    p3 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO products (product_name, category, manufacturer, price, image_path) VALUES (?, ?, ?, ?, ?)",
        ('Сандалии летние', 'Летняя', 'Adidas', 4590.00, 'images/adidas_summer.jpg')
    )
    p4 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO products (product_name, category, manufacturer, price, image_path) VALUES (?, ?, ?, ?, ?)",
        ('Кеды повседневные', 'Повседневная', 'Converse', 6790.00, 'images/converse_casual.jpg')
    )
    p5 = cursor.lastrowid

    cursor.execute("INSERT INTO sizes (size_value) VALUES (36.0)")
    s1 = cursor.lastrowid
    cursor.execute("INSERT INTO sizes (size_value) VALUES (37.0)")
    s2 = cursor.lastrowid
    cursor.execute("INSERT INTO sizes (size_value) VALUES (38.0)")
    s3 = cursor.lastrowid
    cursor.execute("INSERT INTO sizes (size_value) VALUES (39.0)")
    s4 = cursor.lastrowid
    cursor.execute("INSERT INTO sizes (size_value) VALUES (40.0)")
    s5 = cursor.lastrowid

    stock_data = [
        (p1, s1, 10),
        (p1, s2, 5),
        (p1, s3, 0),
        (p2, s2, 7),
        (p2, s3, 3),
        (p3, s4, 12),
        (p3, s5, 8),
        (p4, s1, 20),
        (p4, s2, 15),
        (p5, s3, 6),
    ]
    stock_ids = []
    for product_id, size_id, quantity in stock_data:
        cursor.execute(
            "INSERT INTO stock_items (product_id, size_id, quantity) VALUES (?, ?, ?)",
            (product_id, size_id, quantity)
        )
        stock_ids.append(cursor.lastrowid)

    cursor.execute(
        "INSERT INTO orders (user_id, order_date) VALUES (?, ?)",
        (user_user_id, '2025-01-15')
    )
    o1 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO orders (user_id, order_date) VALUES (?, ?)",
        (user_user_id, '2025-02-20')
    )
    o2 = cursor.lastrowid
    cursor.execute(
        "INSERT INTO orders (user_id, order_date) VALUES (?, ?)",
        (manager_user_id, '2025-03-10')
    )
    o3 = cursor.lastrowid

    cursor.execute(
        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, ?, ?)",
        (o1, stock_ids[0], 1, 8990.00)
    )
    cursor.execute(
        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, ?, ?)",
        (o1, stock_ids[1], 2, 12490.00)
    )
    cursor.execute(
        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, ?, ?)",
        (o2, stock_ids[4], 1, 15990.00)
    )
    cursor.execute(
        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, ?, ?)",
        (o2, stock_ids[8], 3, 4590.00)
    )
    cursor.execute(
        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, ?, ?)",
        (o3, stock_ids[9], 1, 6790.00)
    )
    cursor.execute(
        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, ?, ?)",
        (o3, stock_ids[3], 2, 12490.00)
    )

    conn.commit()
    conn.close()
    print("Тестовые данные вставлены")


if __name__ == "__main__":
    seed_db()