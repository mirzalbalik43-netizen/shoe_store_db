

VIEW 1: Полная информация о заказах
CREATE VIEW v_orders_full AS
SELECT 
    o.order_id,
    o.order_date,
    u.first_name || ' ' || u.last_name AS full_name,
    SUM(oi.quantity * oi.price) AS total_sum
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.order_date, u.first_name, u.last_name;

VIEW 2: Товары с остатками
CREATE VIEW v_products_with_stock AS
SELECT 
    p.model_name,
    p.price,
    s.size_value,
    st.quantity
FROM products p
JOIN stock_items st ON p.product_id = st.product_id
JOIN sizes s ON st.size_id = s.size_id;

VIEW 3: Статистика по клиентам
CREATE VIEW v_user_stats AS
SELECT 
    u.first_name || ' ' || u.last_name AS full_name,
    u.login,
    COUNT(o.order_id) AS orders_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.first_name, u.last_name, u.login;

Задание 2. Создание индексов
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_orders_date ON orders (order_date);
CREATE INDEX idx_orders_user_id ON orders (user_id);
CREATE INDEX idx_stock_product_id ON stock_items (product_id);
CREATE INDEX idx_stock_size_id ON stock_items (size_id);
CREATE INDEX idx_products_manufacturer_category ON products (category, manufacturer);