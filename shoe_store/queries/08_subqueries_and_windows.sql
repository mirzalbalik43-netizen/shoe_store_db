Задание 1. Скалярные подзапросы
1. Товары дороже средней цены
SELECT product_name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);

2. Пользователь с самым дорогим заказом
SELECT u.last_name, u.first_name
FROM users u
JOIN orders o ON u.user_id = o.user_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE (oi.price * oi.quantity) = (
    SELECT MAX(oi2.price * oi2.quantity) 
    FROM order_items oi2
);

Задание 2. Подзапросы с IN и EXISTS
3. Клиенты, у которых есть хотя бы один заказ (IN)
SELECT last_name 
FROM users
WHERE user_id IN (SELECT user_id FROM orders);

4. Пользователи без заказов (NOT EXISTS)
SELECT last_name, first_name
FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id);

5. Товары, которые ни разу не были заказаны (NOT IN)
SELECT product_name
FROM products
WHERE product_id NOT IN (SELECT DISTINCT product_id FROM stock_items WHERE stock_item_id IN (SELECT stock_item_id FROM order_items));

Задание 3. Ранжирование и группировка (Оконные функции)
6. Клиенты и сумма их заказов с рангом (RANK)
SELECT u.last_name, u.first_name, SUM(oi.price * oi.quantity) AS total_spent,
    RANK() OVER(ORDER BY SUM(oi.price * oi.quantity) DESC) AS rnk
FROM users u
JOIN order_items oi ON u.user_id = oi.user_id
GROUP BY u.user_id;

7. Порядковый номер заказа клиента от старых к новым (ROW_NUMBER)
SELECT o.order_id, u.last_name, u.first_name, o.order_date,
    ROW_NUMBER() OVER(PARTITION BY u.user_id ORDER BY o.order_date ASC) AS order_num
FROM orders o
JOIN users u ON o.user_id = u.user_id;

8. Товары по категориям с нумерацией по убыванию цены
SELECT product_name, category, price,
    ROW_NUMBER() OVER(PARTITION BY category ORDER BY price DESC) AS price_rank_in_cat
FROM products;

9. Самый дорогой товар в каждой категории (через табличный подзапрос)
WITH RankedProducts AS (
    SELECT product_name, category, price,
        ROW_NUMBER() OVER(PARTITION BY category ORDER BY price DESC) AS rn
    FROM products
)
SELECT product_name, category, price
FROM RankedProducts
WHERE rn = 1;

Задание 4. Нарастающие итоги и сдвиги
10. Накопительная сумма заказов по датам
SELECT order_date, SUM(total_amount) OVER(ORDER BY order_date) AS running_total
FROM (
    SELECT order_date, SUM(oi.price * oi.quantity) AS total_amount
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY order_date
) AS daily;

11. Дата текущего и предыдущего заказа клиента + разница в днях
SELECT u.last_name, u.first_name, o.order_date,
    LAG(o.order_date) OVER(PARTITION BY u.user_id ORDER BY o.order_date) AS prev_order_date,
    CAST(julianday(o.order_date) - julianday(LAG(o.order_date) OVER(PARTITION BY u.user_id ORDER BY o.order_date))) AS days_diff
FROM orders o
JOIN users u ON o.user_id = u.user_id;