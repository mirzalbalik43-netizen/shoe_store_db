
from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_DIR / "db" / "shoe_store.sqlite"
SQL_FILE = PROJECT_DIR / "queries" / "07_joins_and_aggregates.sql"
REPORT_FILE = PROJECT_DIR / "docs" / "07_query_results.md"

EXPLANATIONS = [
    "INNER JOIN связывает заказы с пользователями по user_id и выводит дату и ФИО.",
    "Три INNER JOIN связывают складскую позицию с моделью и размером.",
    "Пять таблиц объединяются, чтобы показать клиента и каждую купленную модель с ценой и суммой строки.",
    "LEFT JOIN оставляет всех пользователей; COUNT(o.order_id) даёт ноль при отсутствии заказов, а номер заказа остаётся NULL.",
    "COUNT(*) показывает число зарегистрированных пользователей.",
    "AVG вычисляет среднюю цену товара по каталогу, результат округлён до копеек.",
    "MIN и MAX находят крайние цены; отображаются названия товаров с этими ценами.",
    "SUM(quantity * price) вычисляет выручку по историческим ценам order_items.",
    "GROUP BY category подсчитывает число моделей в каждой категории.",
    "GROUP BY manufacturer определяет среднюю цену моделей у каждого производителя.",
    "LEFT JOIN и GROUP BY дают сумму покупок каждого клиента, включая тех, у кого нет заказов.",
    "SUM(quantity) по товару показывает проданные пары каждой модели, включая нулевые продажи.",
    "COUNT(stock_item_id) показывает число товарных позиций каждого размера.",
    "HAVING COUNT(*) > 3 оставляет лишь категории с более чем тремя моделями.",
    "HAVING COUNT(order_id) > 2 оставляет клиентов с более чем двумя заказами.",
    "HAVING SUM(quantity * price) > 100000 выбирает модели с выручкой свыше 100 тысяч рублей.",
    "SUM(quantity), ORDER BY и LIMIT 3 показывают три размера с наибольшим числом проданных пар.",
    "LEFT JOIN + WHERE o.order_id IS NULL находит клиентов без заказов.",
    "Внутренний запрос считает сумму каждого заказа, внешний AVG вычисляет средний чек.",
    "Группировка по производителю, сортировка по выручке и LIMIT 1 выбирают лидера.",
]


def load_queries(path: Path = SQL_FILE) -> list[tuple[int, str, str]]:
    """Парсер учебного SQL с нумерованными комментариями -- 01. и т.д."""
    results = []
    number = None
    title = None
    buffer = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped.startswith("--"):
            m = re.match(r"--\s*(\d{2})\.\s+(.+)$", stripped)
            if m:
                if buffer:
                    raise ValueError(f"Не закончен запрос перед номером {m.group(1)}")
                number, title = int(m.group(1)), m.group(2)
            continue
        if not stripped:
            continue
        buffer.append(raw)
        statement = "\n".join(buffer)
        if sqlite3.complete_statement(statement):
            sql = statement.strip().rstrip(";").strip()
            if number is None or not re.match(r"(?is)^SELECT\s", sql):
                raise ValueError("Для практики допускаются только нумерованные SELECT-запросы")
            results.append((number, title or f"Запрос {number}", sql))
            number = title = None
            buffer.clear()
    if buffer:
        raise ValueError("В конце SQL-файла остался незавершённый запрос")
    if [item[0] for item in results] != list(range(1, 21)):
        raise ValueError("Требуется ровно 20 запросов, пронумерованных от 01 до 20")
    return results


def cell(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, float):
        value = round(value, 2)
    return str(value).replace("|", "\\|").replace("\n", " ")


def execute(db_path: Path = DEFAULT_DB, limit: int = 5, output: Path | None = REPORT_FILE):
    if not db_path.is_file():
        raise FileNotFoundError(f"База данных не найдена: {db_path}")
    queries = load_queries()
    rows_out = []
    con = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys = ON")
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or fk_errors:
            raise RuntimeError(f"Ошибка целостности: integrity={integrity}, FK-ошибки={len(fk_errors)}")
        for number, title, sql in queries:
            cur = con.execute(sql)
            fields = [d[0] for d in cur.description]
            fetched = cur.fetchall()
            rows_out.append((number, title, sql, fields, fetched))
    finally:
        con.close()

    if output is not None:
        report = [
            "# УП.11 №6 — результаты JOIN и агрегатных запросов",
            "",
            "**Тема:** JOIN, COUNT, SUM, AVG, MIN, MAX, GROUP BY, HAVING.",
            "",
            "**Примечание к именованию:** в загруженном задании с заголовком «Тема 6» файлы явно указаны как `07_joins_and_aggregates.sql` и `07_query_results.md`. Использованы именно эти имена.",
            "",
            f"**Источник:** база `db/{db_path.name}` проекта `shoe_store`; выполнены все 20 SQL-запросов из `queries/07_joins_and_aggregates.sql`.",
            "",
            "**База не изменялась:** подключение в режиме только чтения (`mode=ro`). Результаты ниже получены при реальном выполнении запросов.",
            "",
            "**Пустые выборки:** при имеющихся учебных данных некоторые условия HAVING и поиск пользователей без заказов дают 0 строк. Это корректный результат, а не ошибка SQL; исходные записи специально не изменялись ради красивого вывода.",
            "",
        ]
        for number, title, sql, fields, fetched in rows_out:
            report += [f"## Запрос {number}. {title}", "", EXPLANATIONS[number-1], "", "**SQL:**", "", "```sql", sql + ";", "```", "", f"**Фактический результат:** {len(fetched)} строк.", ""]
            if fetched:
                report += ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
                for row in fetched[:limit]:
                    report.append("| " + " | ".join(cell(v) for v in row) + " |")
                if len(fetched) > limit:
                    report.append(f"\n*Показаны первые {limit} из {len(fetched)} строк.*")
            else:
                report.append("Нет строк, удовлетворяющих условию на текущих тестовых данных.")
            report.append("")
        report += ["## Вывод", "", f"Успешно выполнены все {len(rows_out)} запросов, данные предыдущих практик не изменены. Проверены INNER JOIN, LEFT JOIN, агрегаты, GROUP BY, HAVING и аналитические запросы.", ""]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(report), encoding="utf-8")
    return rows_out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit должен быть больше нуля")
    for number, _, _, _, records in execute(args.db, args.limit, None if args.no_report else REPORT_FILE):
        print(f"Запрос {number:02d}: {len(records)} строк")
    if not args.no_report:
        print(f"Отчёт: {REPORT_FILE}")


if __name__ == "__main__":
    main()
