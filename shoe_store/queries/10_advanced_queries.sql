1. Цена со скидкой 20%
SELECT 
    product_name, 
    price, 
    calc_discount(price, 20) AS discounted_price
FROM products;

2. Клиенты без отчества
SELECT 
    format_full_name(last_name, first_name, middle_name) AS full_name
FROM clients;

3. Количество товара в заказе со склонением
SELECT 
    order_id, 
    quantity, 
    pluralize_items(quantity) AS quantity_text
FROM order_items;

4. Сумма заказа клиента со скидкой 10%
SELECT 
    c.first_name || ' ' || c.last_name AS client_name,
    SUM(calc_discount(oi.price * oi.quantity, 10)) AS total_with_discount
FROM orders o
JOIN clients c ON o.user_id = c.user_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, client_name;

5. Аналитика: уровень и стаж клиента
SELECT 
    format_full_name(c.last_name, c.first_name, c.middle_name) AS full_name,
    SUM(p.price * oi.quantity) AS total_spent,
    get_client_tier(SUM(p.price * oi.quantity)) AS tier,
    get_client_loyalty_days(MIN(o.order_date)) AS loyalty_days
FROM clients c
JOIN orders o ON c.user_id = o.user_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY c.user_id, full_name;