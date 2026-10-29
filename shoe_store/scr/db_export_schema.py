import sqlite3
import os

def export_schema():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "shoe_store.sqlite")
    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "schema.sql")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем SQL код всех таблиц и индексов
    cursor.execute("SELECT sql FROM sqlite_master WHERE type IN ('table', 'index') AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL")
    rows = cursor.fetchall()
    
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("PRAGMA foreign_keys = ON;\n\n")
        for row in rows:
            f.write(row[0] + ";\n\n")
            
    conn.close()
    print(f"Структура экспортирована в {sql_path}")

if __name__ == "__main__":
    export_schema()