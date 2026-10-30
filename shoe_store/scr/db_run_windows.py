
from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT / 'db' / 'shoe_store.sqlite'
SQL_PATH = PROJECT / 'queries' / '08_subqueries_and_windows.sql'
REPORT_PATH = PROJECT / 'docs' / '08_query_results.md'

EXPLANATIONS = ['Подзапрос WHERE вычисляет AVG(price) по всем товарам; внешний SELECT выбирает позиции дороже средней.', 'Табличный подзапрос суммирует строки каждого заказа, вложенный MAX находит максимальную сумму; LIMIT 1 выбирает одного клиента при равенстве.', 'Оператор IN сравнивает идентификаторы пользователей со списком user_id из orders.', 'Коррелированный NOT EXISTS ищет пользователей, для которых отсутствует связанный заказ.', 'NOT IN проверяет product_id относительно товаров, реально встречающихся в order_items через stock_items; товары без продаж остаются.', 'LEFT JOIN включает всех пользователей, SUM считает сумму покупок по сохранённой цене, RANK() OVER ранжирует по убыванию суммы.', 'ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY order_date, order_id) присваивает порядковый номер заказа внутри каждого пользователя.', 'ROW_NUMBER с PARTITION BY category нумерует модели каждой категории по убыванию цены.', 'В подзапросе FROM считается ROW_NUMBER отдельно по категории; внешний WHERE оставляет первую, самую дорогую модель.', 'Табличный подзапрос считает сумму по каждому заказу; SUM(...) OVER с явными границами ROWS даёт накопительную выручку в хронологическом порядке.', 'LAG возвращает дату предшествующего заказа того же пользователя, julianday() вычисляет интервал; при первом заказе значение NULL.']


def load_queries(path: Path = SQL_PATH):
    """Извлекает ровно 11 нумерованных SQL-запросов, не используя exec/eval."""
    items = []
    current_number, current_title = None, None
    buffer = []
    for line in path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'^--\s*(\d{2})\.\s+(.+)$', line.strip())
        if m:
            if buffer or current_number is not None:
                raise ValueError('Ошибка разделения SQL перед запросом ' + m.group(1))
            current_number, current_title = int(m.group(1)), m.group(2)
            continue
        if line.lstrip().startswith('--') or not line.strip():
            continue
        buffer.append(line)
        candidate = '\n'.join(buffer)
        if sqlite3.complete_statement(candidate):
            statement = candidate.strip().rstrip(';').strip()
            if current_number is None or not re.match(r'(?is)^SELECT\b', statement):
                raise ValueError('Разрешены только SELECT с нумерованным комментарием')
            items.append((current_number, current_title, statement))
            buffer = []
            current_number, current_title = None, None
    if buffer or current_number is not None:
        raise ValueError('Незавершённый запрос')
    if [n for n, _, _ in items] != list(range(1, 12)):
        raise ValueError('Должно быть ровно 11 запросов №01–№11')
    return items


def markdown_cell(value):
    if value is None:
        return 'NULL'
    if isinstance(value, float):
        value = round(value, 2)
    return str(value).replace('|', '\\|').replace('\n', ' ')


def execute(db_path: Path = DB_PATH, report_path: Path | None = REPORT_PATH, limit: int = 5):
    if limit < 1:
        raise ValueError('limit должен быть положительным')
    if not db_path.is_file():
        raise FileNotFoundError('База не найдена: ' + str(db_path))
    con = sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    results = []
    try:
        con.execute('PRAGMA foreign_keys=ON')
        integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        fk_issues = con.execute('PRAGMA foreign_key_check').fetchall()
        if integrity != 'ok' or fk_issues:
            raise RuntimeError('Нарушена целостность БД: ' + str(integrity))
        if sqlite3.sqlite_version_info < (3, 25, 0):
            raise RuntimeError('Требуется SQLite 3.25+ для оконных функций')
        for number, title, sql in load_queries():
            cur = con.execute(sql)
            fields = [meta[0] for meta in cur.description]
            rows = cur.fetchall()
            results.append((number, title, sql, fields, rows))
    finally:
        con.close()
    if report_path is not None:
        report = [
            '# УП.11 №7 — результаты подзапросов и оконных функций', '',
            '**Тема:** подзапросы SELECT/WHERE/FROM, IN, NOT EXISTS, ROW_NUMBER, RANK, LAG и накопительные суммы.', '',
            '**Имена файлов:** в задании с заголовком «Тема 7» указаны файлы `08_subqueries_and_windows.sql` и `08_query_results.md`; они сохранены дословно.', '',
            '**Источник данных:** единая `db/shoe_store.sqlite` из работ №1–4 и №6. Реально выполненные запросы, подключение только для чтения.', '',
            '**Интерпретация:** пустой результат означает, что учебные данные не удовлетворили фильтру. Для первого заказа клиента `LAG` возвращает `NULL`.', '',
        ]
        for number, title, sql, fields, rows in results:
            report += [f'## Запрос {number}. {title}', '', EXPLANATIONS[number-1], '',
                       '**SQL:**', '', '```sql', sql+';', '```', '',
                       f'**Фактический результат:** {len(rows)} строк.', '']
            if rows:
                report += ['| ' + ' | '.join(fields) + ' |',
                           '| ' + ' | '.join('---' for _ in fields) + ' |']
                for r in rows[:limit]:
                    report.append('| ' + ' | '.join(markdown_cell(v) for v in r) + ' |')
                if len(rows) > limit:
                    report.extend(['', f'*Показано {limit} из {len(rows)} строк.*'])
            else:
                report.append('Нет строк при текущих тестовых данных.')
            report.append('')
        report.extend(['## Итог', '',
                       f'Выполнено {len(results)} из 11 SELECT-запросов без изменения исходной базы. Проверены подзапросы, IN/NOT EXISTS и оконные функции.', ''])
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text('\n'.join(report), encoding='utf-8')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DB_PATH)
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--no-report', action='store_true')
    args = parser.parse_args()
    for n, _, _, _, rows in execute(args.db, None if args.no_report else REPORT_PATH, args.limit):
        print(f'Запрос {n:02}: {len(rows)} строк')
    if not args.no_report:
        print('Отчёт:', REPORT_PATH)


if __name__ == '__main__':
    main()
