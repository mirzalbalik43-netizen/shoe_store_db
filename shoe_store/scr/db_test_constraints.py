import sqlite3
import os


def get_connection():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
    db_path = os.path.join(db_dir, "shoe_store.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def cleanup_test_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM order_items WHERE order_item_id IN (SELECT order_item_id FROM order_items WHERE order_id IN (SELECT order_id FROM orders WHERE user_id IN (SELECT user_id FROM users WHERE login LIKE 'test_%')))")
    cursor.execute("DELETE FROM orders WHERE user_id IN (SELECT user_id FROM users WHERE login LIKE 'test_%')")
    cursor.execute("DELETE FROM users WHERE login LIKE 'test_%'")
    cursor.execute("DELETE FROM stock_items WHERE product_id IN (SELECT product_id FROM products WHERE product_name LIKE 'Test%')")
    cursor.execute("DELETE FROM products WHERE product_name LIKE 'Test%'")
    cursor.execute("DELETE FROM sizes WHERE size_value IN (42.0, 43.0)")
    cursor.execute("DELETE FROM roles WHERE role_name IN ('test_role', 'test_role2', 'restrict_role', 'cascade_role')")
    conn.commit()
    conn.close()


def test_unique_login():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (role_name) VALUES ('test_role')")
        role_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO users (last_name, first_name, login, role_id) VALUES ('Ivanov', 'Ivan', 'test_login', ?)",
            (role_id,)
        )
        try:
            cursor.execute(
                "INSERT INTO users (last_name, first_name, login, role_id) VALUES ('Petrov', 'Petr', 'test_login', ?)",
                (role_id,)
            )
            conn.rollback()
            return ("UNIQUE на login", "ошибка", "ошибка не возникла", "не пройден")
        except sqlite3.IntegrityError:
            conn.rollback()
            return ("UNIQUE на login", "ошибка", "ошибка", "пройден")
    finally:
        conn.close()


def test_not_null_last_name():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (role_name) VALUES ('test_role2')")
        role_id = cursor.lastrowid
        try:
            cursor.execute(
                "INSERT INTO users (last_name, first_name, login, role_id) VALUES (NULL, 'Ivan', 'test_login2', ?)",
                (role_id,)
            )
            conn.rollback()
            return ("NOT NULL на last_name", "ошибка", "ошибка не возникла", "не пройден")
        except sqlite3.IntegrityError:
            conn.rollback()
            return ("NOT NULL на last_name", "ошибка", "ошибка", "пройден")
    finally:
        conn.close()


def test_check_price():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute(
                "INSERT INTO products (product_name, category, manufacturer, price) VALUES ('Test', 'Cat', 'Man', -100)"
            )
            conn.rollback()
            return ("CHECK на price", "ошибка", "ошибка не возникла", "не пройден")
        except sqlite3.IntegrityError:
            conn.rollback()
            return ("CHECK на price", "ошибка", "ошибка", "пройден")
    finally:
        conn.close()


def test_check_quantity():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (product_name, category, manufacturer, price) VALUES ('Test2', 'Cat', 'Man', 1000)")
        product_id = cursor.lastrowid
        cursor.execute("INSERT INTO sizes (size_value) VALUES (42.0)")
        size_id = cursor.lastrowid
        try:
            cursor.execute(
                "INSERT INTO stock_items (product_id, size_id, quantity) VALUES (?, ?, -5)",
                (product_id, size_id)
            )
            conn.rollback()
            return ("CHECK на quantity", "ошибка", "ошибка не возникла", "не пройден")
        except sqlite3.IntegrityError:
            conn.rollback()
            return ("CHECK на quantity", "ошибка", "ошибка", "пройден")
    finally:
        conn.close()


def test_foreign_key():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute(
                "INSERT INTO users (last_name, first_name, login, role_id) VALUES ('Test', 'Test', 'test_fk', 99999)"
            )
            conn.rollback()
            return ("FOREIGN KEY на role_id", "ошибка", "ошибка не возникла", "не пройден")
        except sqlite3.IntegrityError:
            conn.rollback()
            return ("FOREIGN KEY на role_id", "ошибка", "ошибка", "пройден")
    finally:
        conn.close()


def test_on_delete_restrict():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (role_name) VALUES ('restrict_role')")
        role_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO users (last_name, first_name, login, role_id) VALUES ('Test', 'Test', 'test_restrict', ?)",
            (role_id,)
        )
        conn.commit()
        try:
            cursor.execute("DELETE FROM roles WHERE role_id = ?", (role_id,))
            conn.rollback()
            return ("ON DELETE RESTRICT", "ошибка", "ошибка не возникла", "не пройден")
        except sqlite3.IntegrityError:
            conn.rollback()
            return ("ON DELETE RESTRICT", "ошибка", "ошибка", "пройден")
    finally:
        conn.close()


def test_on_delete_cascade():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (role_name) VALUES ('cascade_role')")
        role_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO users (last_name, first_name, login, role_id) VALUES ('Test', 'Test', 'test_cascade', ?)",
            (role_id,)
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO orders (user_id, order_date) VALUES (?, '2025-01-01')",
            (user_id,)
        )
        order_id = cursor.lastrowid
        cursor.execute("INSERT INTO products (product_name, category, manufacturer, price) VALUES ('Test3', 'Cat', 'Man', 500)")
        product_id = cursor.lastrowid
        cursor.execute("INSERT INTO sizes (size_value) VALUES (43.0)")
        size_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO stock_items (product_id, size_id, quantity) VALUES (?, ?, 10)",
            (product_id, size_id)
        )
        stock_item_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, 1, 500)",
            (order_id, stock_item_id)
        )
        conn.commit()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM order_items WHERE order_id = ?", (order_id,))
        count = cursor.fetchone()[0]
        if count == 0:
            return ("ON DELETE CASCADE", "каскадное удаление", "каскадное удаление", "пройден")
        else:
            return ("ON DELETE CASCADE", "каскадное удаление", f"осталось {count} записей", "не пройден")
    finally:
        conn.close()


def main():
    cleanup_test_data()

    results = []
    results.append(test_unique_login())
    results.append(test_not_null_last_name())
    results.append(test_check_price())
    results.append(test_check_quantity())
    results.append(test_foreign_key())
    results.append(test_on_delete_restrict())
    results.append(test_on_delete_cascade())

    cleanup_test_data()

    print("| Ограничение | Ожидаемый результат | Фактический результат | Статус |")
    print("|------------|-------------------|---------------------|--------|")
    for r in results:
        print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")


if __name__ == "__main__":
    main()