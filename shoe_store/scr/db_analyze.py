
from db_init import DATABASE_PATH, TABLES, get_connection


def analyze():
    with get_connection() as conn:
        counts = {table: conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                  for table in sorted(TABLES)}
        indexes = [tuple(r) for r in conn.execute(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY tbl_name, name")]
        views = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
        triggers = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")]
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        page_size = conn.execute('PRAGMA page_size').fetchone()[0]
        page_count = conn.execute('PRAGMA page_count').fetchone()[0]
        return {'counts': counts, 'indexes': indexes, 'views': views,
                'triggers': triggers, 'integrity': integrity,
                'bytes': page_size * page_count,
                'disk_bytes': DATABASE_PATH.stat().st_size if DATABASE_PATH.exists() else 0}


if __name__ == '__main__':
    d = analyze()
    print('Проверка целостности:', d['integrity'])
    print('Размер файла:', d['disk_bytes'], 'байт')
    print('Таблицы:', d['counts'])
    print('Индексы:', d['indexes'])
    print('Представления:', d['views'])
    print('Триггеры:', d['triggers'])
