1. Созданные представления (VIEW)

Для инкапсуляции сложной логики и упрощения работы с базой данных были созданы три виртуальные таблицы:

v_orders_full — полная информация о заказах. Объединяет таблицы orders, users и order_items. Выводит номер и дату заказа, ФИО клиента и итоговую сумму с группировкой.
v_products_with_stock — товары с остатками. Объединяет таблицы products, stock_items и sizes. Выводит название модели, цену, размер и доступное количество.
v_user_stats — статистика по клиентам. Объединяет таблицы users и orders. Выводит ФИО, логин и количество сделанных заказов.


2. Созданные индексы (INDEX)

Для оптимизации производительности поиска и соединений созданы следующие индексы:

Имя индекса	Таблица	Поля	Тип
idx_products_category	products	category	Обычный
idx_orders_date	orders	order_date	Обычный
idx_orders_user_id	orders	user_id	Внешний ключ
idx_stock_product_id	stock_items	product_id	Внешний ключ
idx_stock_size_id	stock_items	size_id	Внешний ключ
idx_products_manufacturer_category	products	category, manufacturer	Составной

Составной индекс создан по полям category и manufacturer. Он будет эффективно ускорять запросы, где фильтрация идет сначала по категории, а затем по производителю.

3. Анализ планов выполнения (EXPLAIN QUERY PLAN)
Поиск по индексированному полю (Категория)

Запрос:

sql
Копировать
EXPLAIN QUERY PLAN
SELECT * FROM products WHERE category = 'Кроссовки';

Поиск по неиндексированному полю (Производитель)

Запрос:

sql
Копировать
EXPLAIN QUERY PLAN
SELECT * FROM products WHERE manufacturer = 'Nike';

Сложный запрос с JOIN

Запрос:

sql
Копировать
EXPLAIN QUERY PLAN
SELECT * FROM orders o JOIN users u ON o.user_id = u.user_id;

Общий вывод об индексах
Ускоряет работу: Точечный поиск по WHERE, сортировка ORDER BY, соединение таблиц JOIN по внешним ключам.

Задание 4

Попытка обновления простого VIEW:

sql
Копировать
CREATE VIEW v_simple AS SELECT product_id, price FROM products;
UPDATE v_simple SET price = 100 WHERE product_id = 1;

Результаты работы с представлениями и индексами День 8

Запросы выполнены через src/db_run_queries.py. Все SQL-команды из файла db/views_indexes.sql (3 представления и 5 индексов) успешно применены к базе данных shoe_store.sqlite.
Анализ планов выполнения через EXPLAIN QUERY PLAN подтверждает корректную работу оптимизатора. Данные выводятся в консоль в виде форматированных таблиц.
1. Проверка представлений (VIEW)
Виртуальные таблицы созданы и возвращают корректные агрегированные данные без необходимости каждый раз писать сложные JOIN вручную.
VIEW 1: v_orders_full
Объединяет orders, users и order_items. Корректно рассчитывает итоговую сумму по каждому заказу.
