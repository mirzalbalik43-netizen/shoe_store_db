
from pathlib import Path
from admin import ensure_admin_roles
from db_init import get_connection

SQL = Path(__file__).resolve().parent.parent / 'db' / 'security.sql'


def apply_security(conn):
    ensure_admin_roles(conn)
    columns = {r[1] for r in conn.execute('PRAGMA table_info(users)')}
    if 'password_hash' not in columns:
        conn.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
    conn.executescript(SQL.read_text('utf-8'))
    conn.commit()


if __name__ == '__main__':
    with get_connection() as c:
        apply_security(c)
        print('Роли и безопасность настроены. Колонки users:',
              [r[1] for r in c.execute('PRAGMA table_info(users)')])
