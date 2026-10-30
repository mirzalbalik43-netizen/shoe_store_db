
import argparse
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / 'db' / 'shoe_store.sqlite'
DATABASE_PATH = DB_PATH
SCHEMA_PATH = PROJECT_DIR / 'db' / 'schema.sql'
VIEWS_INDEXES_PATH = PROJECT_DIR / 'db' / 'views_indexes.sql'
TABLES = ['roles', 'sizes', 'users', 'products', 'stock_items', 'orders', 'order_items']


def get_connection(db_path=None):
    """Подключение с обязательной ссылочной целостностью и sqlite3.Row."""
    path = Path(db_path) if db_path is not None else DB_PATH
    if str(path) != ':memory:':
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    if conn.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
        conn.close()
        raise RuntimeError('PRAGMA foreign_keys не активирован')
    return conn


def drop_all_tables(db_path=None):
    """Удаление схемы в обратном порядке связей. ВНИМАНИЕ: теряются все данные!"""
    with get_connection(db_path) as conn:
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            conn.execute('DROP TRIGGER IF EXISTS "' + row[0].replace('"','""') + '"')
        conn.execute('DROP TABLE IF EXISTS audit_log')
        conn.execute('DROP VIEW IF EXISTS v_user_stats')
        conn.execute('DROP VIEW IF EXISTS v_orders_full')
        conn.execute('DROP VIEW IF EXISTS v_products_with_stock')
        for table in reversed(TABLES):
            conn.execute(f'DROP TABLE IF EXISTS {table}')


def create_tables(db_path=None, connection=None):
    """Создание структур из schema.sql и фиксация изменений."""
    owned = connection is None
    conn = connection or get_connection(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding='utf-8'))
        # Повторный запуск обновляет все VIEW, но не трогает строки таблиц.
        conn.executescript(VIEWS_INDEXES_PATH.read_text(encoding='utf-8'))
        conn.commit()
        return conn
    finally:
        if owned:
            conn.close()


def init_db(db_path=None, connection=None):
    """Создаёт недостающие структуры без удаления данных.

    Для скриптов дней 1–3 поддержан вызов init_db(conn), а для дня 4 —
    init_db(path). Это одна и та же схема db/schema.sql.
    """
    if isinstance(db_path, sqlite3.Connection):
        connection, db_path = db_path, None
    create_tables(db_path, connection=connection)



def main(argv=None):
    parser = argparse.ArgumentParser(description='УП.11 №4 — пересоздание SQLite базы.')
    parser.add_argument('--db', type=Path, default=DB_PATH, help='Путь к файлу базы')
    parser.add_argument('--keep-data', action='store_true', help='Не удалять существующие данные')
    args = parser.parse_args(argv)
    if not args.keep_data:
        drop_all_tables(args.db)
    create_tables(args.db)
    with get_connection(args.db) as conn:
        present = [r['name'] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        if set(present) != set(TABLES):
            raise RuntimeError(f'Неправильный набор таблиц: {present}')
        if conn.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Обнаружены повреждённые внешние ключи')
    print(f'База создана: {args.db} | {len(present)} таблиц | внешние ключи включены')


if __name__ == '__main__':
    main()
