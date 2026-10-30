
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / 'db' / 'shoe_store.sqlite'
DEFAULT_REPORT = ROOT / 'docs' / '09_explain_analysis.md'
VIEWS = ('v_orders_full', 'v_products_with_stock', 'v_user_stats')
COLUMNS = {
    'v_orders_full': {'order_id','order_date','client_name','total_amount'},
    'v_products_with_stock': {'product_name','price','size_value','quantity_available'},
    'v_user_stats': {'client_name','login','order_count'},
}
REQUIRED_INDEXES = {
    'idx_products_category', 'idx_orders_order_date', 'idx_orders_user_id',
    'idx_stock_items_product_id', 'idx_stock_items_size_id',
    'idx_products_manufacturer_category',
}


def explain(conn: sqlite3.Connection, sql: str) -> list[str]:
    return [str(row[3]) for row in conn.execute('EXPLAIN QUERY PLAN ' + sql)]


def mcell(value):
    if value is None:
        return 'NULL'
    if isinstance(value, float):
        return str(round(value, 2))
    return str(value).replace('|', '\\|').replace('\n', ' ')


def sample_table(conn: sqlite3.Connection, sql: str, limit=3):
    cur = conn.execute(sql + ' LIMIT ' + str(int(limit)))
    cols = [entry[0] for entry in cur.description]
    rows = cur.fetchall()
    result = ['| ' + ' | '.join(cols) + ' |', '|' + '|'.join('---' for _ in cols) + '|']
    result += ['| ' + ' | '.join(mcell(value) for value in row) + ' |' for row in rows]
    if not rows:
        result += ['Нет строк.']
    return result


