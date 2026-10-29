import sqlite3
import os

# Шаг 17: Константа пути к базе
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "shoe_store.sqlite")


def get_connection():
    # Создаем папку db, если её нет
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    # Шаг 18: Строки возвращаются как словари
    conn.row_factory = sqlite3.Row
    # Шаг 21: Включаем проверку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def drop_all_tables(cursor):
    # Шаг 19: Удаление таблиц в обратном порядке (от зависимых к главным)
    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS stock_items")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS sizes")
    cursor.execute("DROP TABLE IF EXISTS roles")


def create_tables(cursor):
    # 1. roles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE
        )
    """)

    # 2. sizes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sizes (
            size_id INTEGER PRIMARY KEY AUTOINCREMENT,
            size_value REAL NOT NULL UNIQUE CHECK (size_value > 20 AND size_value < 50)
        )
    """)

    # 3. products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL CHECK (length(product_name) > 0),
            category TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            price NUMERIC NOT NULL CHECK (price > 0 AND price < 1000000),
            image_path TEXT
        )
    """)

    # 4. users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            login TEXT NOT NULL UNIQUE CHECK (length(login) >= 3 AND length(login) <= 20),
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
        )
    """)

    # 5. stock_items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_items (
            stock_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            size_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
            FOREIGN KEY (size_id) REFERENCES sizes(size_id) ON DELETE RESTRICT
        )
    """)

    # 6. orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date TEXT NOT NULL DEFAULT CURRENT_DATE CHECK (date(order_date) IS NOT NULL),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
        )
    """)

    # 7. order_items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            stock_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            price NUMERIC NOT NULL CHECK (price > 0),
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (stock_item_id) REFERENCES stock_items(stock_item_id) ON DELETE RESTRICT
        )
    """)

    # Шаги 65-71: Создание индексов
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_manufacturer ON products(manufacturer)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_items_product_id ON stock_items(product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_items_size_id ON stock_items(size_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_stock_item_id ON order_items(stock_item_id)")


def main():
    conn = get_connection()
    cursor = conn.cursor()
    
    drop_all_tables(cursor)
    create_tables(cursor)
    
    conn.commit()
    conn.close()
    print("База данных успешно пересоздана со всеми таблицами и индексами")


if __name__ == "__main__":
    main()