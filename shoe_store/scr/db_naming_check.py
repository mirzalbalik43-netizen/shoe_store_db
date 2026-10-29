import sqlite3
import os
import re


RESERVED_WORDS = {
    'select', 'from', 'where', 'insert', 'update', 'delete', 'table',
    'index', 'order', 'group', 'by', 'having', 'join', 'inner', 'outer',
    'left', 'right', 'on', 'as', 'and', 'or', 'not', 'null', 'primary',
    'key', 'foreign', 'references', 'unique', 'check', 'default', 'create',
    'drop', 'alter', 'column', 'values', 'into', 'set', 'distinct'
}


def get_connection():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
    db_path = os.path.join(db_dir, "shoe_store.sqlite")
    conn = sqlite3.connect(db_path)
    return conn


def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]


def get_columns(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def check_name(name):
    errors = []
    if not name[0].isalpha():
        errors.append("не начинается с буквы")
    if not re.match(r'^[a-z0-9_]+$', name):
        errors.append("содержит недопустимые символы")
    if name != name.lower():
        errors.append("не в нижнем регистре")
    if name in RESERVED_WORDS:
        errors.append("зарезервированное слово SQL")
    return errors


def check_database():
    conn = get_connection()
    tables = get_tables(conn)

    print("=" * 70)
    print("ПРОВЕРКА СХЕМЫ ИМЕНОВАНИЯ")
    print("=" * 70)
    print()

    total_errors = 0

    for table in tables:
        errors = check_name(table)
        if errors:
            print(f"Таблица {table}: ОШИБКИ - {', '.join(errors)}")
            total_errors += len(errors)
        else:
            print(f"Таблица {table}: OK")

        columns = get_columns(conn, table)
        for column in columns:
            col_errors = check_name(column)
            if col_errors:
                print(f"  Поле {column}: ОШИБКИ - {', '.join(col_errors)}")
                total_errors += len(col_errors)

    print()
    print("=" * 70)
    if total_errors == 0:
        print("РЕЗУЛЬТАТ: Все имена соответствуют правилам")
    else:
        print(f"РЕЗУЛЬТАТ: Найдено ошибок - {total_errors}")
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    check_database()