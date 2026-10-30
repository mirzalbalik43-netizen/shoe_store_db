
from __future__ import annotations
import hashlib
import hmac
from db_apply_security import apply_security
from db_init import get_connection


def hash_password(password):
    if not isinstance(password, str) or not password:
        raise ValueError('Пароль должен быть непустой строкой')
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def register_user(conn, login, password, last_name='Учебный', first_name='Пользователь'):
    
    if not isinstance(login, str) or not 3 <= len(login) <= 20:
        return False
    try:
        password_hash = hash_password(password)
       
        role = conn.execute("SELECT role_id FROM roles WHERE role_name='reader'").fetchone()
        if role is None:
            return False
        conn.execute('''INSERT INTO users(last_name,first_name,login,role_id,password_hash)
                      VALUES(?,?,?,?,?)''', (last_name,first_name,login,role[0],password_hash))
        conn.commit()
        return True
    except (ValueError, TypeError, __import__('sqlite3').IntegrityError):
        conn.rollback()
        return False


def check_password(conn, login, password):
    
    valid = isinstance(login, str) and isinstance(password, str)
    if valid:
        found = conn.execute('SELECT password_hash FROM users WHERE login = ?', (login,)).fetchone()
        stored = found[0] if found else None
        calculated = hash_password(password) if password else ''
        result = bool(stored and calculated and hmac.compare_digest(stored, calculated))
    else:
        result = False
    conn.execute('INSERT INTO login_audit(login,status) VALUES(?,?)',
                 (str(login)[:200], 'успех' if result else 'отказ'))
    conn.commit()
    return result


def main():
   
    import sqlite3
    with get_connection() as source:
        c = sqlite3.connect(':memory:')
        try:
            source.backup(c)
            c.execute('PRAGMA foreign_keys=ON')
            apply_security(c)
            assert register_user(c,'auth_demo','admin123')
            assert check_password(c,'auth_demo','admin123')
            assert not check_password(c,'auth_demo','bad_password')
            print('Успешный и неуспешный вход зафиксированы (в RAM-копии).')
        finally:
            c.close()


if __name__ == '__main__':
    main()
