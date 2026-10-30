
from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sqlite3
from db_init import DB_PATH

BACKUP_DIR = DB_PATH.parent / 'backups'


def _target(prefix, output_dir=None):
    out = Path(output_dir) if output_dir is not None else BACKUP_DIR
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
    return out / f'{prefix}_{stamp}.sqlite'


def _validate_source(db_path):
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f'База не найдена: {path}')
    return path


def backup_simple(db_path=DB_PATH, output_dir=None):
    """Файловая копия: только когда база не используется для записи."""
    source = _validate_source(db_path)
    dest = _target('backup_simple', output_dir)
    shutil.copy2(source, dest)
    return dest


def backup_safe(db_path=DB_PATH, output_dir=None):
    """Гарантированный консистентный snapshot через SQLite backup API."""
    source = _validate_source(db_path)
    dest = _target('backup_safe', output_dir)
    try:
        with sqlite3.connect(str(source)) as src, sqlite3.connect(str(dest)) as dst:
            src.backup(dst)
        with sqlite3.connect(str(dest)) as check:
            if check.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Ошибка целостности резервной копии')
        return dest
    except Exception:
        dest.unlink(missing_ok=True)
        raise


def check_integrity(conn):
    return [r[0] for r in conn.execute('PRAGMA integrity_check').fetchall()]


def get_db_stats(conn):
    page_size = conn.execute('PRAGMA page_size').fetchone()[0]
    page_count = conn.execute('PRAGMA page_count').fetchone()[0]
    tables = [r[0] for r in conn.execute('''
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name
    ''')]
    return {'page_size': page_size, 'page_count': page_count,
            'bytes': page_size * page_count, 'tables': tables}


def clear_old_logs(conn, days=30):
    if type(days) is not int or days < 0:
        raise ValueError('days должно быть целым неотрицательным числом')
    threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.execute('DELETE FROM audit_log WHERE changed_at < ?', (threshold,))
    conn.commit()
    return cur.rowcount


def restore(backup_path, db_path=DB_PATH):
    """Атомарное восстановление из файла после закрытия иных соединений.

    Для настоящей аварии предварительно остановить все процессы, открывающие
    файл основной БД. Не использовать при активных WAL-соединениях.
    """
    source = _validate_source(backup_path)
    dest = Path(db_path)
    if source.resolve() == dest.resolve():
        raise ValueError('Источник и назначение совпадают')
    # Не допускаем замены поврежденным бэкапом.
    with sqlite3.connect(f'file:{source.resolve()}?mode=ro', uri=True) as c:
        if c.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Резервная копия повреждена')
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + '.restore_tmp')
    try:
        shutil.copy2(source, tmp)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest


def demo_restore(db_path=DB_PATH):
    """Симуляция аварии только во временном каталоге, основная БД нетронута."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix='shoe_store_restore_') as t:
        work = Path(t) / 'simulation.sqlite'
        backup = backup_safe(db_path, t)
        shutil.copy2(backup, work)
        with sqlite3.connect(work) as c:
            before = c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
            if before == 0:
                raise AssertionError('Для демонстрации нужны существующие заказы')
            c.execute('PRAGMA foreign_keys=ON')
            c.execute('DELETE FROM order_items')
            c.execute('DELETE FROM orders')
            c.commit()
            broken = c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
        restore(backup, work)
        with sqlite3.connect(work) as c:
            after = c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
            integrity = c.execute('PRAGMA integrity_check').fetchone()[0]
        assert broken == 0 and after == before and integrity == 'ok'
        return {'before': before, 'damaged': broken, 'restored': after, 'integrity': integrity}


if __name__ == '__main__':
    from db_init import get_connection
    with get_connection() as c:
        print('Целостность:', check_integrity(c))
        print('Статистика:', get_db_stats(c))
    print('Резервная копия:', backup_safe())
    print('Восстановление на копии:', demo_restore())
