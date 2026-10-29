import sqlite3
import sys

def setup_database(conn):
    with open('db/triggers.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    conn.executescript(sql_script)
    conn.commit()

def test_trigger_flow():
    conn = sqlite3.connect("db/shoe_store.sqlite")
    setup_database(conn)
    cursor = conn.cursor()

    print("--- 1. Проверка списания остатков (AFTER INSERT) ---")
    cursor.execute("SELECT stock_item_id, quantity_available FROM stock_items LIMIT 1")
    stock_item = cursor.fetchone()
    if not stock_item:
        print("В базе нет складских позиций для теста.")
        conn.close()
        return
        
    stock_item_id, initial_qty = stock_item

    cursor.execute("INSERT INTO orders (user_id, order_date) VALUES (1, datetime('now'))")
    order_id = cursor.lastrowid
    
    cursor.execute(
        "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, 2, 1500.0)", 
        (order_id, stock_item_id)
    )
    conn.commit()

    cursor.execute("SELECT quantity_available FROM stock_items WHERE stock_item_id = ?", (stock_item_id,))
    new_qty = cursor.fetchone()[0]
    print(f"Остаток до: {initial_qty}, Остаток после: {new_qty}")
    assert new_qty == initial_qty - 2, "Триггер списания остатков не сработал!"

    print("\n--- 2. Проверка защиты от удаления пользователя (BEFORE DELETE) ---")
    cursor.execute("INSERT INTO users (first_name, last_name) VALUES ('Тест', 'Удаление')")
    test_user_id = cursor.lastrowid
    cursor.execute("INSERT INTO orders (user_id, order_date) VALUES (?, datetime('now'))", (test_user_id,))
    conn.commit()
    
    try:
        cursor.execute("DELETE FROM users WHERE user_id = ?", (test_user_id,))
        conn.commit()
        print("ОШИБКА: Пользователь был удален, хотя у него был заказ!")
        sys.exit(1)
    except sqlite3.IntegrityError as e:
        print(f"Защита сработала корректно: {e}")

    print("\n--- 3. Проверка аудита изменения цен (AFTER UPDATE) ---")
    cursor.execute("UPDATE products SET price = price + 100 WHERE product_id = 1")
    conn.commit()
    
    cursor.execute("SELECT table_name, operation, old_value, new_value FROM audit_log ORDER BY log_id DESC LIMIT 1")
    log_entry = cursor.fetchone()
    print(f"Запись в логе: Таблица={log_entry[0]}, Операция={log_entry[1]}, Было={log_entry[2]}, Стало={log_entry[3]}")
    assert log_entry[0] == 'products' and log_entry[1] == 'UPDATE', "Триггер аудита цен не сработал!"

    print("\n--- 4. Проверка аудита удаления заказов (AFTER DELETE) ---")
    cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    conn.commit()
    
    cursor.execute("SELECT table_name, operation FROM audit_log ORDER BY log_id DESC LIMIT 1")
    log_entry = cursor.fetchone()
    print(f"Запись в логе: Таблица={log_entry[0]}, Операция={log_entry[1]}")
    assert log_entry[0] == 'orders' and log_entry[1] == 'DELETE', "Триггер аудита удаления не сработал!"

    print("\n--- 5. Проверка триггера BEFORE INSERT (отрицательное количество) ---")
    try:
        cursor.execute("INSERT INTO stock_items (product_id, size_id, quantity_available) VALUES (1, 1, -5)")
        conn.commit()
        print("ОШИБКА: В базу вставлено отрицательное количество!")
        sys.exit(1)
    except sqlite3.IntegrityError as e:
        print(f"Защита от отрицательного количества сработала: {e}")

    print("\n✅ Все тесты триггеров пройдены успешно.")
    conn.close()

if __name__ == "__main__":
    test_trigger_flow()