
from __future__ import annotations
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from db_init import DB_PATH, get_connection
from admin import PERMISSIONS, check_permission, ensure_admin_roles
from backup_restore import backup_simple, backup_safe, check_integrity, get_db_stats, clear_old_logs, demo_restore, restore
from db_apply_security import apply_security
from auth_secure import hash_password, register_user, check_password
from security_demo import vulnerable_login, secure_login, find_products, find_user_by_login, find_orders_by_user


def clone():
    source = get_connection()
    c = sqlite3.connect(':memory:')
    try:
        source.backup(c)
    finally:
        source.close()
    c.execute('PRAGMA foreign_keys=ON')
    return c


def run_tests(verbose=True):
    checks=[]
    def test(label, callback):
        try:
            callback()
            checks.append((label, True, 'OK'))
        except Exception as e:
            checks.append((label, False, f'{type(e).__name__}: {e}'))
        if verbose:
            print(('PASS ' if checks[-1][1] else 'FAIL ') + label + (' | '+checks[-1][2] if not checks[-1][1] else ''))
    def equal(a,b): assert a==b, f'{a!r} != {b!r}'
    def truth(a): assert a, 'Ожидалось True'

    with clone() as c:
        ensure_admin_roles(c)
        apply_security(c)
        role_ids = {name: c.execute('SELECT role_id FROM roles WHERE role_name=?',(name,)).fetchone()[0] for name in PERMISSIONS}
        test('Все три роли зарегистрированы',lambda: equal(len(role_ids),3))
        test('Повторное добавление ролей идемпотентно',lambda: (ensure_admin_roles(c), equal(c.execute("SELECT COUNT(*) FROM roles WHERE role_name IN ('reader','admin_db','developer')").fetchone()[0],3)))
        users={}
        for role in PERMISSIONS:
            users[role] = c.execute('INSERT INTO users(last_name,first_name,login,role_id) VALUES(?,?,?,?)',
                ('Тест','Роль', 'temp_'+role, role_ids[role])).lastrowid
        test('reader SELECT разрешен', lambda: truth(check_permission(c,users['reader'],'SELECT')))
        test('reader DELETE запрещен',lambda: equal(check_permission(c,users['reader'],'DELETE'),False))
        test('reader INSERT запрещен',lambda: equal(check_permission(c,users['reader'],'INSERT'),False))
        test('developer UPDATE разрешен',lambda: truth(check_permission(c,users['developer'],'UPDATE')))
        test('developer DROP запрещен',lambda: equal(check_permission(c,users['developer'],'DROP'),False))
        test('admin_db DELETE разрешен',lambda: truth(check_permission(c,users['admin_db'],'delete')))
        test('admin_db DROP разрешен',lambda: truth(check_permission(c,users['admin_db'],'DROP')))
        test('Несуществующий пользователь не имеет прав',lambda: equal(check_permission(c,999999,'SELECT'),False))
        test('Неизвестное действие запрещено',lambda: equal(check_permission(c,users['admin_db'],'SUPERUSER'),False))
        test('integrity_check ok',lambda: equal(check_integrity(c),['ok']))
        stats=get_db_stats(c)
        test('Размер равен числу страниц * размер',lambda: equal(stats['bytes'],stats['page_size']*stats['page_count']))
        test('Справочники присутствуют в статистике',lambda: truth(set(['users','roles','orders','audit_log','login_audit']) <= set(stats['tables'])))
        old=(datetime.now()-timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO audit_log(table_name,operation,record_id,changed_at) VALUES('users','UPDATE',123456,?)",(old,))
        c.commit()
        test('Очистка удаляет только старые логи',lambda: truth(clear_old_logs(c,30)>=1))
        test('Старый аудит отсутствует',lambda: equal(c.execute('SELECT COUNT(*) FROM audit_log WHERE changed_at=?',(old,)).fetchone()[0],0))
        test('Нельзя передать отрицательный срок хранения',lambda: assert_raises(ValueError,lambda:clear_old_logs(c,-1)))
        test('SHA256 совпадает с hashlib',lambda: equal(hash_password('admin123'), __import__('hashlib').sha256(b'admin123').hexdigest()))
        test('Пустой пароль не принимается',lambda: assert_raises(ValueError,lambda:hash_password('')))
        test('Регистрация с hash',lambda: truth(register_user(c,'new_demo','admin123')))
        stored=c.execute("SELECT password_hash FROM users WHERE login='new_demo'").fetchone()[0]
        test('В БД нет открытого пароля',lambda: truth(stored!='admin123' and len(stored)==64))
        test('Успешный вход',lambda: truth(check_password(c,'new_demo','admin123')))
        test('Неуспешный вход',lambda: equal(check_password(c,'new_demo','wrong'),False))
        test('Несуществующий логин',lambda: equal(check_password(c,'missing','password'),False))
        test('SQL injection не проходит авторизацию',lambda: equal(check_password(c,"' OR '1'='1",'admin123'),False))
        statuses=[r[0] for r in c.execute("SELECT status FROM login_audit ORDER BY id DESC LIMIT 4").fetchall()]
        test('login_audit записывает успех',lambda: truth('успех' in statuses))
        test('login_audit записывает отказ',lambda: truth('отказ' in statuses))
        test('Повторная регистрация запрещена',lambda: equal(register_user(c,'new_demo','other'),False))
        attack="' OR '1'='1"
        test('Уязвимый запрос показывает больше строк',lambda: truth(len(vulnerable_login(c,attack))>1))
        test('Параметризация защищает от injection',lambda:equal(len(secure_login(c,attack)),0))
        test('Поиск продукта с injection безопасен',lambda: equal(len(find_products(c,attack)),0))
        test('Поиск пользователя c injection безопасен',lambda: equal(find_user_by_login(c,attack),None))
        test('Поиск заказов параметризован',lambda: truth(len(find_orders_by_user(c,1))>=1))
        test('Повторная миграция не меняет схему',lambda: (apply_security(c),equal(c.execute("SELECT count(*) FROM pragma_table_info('users') WHERE name='password_hash'").fetchone()[0],1)))
        test('Все внешние ключи сохранились',lambda: equal(c.execute('PRAGMA foreign_key_check').fetchall(),[]))
        c.rollback()

    with tempfile.TemporaryDirectory(prefix='up11_admin_') as t:
        root=Path(t)
        src=root/'db.sqlite'
        with sqlite3.connect(src) as target, get_connection() as origin:
            origin.backup(target)
        simple=backup_simple(src, root)
        safe=backup_safe(src, root)
        test('shutil бэкап создан',lambda: truth(simple.is_file()))
        test('API-бэкап создан',lambda: truth(safe.is_file()))
        test('У двух бэкапов разные имена',lambda: truth(simple != safe))
        with sqlite3.connect(safe) as c:
            test('SQLite backup integrity ok',lambda: equal(c.execute('PRAGMA integrity_check').fetchone()[0],'ok'))
        with sqlite3.connect(src) as c:
            original=c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
            c.execute('PRAGMA foreign_keys=ON')
            c.execute('DELETE FROM order_items')
            c.execute('DELETE FROM orders')
            c.commit()
        restored=restore(safe,src)
        with sqlite3.connect(restored) as c:
            test('После восстановления заказы вернулись',lambda: equal(c.execute('SELECT COUNT(*) FROM orders').fetchone()[0],original))
        test('Симуляция сбоя и восстановления пройдена',lambda: equal(demo_restore(DB_PATH)['integrity'],'ok'))
    if verbose: print(f'ИТОГ: {sum(r[1] for r in checks)}/{len(checks)}')
    return checks


def assert_raises(kind,fn):
    try:
        fn()
    except kind:
        return True
    raise AssertionError('Ожидалась ошибка '+kind.__name__)


if __name__=='__main__':
    rows=run_tests()
    raise SystemExit(0 if all(row[1] for row in rows) else 1)