def run(db_path=DEFAULT_DB, report_path=DEFAULT_REPORT, verbose=True):
    db_path = Path(db_path)
    if not db_path.is_file():
        raise FileNotFoundError(str(db_path))
    original = sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True)
    copy = sqlite3.connect(':memory:')
    try:
        original.execute('PRAGMA foreign_keys=ON')
        if original.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise AssertionError('PRAGMA integrity_check не пройдена')
        if original.execute('PRAGMA foreign_key_check').fetchall():
            raise AssertionError('Нарушены внешние ключи')
        expected_tables={'roles','users','products','sizes','stock_items','orders','order_items'}
        tables={r[0] for r in original.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if tables != expected_tables:
            raise AssertionError(f'Не семь проектных таблиц: {tables}')
        known={r[0] for r in original.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        if set(VIEWS) != known:
            raise AssertionError(f'Ожидалось три представления, фактически: {sorted(known)}')
        for view,cols in COLUMNS.items():
            names={x[1] for x in original.execute('PRAGMA table_info("'+view+'")')}
            if not cols <= names:
                raise AssertionError(f'У представления {view} отсутствуют колонки {cols-names}')
        indices={r[0] for r in original.execute("SELECT name FROM sqlite_master WHERE type='index'")}
        if not REQUIRED_INDEXES <= indices:
            raise AssertionError('Не найдены индексы: '+str(REQUIRED_INDEXES-indices))

        category_sql="SELECT * FROM products WHERE category = 'Кроссовки'"
        manufacturer_sql="SELECT * FROM products WHERE manufacturer = 'Nike'"
        join_sql='SELECT * FROM orders o JOIN users u ON o.user_id = u.user_id'
        after_cat=explain(original,category_sql)
        main_manufacturer=explain(original,manufacturer_sql)
        main_join=explain(original,join_sql)
        main_composite=explain(original, "SELECT * FROM products WHERE manufacturer = 'NordStep' AND category = 'Мужская обувь'")
        # Временно убираем только индекс в копии; рабочая база остаётся неизменной.
        original.backup(copy)
        copy.execute('DROP INDEX IF EXISTS idx_products_category')
        before_cat=explain(copy,category_sql)
        copy.execute('CREATE INDEX idx_products_category ON products(category)')
        after_cat_copy=explain(copy,category_sql)
        if not any('SCAN products' in x for x in before_cat):
            raise AssertionError('План до индекса не показывает SCAN products')
        if not any('idx_products_category' in x for x in after_cat_copy):
            raise AssertionError('План после индекса не использует индекс категории')

        # Показываем, что существовавший с дня 3 индекс производителя меняет
        # ожидание из PDF: на исходной БД SELECT manufacturer использует индекс.
        copy.execute('DROP INDEX IF EXISTS idx_products_manufacturer')
        copy.execute('DROP INDEX IF EXISTS idx_products_manufacturer_category')
        unindexed_manufacturer=explain(copy,manufacturer_sql)

        # В SQLite обычное VIEW нельзя обновить без INSTEAD OF-триггера.
        copy.execute('CREATE VIEW v_simple AS SELECT product_id, price FROM products')
        p_before=copy.execute('SELECT price FROM products WHERE product_id=1').fetchone()[0]
        update_error=''
        try:
            copy.execute('UPDATE v_simple SET price = 100 WHERE product_id = 1')
        except sqlite3.OperationalError as e:
            update_error=str(e)
        else:
            raise AssertionError('Неожиданно удалось обновить обычное VIEW в SQLite')
        p_after=copy.execute('SELECT price FROM products WHERE product_id=1').fetchone()[0]
        if p_before != p_after:
            raise AssertionError('Содержимое таблицы products изменилось')

        counts={v:original.execute('SELECT COUNT(*) FROM "'+v+'"').fetchone()[0] for v in VIEWS}
        expected_counts={'v_orders_full':3,'v_products_with_stock':10,'v_user_stats':3}
        if counts != expected_counts:
            raise AssertionError(f'Неожиданное количество строк VIEW: {counts}')
        legacy=original.execute('SELECT total_quantity FROM v_products_with_stock WHERE product_id=1 LIMIT 1').fetchone()[0]
        if legacy != 26:
            raise AssertionError('Нарушена обратная совместимость с тестом дня 3')
        stats=original.execute('SELECT login,order_count FROM v_user_stats ORDER BY user_id').fetchall()
        if len(stats)!=3 or any(c!=1 for _,c in stats):
            raise AssertionError('Статистика по клиентам отличается от заказов')
        result={
            'counts':counts,'indexes':len([x for x in indices if x.startswith('idx_')]),
            'before':before_cat,'after':after_cat,'after_copy':after_cat_copy,
            'manufacturer':main_manufacturer,'manufacturer_without_index':unindexed_manufacturer,
            'join':main_join,'composite':main_composite,'update_error':update_error,
        }

        lines=['# УП.11 №8. Представления, индексы и EXPLAIN', '',
            '## 1. Условия проверки', '',
            '- Общая база: `db/shoe_store.sqlite` (сохранена из предыдущих занятий).',
            f'- SQLite: `{sqlite3.sqlite_version}`.',
            '- Семь пользовательских таблиц, внешние ключи и проверка целостности без ошибок.',
            f'- Представлений: **{len(known)}**, явных индексов: **{result["indexes"]}**.',
            '- Сравнение плана до создания индекса выполнялось **на копии в оперативной памяти**, не на оригинале.', '',
            '## 2. Созданные представления', '',
            '| Представление | Назначение | Строк |', '|---|---|---:|',
            f'| `v_orders_full` | Заказ, дата, ФИО клиента, сумма по `order_items` | {counts["v_orders_full"]} |',
            f'| `v_products_with_stock` | Модель, цена, размер, остаток по размеру | {counts["v_products_with_stock"]} |',
            f'| `v_user_stats` | ФИО, логин, количество заказов, включая ноль | {counts["v_user_stats"]} |', '',
            '**v_orders_full: первые три строки**', '',
            *sample_table(original,'SELECT order_id, order_date, client_name, total_amount FROM v_orders_full ORDER BY order_id'), '',
            '**v_products_with_stock: первые три строки**', '',
            *sample_table(original,'SELECT product_name, price, size_value, quantity_available FROM v_products_with_stock ORDER BY product_id, size_value'), '',
            '**v_user_stats: первые три строки**', '',
            *sample_table(original,'SELECT client_name, login, order_count FROM v_user_stats ORDER BY user_id'), '',
            'Для совместимости с прошлыми работами в `v_products_with_stock` также оставлен столбец `total_quantity`, суммарный остаток по всей модели. Теперь каждая строка показывает конкретный размер и его количество.', '',
            '## 3. Индексы', '',
            '| Индекс | Поля | Назначение |', '|---|---|---|',
            '| `idx_products_category` | products(category) | Быстрый поиск по категории |',
            '| `idx_orders_order_date` | orders(order_date) | Поиск и сортировка по дате заказа |',
            '| `idx_orders_user_id` | orders(user_id) | JOIN с users и заказы пользователя |',
            '| `idx_stock_items_product_id` | stock_items(product_id) | JOIN с products |',
            '| `idx_stock_items_size_id` | stock_items(size_id) | JOIN с sizes |',
            '| `idx_products_manufacturer_category` | products(manufacturer, category) | Уточняющий поиск одновременно по производителю и категории |', '',
            'Первые пять индексов были созданы в прежних практиках; команды в `views_indexes.sql` используют `IF NOT EXISTS` и не дублируют их. Новый индекс здесь составной. Индекс `idx_products_manufacturer` из старого дня также оставлен для совместимости, хотя он частично перекрывается составным по его первому полю.', '',
            '## 4. Фактические результаты EXPLAIN QUERY PLAN', '',
            '**Поиск категории без индекса (временная копия)**', '',
            '```sql', 'EXPLAIN QUERY PLAN', category_sql+';', '```',
            *['- `'+p+'`' for p in before_cat], '',
            '**Поиск категории с индексом (рабочая база)**', '',
            *['- `'+p+'`' for p in after_cat], '',
            '**Тот же поиск после восстановления индекса во временной копии**', '',
            *['- `'+p+'`' for p in after_cat_copy], '',
            'План меняется с `SCAN products` на `SEARCH products USING INDEX idx_products_category`. Это доказательство выбора индекса планировщиком, а не замер скорости выполнения.', '',
            '**Поиск производителя**', '',
            '```sql', 'EXPLAIN QUERY PLAN', manufacturer_sql+';', '```',
            'Реальная исходная база:', *['- `'+p+'`' for p in main_manufacturer],
            'При отсутствии обоих индексов на manufacturer (временная копия):',
            *['- `'+p+'`' for p in unindexed_manufacturer], '',
            'В отличие от ожидаемого в PDF полного сканирования, в исходном проекте индекс `idx_products_manufacturer` уже существовал. Поэтому реальный план использует индекс; временная копия демонстрирует противоположный сценарий без него.', '',
            '**JOIN заказов и пользователей**', '',
            '```sql','EXPLAIN QUERY PLAN',join_sql+';','```',
            *['- `'+p+'`' for p in main_join], '',
            'Полное сканирование `orders` здесь нормально, так как условие WHERE отсутствует и нужны все заказы. Для каждой строки `users` ищется по первичному ключу.', '',
            '**Составной индекс по двум фильтрам**', '',
            *['- `'+p+'`' for p in main_composite], '',
            'Выбор конкретного индекса зависит от статистики, объёма данных и запроса. На маленьком учебном наборе нельзя обещать заметное ускорение по времени.', '',
            '## 5. Попытка обновить VIEW', '',
            '```sql','CREATE VIEW v_simple AS SELECT product_id, price FROM products;',
            'UPDATE v_simple SET price = 100 WHERE product_id = 1;','```',
            f'- Получена ошибка SQLite: `{update_error}`.',
            f'- Цена в исходной таблице до попытки: **{mcell(p_before)}**, после: **{mcell(p_after)}**.',
            '- В SQLite обычные VIEW доступны только на чтение. Для записи необходим специальный триггер `INSTEAD OF`, в этом задании он не нужен.',
            '- Проверка выполнена на временной копии БД, поэтому основная база не изменена.', '',
            '## 6. Вывод', '',
            'Представления позволяют обращаться к готовым отчётным запросам как к таблицам и избегать повторного написания JOIN. Индексы ускоряют определённые фильтры, соединения и сортировки, однако увеличивают расходы на запись и место на диске. Команда `EXPLAIN QUERY PLAN` показывает выбранную стратегию: `SCAN` или `SEARCH ... USING INDEX`. Для каждого запроса индекс нужно подбирать по реальной нагрузке, а не создавать индексы для всех полей.', '' ]
        if report_path is not None:
            Path(report_path).parent.mkdir(parents=True,exist_ok=True)
            Path(report_path).write_text('\n'.join(lines),encoding='utf-8')
        if verbose:
            print('VIEW: '+', '.join(f'{k}={v}' for k,v in counts.items()))
            print('INDEX: найдено',result['indexes'],'явных, все обязательные присутствуют')
            print('BEFORE:',' | '.join(before_cat))
            print('AFTER:',' | '.join(after_cat))
            print('UPDATE VIEW: ожидаемая ошибка:',update_error)
            print('Все проверки УП.11 №8 выполнены.')
        return result
    finally:
        copy.close()
        original.close()


def main():
    parser=argparse.ArgumentParser(description='Анализ VIEW и INDEX без изменения рабочей базы')
    parser.add_argument('--db',type=Path,default=DEFAULT_DB)
    parser.add_argument('--report',type=Path,default=DEFAULT_REPORT)
    args=parser.parse_args()
    run(args.db,args.report)


if __name__ == '__main__':
    main()
