
import sqlite3
from pathlib import Path
from db_init import DB_PATH, PROJECT_DIR, TABLES, get_connection
from db_naming_check import check_database
from db_structure_check import check_database as structure_check
from db_test_final import run_tests as integration_tests
from db_test_constraints import run_tests as constraints_tests
from db_validate import validate

EXPECTED_COUNTS={'roles':6,'sizes':5,'users':3,'products':5,'stock_items':10,'orders':3,'order_items':6}
SQL_FILES=['02_check_queries.sql','03_data_validation.sql','04_check_queries.sql','examples.sql','07_joins_and_aggregates.sql','08_subqueries_and_windows.sql']


def iter_statements(text):
    lines=[]
    for line in text.splitlines():
        if line.lstrip().startswith('--'):
            continue
        lines.append(line)
        candidate='\n'.join(lines).strip()
        if candidate and sqlite3.complete_statement(candidate):
            stmt=candidate.rstrip().rstrip(';').strip()
            if stmt: yield stmt
            lines=[]
    if '\n'.join(lines).strip():
        raise ValueError('SQL без завершающей точки с запятой')


def main():
    tests=[]
    def log(label,condition,details=''):
        tests.append((label,bool(condition),str(details)))
        print(('OK  ' if condition else 'FAIL')+' '+label+((' | '+str(details)) if details else ''))

    with get_connection() as conn:
        tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        log('Семь основных таблиц и два журнала аудита',tables==set(TABLES)|{'audit_log','login_audit'},str(sorted(tables)))
        counts={t:conn.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES}
        log('Тестовые данные и шесть ролей после №12',counts==EXPECTED_COUNTS,str(counts))
        log('FK включены',conn.execute('PRAGMA foreign_keys').fetchone()[0]==1)
        log('Нет ошибок foreign_key_check',not conn.execute('PRAGMA foreign_key_check').fetchall())
        log('Общая целостность SQLite',conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
        current_views={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        log('Три VIEW из практики №8',
            current_views=={'v_orders_full','v_products_with_stock','v_user_stats'},
            str(sorted(current_views)))
        extra_idx={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}
        log('Составной индекс практики №8',
            'idx_products_manufacturer_category' in extra_idx,
            f'{len(extra_idx)} пользовательских индексов')
        log('Новые представления и старые итоги совместимы',
            conn.execute('SELECT count(*) FROM v_products_with_stock').fetchone()[0]==10
            and conn.execute('SELECT total_quantity FROM v_products_with_stock WHERE product_id=1 LIMIT 1').fetchone()[0]==26
            and conn.execute('SELECT count(*) FROM v_user_stats').fetchone()[0]==3)

        for filename in SQL_FILES:
            path=PROJECT_DIR/'queries'/filename
            queries=list(iter_statements(path.read_text('utf-8')))
            problems=[]
            for i,statement in enumerate(queries,1):
                try:
                    rows=conn.execute(statement).fetchall()
                    if filename=='03_data_validation.sql' and rows:
                        problems.append(f'запрос {i}: обнаружено {len(rows)} нарушений')
                except Exception as exc:
                    problems.append(f'запрос {i}: {exc}')
            log('SQL '+filename, bool(queries) and not problems,
                f'{len(queries)} запросов'+ ('; '+'; '.join(problems) if problems else ''))
    # Дополнительно проверяем нумерацию новых аналитических заданий.
    from db_run_windows import load_queries as load_window_queries
    try:
        win = load_window_queries()
        log('Ровно 11 SQL-запросов практики №7', len(win) == 11)
    except Exception as error:
        log('Ровно 11 SQL-запросов практики №7', False, str(error))
    log('Аудит имён (день 3)',not any(err for _,_,err in check_database()))
    strukt=structure_check(write_report=False)
    log('Проверка структуры (день 4)',bool(strukt) and all(row[1] for row in strukt),f'{sum(x[1] for x in strukt)}/{len(strukt)}')
    final=integration_tests()
    log('Комплексные проверки (день 3)',all(row[1]=='PASS' for row in final), f'{sum(x[1]=="PASS" for x in final)}/{len(final)}')
    tests04=constraints_tests(write_report=False)
    log('Ограничения (день 4)',all(row[3] for row in tests04),f'{sum(row[3] for row in tests04)}/{len(tests04)}')
    anomalies=validate()
    log('Аномалий нет (день 3)',all(value==0 if key!='PRAGMA integrity_check' else value=='ok' for key,value in anomalies.items()))
    schema=(PROJECT_DIR/'db'/'schema.sql').read_text('utf-8')
    generated=(PROJECT_DIR/'db'/'schema_generated.sql').read_text('utf-8')
    for label,ddl in [('schema.sql',schema),('schema_generated.sql',generated)]:
        try:
            con=sqlite3.connect(':memory:')
            con.executescript(ddl)
            found={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            indices=con.execute("SELECT count(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
            log('DDL разворачивается с нуля: '+label,found==set(TABLES) and indices>=10,f'{len(found)} таблиц, {indices} индексов')
        except Exception as exc:
            log('DDL разворачивается с нуля: '+label,False,str(exc))
        finally:
            con.close()
    expected=[*('docs/'+p for p in ['01_entities.md','01_normalization.md','01_erd_description.md','02_data_types.md','02_constraints.md','03_constraints_final.md','03_indexes.md','04_schema_report.md','04_day_report.md','ERD_module_1.pdf','ERD_module_1.drawio','07_query_results.md','07_day_report.md','08_query_results.md','08_day_report.md','08_self_check_questions.md','09_explain_analysis.md','09_day_report.md','09_self_check_questions.md']), 'db/shoe_store.sqlite', 'db/views_indexes.sql', 'src/db_run_views_indexes.py']
    log('Документы №1–4, №6–8 и диаграмма на месте',all((PROJECT_DIR/p).is_file() for p in expected))
    log('Нет previous_days или вложенных архивов',not any(p.name=='previous_days' or p.suffix=='.zip' for p in PROJECT_DIR.rglob('*')))
    # Проверки новой практики №9 выполняются без изменения основной базы.
    from app_functions import execute_queries as run_udf_queries
    from test_functions import run_tests as run_function_tests
    with get_connection() as conn:
        try:
            udf_queries = run_udf_queries(conn)
            log('Пять SQL-запросов №9', len(udf_queries) == 5 and len(udf_queries[0][2]) > 0
                and len(udf_queries[4][2]) == 3, str([len(q[2]) for q in udf_queries]))
        except Exception as err:
            log('Пять SQL-запросов №9', False, str(err))
    udf_tests = run_function_tests(verbose=False)
    log('Unit-тесты и транзакции №9', all(r[1] for r in udf_tests),
        f'{sum(r[1] for r in udf_tests)}/{len(udf_tests)}')
    log('Четыре основных файла №9 на месте', all((PROJECT_DIR / rel).is_file() for rel in [
        'src/app_functions.py', 'src/test_functions.py',
        'queries/10_advanced_queries.sql', 'docs/10_functions_report.md']))
    # Практика №10 из PDF: PostgreSQL примеры и SQLite-процедуры.
    from procedures_functions import get_demo_query_results as day10_queries
    from test_procedures_functions import run_tests as day10_tests
    new_files = [
        'src/procedures_functions.py', 'src/test_procedures_functions.py',
        'db/procedures_functions.sql', 'queries/11_procedures_demo.sql',
        'docs/10_report.md'
    ]
    log('Файлы практики №10 на месте',
        all((PROJECT_DIR / f).is_file() for f in new_files),
        f'{sum((PROJECT_DIR / f).is_file() for f in new_files)}/{len(new_files)}')
    with get_connection() as conn:
        try:
            output = day10_queries(conn)
            log('SQL UDF практики №10',
                len(output) == 3 and all(rows for _, _, rows in output),
                f'{len(output)} SQL-запроса; строки: {[len(x[2]) for x in output]}')
        except Exception as error:
            log('SQL UDF практики №10', False, str(error))
    passed_new = day10_tests(verbose=False)
    log('Процедуры и транзакции №10 (RAM-копии)',
        bool(passed_new) and all(row[1] for row in passed_new),
        f'{sum(row[1] for row in passed_new)}/{len(passed_new)}')
    # День 11: проверка миграции, аудит и недвойное списание на RAM-копии.
    from test_triggers import run_tests as run_trigger_tests
    trigger_files = ['db/triggers.sql', 'src/db_apply_triggers.py',
                     'src/test_triggers.py', 'docs/11_triggers_description.md']
    log('Файлы практики №11 на месте',
        all((PROJECT_DIR / f).is_file() for f in trigger_files))
    with get_connection() as c:
        trigger_names = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        log('Не меньше 10 триггеров, аудит и updated_at',
            len(trigger_names) >= 10 and 'audit_log' in tables
            and 'updated_at' in [r[1] for r in c.execute('PRAGMA table_info(users)')])
    trigger_checks=run_trigger_tests(verbose=False)
    log('Автотесты триггеров №11 (RAM-копии)',
        bool(trigger_checks) and all(r[1] for r in trigger_checks),
        f'{sum(r[1] for r in trigger_checks)}/{len(trigger_checks)}')
    # Дни 12+13: права, резервирование, SQL-инъекции, пароли и аудит.
    from test_admin_security import run_tests as run_admin_security_tests
    admin_files = ['src/admin.py', 'src/backup_restore.py', 'src/maintenance.py',
                   'src/db_apply_security.py', 'docs/12_admin_report.md']
    security_files = ['src/security_demo.py', 'src/auth_secure.py',
                      'src/test_admin_security.py', 'db/security.sql',
                      'docs/13_security_policy.md']
    log('Материалы №12 на месте', all((PROJECT_DIR/f).is_file() for f in admin_files))
    log('Материалы №13 на месте', all((PROJECT_DIR/f).is_file() for f in security_files))
    with get_connection() as conn:
        role_names = {r[0] for r in conn.execute('SELECT role_name FROM roles')}
        col_names = {r[1] for r in conn.execute('PRAGMA table_info(users)')}
        log('Роли и новое поле password_hash',
            {'admin_db','developer','reader'} <= role_names and 'password_hash' in col_names)
        log('Журнал login_audit и контроль целостности',
            'login_audit' in tables and not conn.execute('PRAGMA foreign_key_check').fetchall())
    backups = list((PROJECT_DIR/'db'/'backups').glob('backup_*.sqlite'))
    log('Два программных бэкапа №12', len(backups) >= 2)
    security_checks = run_admin_security_tests(verbose=False)
    log('Автотесты администрирования и безопасности №12–13',
        bool(security_checks) and all(r[1] for r in security_checks),
        f'{sum(r[1] for r in security_checks)}/{len(security_checks)}')
    passed=sum(ok for _,ok,_ in tests)
    lines=['# Сквозная проверка практик №1–4, №6–13','','Проверка выполнена на единой схеме SQLite с VIEW, INDEX, функциями №9–10, триггерами и аудитом №11, управлением доступом №12 и безопасностью №13.','',
           '| Проверка | Результат | Примечания |','|---|---|---|']
    for name,ok,notes in tests:
        lines.append(f'| {name} | {"ПРОЙДЕНО" if ok else "ОШИБКА"} | {notes.replace("|","/")} |')
    lines+=['',f'**Итог: {passed} из {len(tests)} проверок пройдено.**','']
    (PROJECT_DIR/'docs'/'04_cross_day_validation.md').write_text('\n'.join(lines),'utf-8')
    print(f'ИТОГ: {passed}/{len(tests)}')
    return 0 if passed==len(tests) else 1


if __name__=='__main__':
    raise SystemExit(main())
