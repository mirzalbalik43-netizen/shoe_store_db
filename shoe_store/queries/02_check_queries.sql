Запрос 1. Список всех пользователей с ролями
SELECT u.user_id, u.last_name, u.first_name, u.middle_name, u.login, r.role_name
FROM users u
JOIN roles r ON u.role_id = r.role_id;

Запрос 2. Список всех товаров
SELECT product_id, product_name, category, manufacturer, price, image_path
FROM products;

Запрос 3. Список всех размеров
SELECT size_id, size_value
FROM sizes
ORDER BY size_value;

Запрос 4. Список всех заказов с ФИО клиентов
SELECT o.order_id, u.last_name, u.first_name, u.middle_name, o.order_date
FROM orders o
JOIN users u ON o.user_id = u.user_id
ORDER BY o.order_date;

Запрос 5. Список всех товарных позиций с наименованием товара и размером
SELECT si.stock_item_id, p.product_name, s.size_value, si.quantity
FROM stock_items si
JOIN products p ON si.product_id = p.product_id
JOIN sizes s ON si.size_id = s.size_id
ORDER BY p.product_name, s.size_value;