УП.11 №10. Демонстрация функций SQLite.
Команды SELECT требуют регистрации через src/procedures_functions.py
(conn.create_function(...) действует лишь в рамках одного соединения).

1. Сумма по каждому заказу.
SELECT oi.order_id,
       ROUND(SUM(calculate_total(oi.price, oi.quantity)), 2) AS order_total
FROM order_items AS oi
GROUP BY oi.order_id
ORDER BY oi.order_id;

2. Число товаров в каждой категории.
SELECT categories.category,
       count_in_category(categories.category) AS products_count
FROM (SELECT DISTINCT category FROM products) AS categories
ORDER BY categories.category;

3. Телефоны - иллюстративный набор для пользователей. Реальная таблица
users из предыдущих дней телефона не имеет, схема намеренно сохранена.
WITH demo_phones(user_id, phone) AS (
    VALUES (1, '89991234567'), (2, '89161234567'), (3, 'не указан')
)
SELECT u.user_id, u.last_name, u.first_name,
       demo_phones.phone, format_phone(demo_phones.phone) AS formatted_phone
FROM users AS u
LEFT JOIN demo_phones ON demo_phones.user_id = u.user_id
ORDER BY u.user_id;
