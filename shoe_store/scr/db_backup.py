
from datetime import datetime
from pathlib import Path
import sqlite3
from db_init import DATABASE_PATH, get_connection


def backup(target: Path | None = None):
    dest = target or DATABASE_PATH.parent / 'backups' / f'shoe_store_{datetime.now():%Y%m%d_%H%M%S}.sqlite'
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.resolve() == DATABASE_PATH.resolve():
        raise ValueError('Резервная копия должна находиться в другом файле')
    with get_connection() as src, sqlite3.connect(str(dest)) as dst:
        src.backup(dst)
    return dest


if __name__ == '__main__':
    print('Резервная копия:', backup())
