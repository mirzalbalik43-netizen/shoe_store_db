10 учебных запросов к db/schema.sql (при выполнении замените ID/значения).
1. Каталог по алфавиту.
SELECT product_id, product_name, manufacturer, price FROM products ORDER BY product_name;

2. Фильтр категории и цены.
SELECT product_id, product_name, price FROM products
WHERE category = 'Обувь' AND price BETWEEN 1500 AND 6000 ORDER BY price;

3. Остатки и размеры модели с ID=1.
SELECT p.product_name, s.size_value AS size, si.quantity_available
FROM stock_items si
JOIN products p ON p.product_id = si.product_id
JOIN sizes s ON s.size_id = si.size_id
WHERE si.product_id = 1 ORDER BY CAST(s.size_value AS REAL);

4. Заказы за октябрь 2026 года.
SELECT order_id, order_date, user_id FROM orders
WHERE order_date >= '2026-10-01' AND order_date < '2026-11-01'
ORDER BY order_date;

5. Список заказов с ФИО клиента.
SELECT o.order_id, o.order_date,
       u.last_name || ' ' || u.first_name || ' ' || COALESCE(u.middle_name, '') AS customer
FROM orders o JOIN users u ON u.user_id = o.user_id
ORDER BY o.order_date DESC;

6. Состав заказа с ID=1.
SELECT p.product_name, s.size_value AS size, oi.quantity, oi.price,
       oi.quantity * oi.price AS line_amount
FROM order_items oi
JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
JOIN products p ON p.product_id = si.product_id
JOIN sizes s ON s.size_id = si.size_id
WHERE oi.order_id = 1;

7. Суммы всех заказов.
SELECT order_id, total_amount FROM v_orders_full ORDER BY order_id;

8. Пять наиболее продаваемых моделей (в штуках).
SELECT p.product_name, SUM(oi.quantity) AS units_sold
FROM order_items oi
JOIN stock_items si ON si.stock_item_id = oi.stock_item_id
JOIN products p ON p.product_id = si.product_id
GROUP BY p.product_id, p.product_name ORDER BY units_sold DESC LIMIT 5;

9. Пять клиентов с наибольшей суммой заказов.
SELECT u.user_id, u.last_name, u.first_name,
       SUM(ot.total_amount) AS spent_rub
FROM users u JOIN v_orders_full ot ON ot.user_id = u.user_id
GROUP BY u.user_id, u.last_name, u.first_name ORDER BY spent_rub DESC LIMIT 5;

10. Малый остаток (3 пары и меньше).
SELECT p.product_name, s.size_value AS size, si.quantity_available
FROM stock_items si
JOIN products p ON p.product_id = si.product_id
JOIN sizes s ON s.size_id = si.size_id
WHERE si.quantity_available <= 3 ORDER BY si.quantity_available, p.product_name;
