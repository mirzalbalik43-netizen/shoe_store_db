
from __future__ import annotations
import re
from db_init import get_connection, TABLES

SQL_RESERVED = {
    'add', 'all', 'alter', 'and', 'as', 'asc', 'between', 'by', 'case', 'check',
    'column', 'constraint', 'create', 'cross', 'database', 'default', 'delete',
    'desc', 'distinct', 'drop', 'else', 'end', 'except', 'exists', 'false',
    'foreign', 'from', 'full', 'group', 'having', 'in', 'index', 'inner',
    'insert', 'into', 'is', 'join', 'key', 'left', 'limit', 'like', 'not', 'null',
    'on', 'or', 'order', 'outer', 'primary', 'references', 'right', 'select',
    'set', 'table', 'then', 'true', 'union', 'unique', 'update', 'using', 'values',
    'view', 'when', 'where', 'with',
}
ID_NAMES = {'role_id', 'user_id', 'product_id', 'size_id',
            'stock_item_id', 'order_id', 'order_item_id'}


def check_name(name: str):
    """Список нарушений: буква в начале, строчная латиница/snake_case, SQL-слова."""
    errors = []
    if not name or not ('a' <= name[0] <= 'z'):
        errors.append('имя должно начинаться с латинской буквы')
    if not re.fullmatch(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*', name or ''):
        errors.append('используйте строчную латиницу, цифры и snake_case')
    if name.lower() in SQL_RESERVED:
        errors.append('зарезервированное слово SQL')
    return errors


def get_tables(conn=None):
    own = conn is None
    db = conn if conn is not None else get_connection()
    try:
        return [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
    finally:
        if own:
            db.close()


def get_columns(table_name, conn=None):
    own = conn is None
    db = conn if conn is not None else get_connection()
    try:
        # Экранировать идентификатор из sqlite_master, не подставлять в SQL без кавычек.
        table = table_name.replace('"', '""')
        return [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
    finally:
        if own:
            db.close()


def check_database(conn=None):
    own = conn is None
    db = conn if conn is not None else get_connection()
    try:
        rows = []
        for table in get_tables(db):
            errs = check_name(table)
            if table not in TABLES and table not in ('audit_log', 'login_audit'):
                errs.append('не входит в перечень 7 основных таблиц и журналов аудита')
            if table not in ('audit_log','login_audit') and not table.endswith('s'):
                errs.append('имя таблицы должно быть во множественном числе')
            rows.append(('таблица', table, errs))
            for field in get_columns(table, db):
                errs = check_name(field)
                if field.endswith('_id') and field not in ID_NAMES | {'log_id', 'record_id'}:
                    errs.append('проверьте название идентификатора')
                if field in ('names', 'prices', 'quantities'):
                    errs.append('имя поля должно быть в единственном числе')
                rows.append(('поле', field, errs))
        missing = set(TABLES) - set(get_tables(db))
        for name in sorted(missing):
            rows.append(('таблица', name, ['отсутствует в базе']))
        return rows
    finally:
        if own:
            db.close()


if __name__ == '__main__':
    report = check_database()
    for kind, name, errors in report:
        print(f'{kind:7} {name:27} ' + ('OK' if not errors else '; '.join(errors)))
    count = sum(bool(errors) for _, _, errors in report)
    print(f'ИТОГО: {len(report)} имён, ошибок: {count}')
    raise SystemExit(1 if count else 0)
