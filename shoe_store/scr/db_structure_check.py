import sqlite3
import os

def get_connection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "shoe_store.sqlite")
    return sqlite3.connect(db_path)

def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]

def get_columns(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]

def get_foreign_keys(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    return [row[2] for row in cursor.fetchall()] # Возвращает имена таблиц, на которые ссылаемся

def get_indexes(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list({table})")
    return [row[1] for row in cursor.fetchall()]

def check_database():
    conn = get_connection()
    tables = get_tables(conn)
    
    print("=" * 60)
    print("ПРОВЕРКА СТРУКТУРЫ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    expected_tables = ['roles', 'sizes', 'products', 'users', 'stock_items', 'orders', 'order_items']
    
    if len(tables) != 7:
        print(f"ВНИМАНИЕ: Найдено {len(tables)} таблиц вместо 7!")
    else:
        print("Все 7 таблиц созданы.")
    
    for table in expected_tables:
        if table not in tables:
            print(f"ОШИБКА: Таблица {table} не найдена!")
            continue
            
        cols = get_columns(conn, table)
        fks = get_foreign_keys(conn, table)
        idxs = get_indexes(conn, table)
        
        print(f"\nТаблица: {table}")
        print(f"  Поля ({len(cols)}): {', '.join(cols)}")
        if fks:
            print(f"  Внешние ключи: {', '.join(fks)}")
        if idxs:
            print(f"  Индексы: {', '.join(idxs)}")
            
    conn.close()
    print("\n" + "=" * 60)
    print("Проверка завершена.")
    print("=" * 60)

if __name__ == "__main__":
    check_database()