
from __future__ import annotations
from db_init import get_connection

PERMISSIONS = {
    'admin_db': {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP'},
    'developer': {'SELECT', 'INSERT', 'UPDATE'},
    'reader': {'SELECT'},
}


def ensure_admin_roles(conn):
   
    for role in PERMISSIONS:
        conn.execute('INSERT OR IGNORE INTO roles(role_name) VALUES (?)', (role,))
    conn.commit()


def check_permission(conn, user_id, action):
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return False
    if not isinstance(action, str):
        return False
    row = conn.execute('''
        SELECT r.role_name FROM users AS u
        JOIN roles AS r ON r.role_id = u.role_id
        WHERE u.user_id = ?
    ''', (user_id,)).fetchone()
    return bool(row and action.strip().upper() in PERMISSIONS.get(row[0], set()))


def main():
    with get_connection() as c:
        ensure_admin_roles(c)
        print('Роли:', [r[0] for r in c.execute('SELECT role_name FROM roles ORDER BY role_id')])
        print('Проверка несуществующего пользователя на DELETE:', check_permission(c, -1, 'DELETE'))
        print('Важно: демонстрационные учетные записи создаются только в тестовой копии.')


if __name__ == '__main__':
    main()