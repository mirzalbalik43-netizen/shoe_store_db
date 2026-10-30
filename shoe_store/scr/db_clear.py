
import argparse
from pathlib import Path
from db_init import DB_PATH, get_connection, TABLES

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',type=Path,default=DB_PATH)
    parser.add_argument('--yes',action='store_true')
    args=parser.parse_args()
    if not args.yes:
        parser.error('Удаление данных требует --yes')
    with get_connection(args.db) as conn:
        for table in reversed(TABLES):
            conn.execute(f'DELETE FROM {table}')
        conn.execute('DELETE FROM sqlite_sequence')
    print('Данные очищены. Таблицы и индексы сохранены.')
