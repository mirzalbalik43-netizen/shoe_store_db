Задание 1. Простые JOIN
1. Список всех заказов с датой и ФИО клиента
SELECT o.order_id, o.order_date, u.last_name, u.first_name
FROM orders o
INNER JOIN users u ON o.user_id = u.user_id;

2. Товарные позиции с названием модели и размером
SELECT si.stock_item_id, p.product_name, s.size_value
FROM stock_items si
JOIN products p ON si.product_id = p.product_id
JOIN sizes s ON si.size_id = s.size_id;

3. Заказы с ФИО клиента и названием купленного товара
SELECT o.order_id, u.last_name, u.first_name, p.product_name
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN stock_items si ON oi.stock_item_id = si.stock_item_id
JOIN products p ON si.product_id = p.product_id;

4. Все пользователи и количество их заказов (LEFT JOIN)
SELECT u.user_id, u.last_name, u.first_name, COUNT(o.order_id) AS order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id;

Задание 2. Базовые агрегатные функции
5. Общее количество пользователей
SELECT COUNT(*) AS total_users FROM users;

6. Средняя цена всех товаров
SELECT AVG(price) AS avg_price FROM products;

7. Самый дорогой и самый дешевый товар
SELECT MIN(price) AS min_price, MAX(price) AS max_price FROM products;

8. Общая сумма всех проданных товаров (выручка)
SELECT SUM(oi.quantity * oi.price) AS total_revenue
FROM order_items oi;

Задание 3. Группировка GROUP BY
9. Количество товаров в каждой категории
SELECT category, COUNT(*) AS product_count
FROM products
GROUP BY category;

10. Производители и средняя цена их товаров
SELECT manufacturer, AVG(price) AS avg_price
FROM products
GROUP BY manufacturer;

11. ФИО пользователя и общая сумма его заказов
SELECT u.user_id, u.last_name, u.first_name, SUM(oi.quantity * oi.price) AS total_spent
FROM users u
JOIN order_items oi ON u.user_id = oi.user_id
GROUP BY u.user_id;

12. Статистика продаж для каждой модели: название и продано пар
SELECT p.product_name, SUM(oi.quantity) AS total_sold
FROM order_items oi
JOIN stock_items si ON oi.stock_item_id = si.stock_item_id
JOIN products p ON si.product_id = p.product_id
GROUP BY p.product_name;

13. Список размеров и количество позиций в этом размере
SELECT s.size_value, COUNT(si.stock_item_id) AS items_count
FROM sizes s
JOIN stock_items si ON s.size_id = si.size_id
GROUP BY s.size_value;

Задание 4. Фильтрация групп HAVING
14. Категории, в которых больше 3 моделей
SELECT category, COUNT(*) AS model_count
FROM products
GROUP BY category
HAVING COUNT(*) > 3;

15. Клиенты, сделавшие больше 2 заказов
SELECT u.user_id, u.last_name, u.first_name, COUNT(o.order_id) AS order_count
FROM users u
JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id
HAVING COUNT(o.order_id) > 2;

16. Модели, общая сумма продаж которых превысила 100 000
SELECT p.product_name, SUM(oi.quantity * oi.price) AS total_sales
FROM products p
JOIN stock_items si ON p.product_id = si.product_id
JOIN order_items oi ON si.stock_item_id = oi.stock_item_id
GROUP BY p.product_name
HAVING SUM(oi.quantity * oi.price) > 100000;

Задание 5. Комбинированный аналитический отчет
17. Топ-3 самых популярных размеров обуви
SELECT s.size_value, SUM(oi.quantity) AS bought_count
FROM sizes s
JOIN stock_items si ON s.size_id = si.size_id
JOIN order_items oi ON si.stock_item_id = oi.stock_item_id
GROUP BY s.size_value
ORDER BY bought_count DESC
LIMIT 3;

18. Пользователи, которые ни разу ничего не заказали
SELECT u.user_id, u.last_name, u.first_name
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_id IS NULL;

19. Средний чек (средняя стоимость одного заказа)
SELECT AVG(order_total) AS avg_check FROM (
    SELECT o.order_id, SUM(oi.quantity * oi.price) AS order_total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.order_id
) AS subquery;

20. Производитель, чьи товары принесли наибольшую выручку
SELECT p.manufacturer, SUM(oi.quantity * oi.price) AS total_revenue
FROM products p
JOIN stock_items si ON p.product_id = si.product_id
JOIN order_items oi ON si.stock_item_id = oi.stock_item_id
GROUP BY p.manufacturer
ORDER BY total_revenue DESC
LIMIT 1;