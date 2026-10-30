
import argparse
from pathlib import Path
from db_init import DB_PATH, PROJECT_DIR, TABLES, get_connection

EXPECTED_COLUMNS = {
    'roles': [('role_id','INTEGER'),('role_name','TEXT')],
    'sizes': [('size_id','INTEGER'),('size_value','REAL')],
    'users': [('user_id','INTEGER'),('last_name','TEXT'),('first_name','TEXT'),
              ('middle_name','TEXT'),('login','TEXT'),('role_id','INTEGER')],
    'products': [('product_id','INTEGER'),('category','TEXT'),('subcategory','TEXT'),
                 ('manufacturer','TEXT'),('product_name','TEXT'),('image_path','TEXT'),
                 ('composition','TEXT'),('description','TEXT'),('price','REAL')],
    'stock_items': [('stock_item_id','INTEGER'),('product_id','INTEGER'),
                    ('size_id','INTEGER'),('quantity_available','INTEGER')],
    'orders': [('order_id','INTEGER'),('order_date','TEXT'),('user_id','INTEGER')],
    'order_items': [('order_item_id','INTEGER'),('order_id','INTEGER'),
                    ('stock_item_id','INTEGER'),('quantity','INTEGER'),('price','REAL')],
}
EXPECTED_FKS = {
    'users': [('role_id','roles','role_id','RESTRICT')],
    'stock_items': [('product_id','products','product_id','RESTRICT'),
                    ('size_id','sizes','size_id','RESTRICT')],
    'orders': [('user_id','users','user_id','RESTRICT')],
    'order_items': [('order_id','orders','order_id','CASCADE'),
                    ('stock_item_id','stock_items','stock_item_id','RESTRICT')],
}
EXPECTED_INDEXES = {
    'idx_users_role_id', 'idx_orders_user_id', 'idx_stock_items_product_id',
    'idx_stock_items_size_id', 'idx_order_items_order_id',
    'idx_order_items_stock_item_id', 'idx_orders_order_date',
    'idx_products_category','idx_products_manufacturer','idx_products_price',
}


def _quoted(table):
    if table not in TABLES:
        raise ValueError('Неизвестная таблица: ' + str(table))
    return f'"{table}"'


def get_tables(conn):
    return [r['name'] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def get_columns(conn, table):
    return [dict(row) for row in conn.execute(f'PRAGMA table_info({_quoted(table)})')]


def get_foreign_keys(conn, table):
    return [dict(row) for row in conn.execute(f'PRAGMA foreign_key_list({_quoted(table)})')]


def get_indexes(conn, table):
    return [dict(row) for row in conn.execute(f'PRAGMA index_list({_quoted(table)})')]


def check_database(db_path=DB_PATH, write_report=True):
    conn = get_connection(db_path)
    checks = []
    lines = ['# УП.11 №4 — Проверка схемы SQLite', '',
             f'Файл: `{Path(db_path).name}`. Проверка проведена программно через `sqlite_master` и `PRAGMA`.', '']
    try:
        present = set(get_tables(conn))
        checks.append(('7 основных таблиц (плюс audit_log из №11)',
                       set(TABLES) <= present and present <= set(TABLES) | {'audit_log', 'login_audit'}))
        fk_status = conn.execute('PRAGMA foreign_keys').fetchone()[0]
        checks.append(('PRAGMA foreign_keys = ON', fk_status == 1))
        lines += ['| Таблица | Полей | PK | FK | Индексы (явные / служебные) | Результат |',
                  '|---|---:|---|---|---|---|']
        for table in TABLES:
            cols = get_columns(conn, table)
            fk = get_foreign_keys(conn, table)
            idx = get_indexes(conn, table)
            pairs = [(c['name'],c['type'].upper()) for c in cols]
            fields_ok = (pairs == EXPECTED_COLUMNS[table] or (table == 'users'
                         and pairs in [EXPECTED_COLUMNS[table] + [('updated_at', 'TEXT')], EXPECTED_COLUMNS[table] + [('updated_at', 'TEXT'), ('password_hash', 'TEXT')]]))
            pk = [c['name'] for c in cols if c['pk'] == 1]
            pk_ok = pk == [EXPECTED_COLUMNS[table][0][0]]
            actual_fk = {(f['from'],f['table'],f['to'],f['on_delete']) for f in fk}
            required_fk = set(EXPECTED_FKS.get(table, []))
            fk_ok = actual_fk == required_fk
            checks += [(f'{table}: поля и типы',fields_ok),
                       (f'{table}: первичный ключ',pk_ok),
                       (f'{table}: внешние ключи',fk_ok)]
            names = [f['name'] for f in idx]
            ok = fields_ok and pk_ok and fk_ok
            fk_s = ', '.join(f"{r['from']} → {r['table']} ({r['on_delete']})" for r in fk) or 'нет'
            lines.append(f'| {table} | {len(cols)} | {", ".join(pk)} | {fk_s} | {", ".join(names) or "—"} | {"ПРОЙДЕНО" if ok else "ОШИБКА"} |')
        actual_indexes = {r['name'] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}
        checks.append(('Все 10 базовых индексов дня 4', EXPECTED_INDEXES <= actual_indexes))
        fk_broken = conn.execute('PRAGMA foreign_key_check').fetchall()
        checks.append(('PRAGMA foreign_key_check без ошибок', len(fk_broken) == 0))
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        checks.append(('PRAGMA integrity_check = ok', integrity == 'ok'))
        view = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        checks.append(('v_orders_full существует', 'v_orders_full' in view))
        lines += ['', '## Сводка', '',
                  f'- Пользовательских таблиц: **{len(present)}**.',
                  f'- Явных индексов: **{len(actual_indexes)}**.',
                  f'- Внешних ключей: **{sum(len(get_foreign_keys(conn,t)) for t in TABLES)}**.',
                  f'- Проверка целостности: **{integrity}**.', '',
                  '| Проверка | Статус |', '|---|---|']
        lines.extend(f'| {name} | {"ПРОЙДЕНО" if ok else "ОШИБКА"} |' for name,ok in checks)
        passed = sum(ok for _,ok in checks)
        lines += ['', f'**Итого: {passed} из {len(checks)} проверок пройдено.**', '']
        if write_report:
            (PROJECT_DIR/'docs'/'04_schema_check.md').write_text('\n'.join(lines),encoding='utf-8')
        return checks
    finally:
        conn.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--db', type=Path, default=DB_PATH)
    args=parser.parse_args()
    result=check_database(args.db)
    for key, ok in result:
        print(('PASS' if ok else 'FAIL'), key)
    print(f'ИТОГО: {sum(x[1] for x in result)}/{len(result)}')
    if not all(x[1] for x in result):
        raise SystemExit(1)

if __name__=='__main__':
    main()
