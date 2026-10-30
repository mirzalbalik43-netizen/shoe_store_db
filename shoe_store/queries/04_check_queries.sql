1. Все роли
SELECT role_id, role_name FROM roles ORDER BY role_id;

2. Пользователи с ролями
SELECT u.user_id, u.login, u.last_name, u.first_name, u.middle_name, r.role_name
FROM users u JOIN roles r ON u.role_id = r.role_id ORDER BY u.user_id;

3. Каталог товаров
SELECT product_id, product_name, category, subcategory, manufacturer, price, image_path
FROM products ORDER BY product_id;

4. Размеры обуви
SELECT size_id, size_value FROM sizes ORDER BY size_value;

5. Заказы с ФИО клиентов и датой
SELECT o.order_id, o.order_date,
       trim(u.last_name || ' ' || u.first_name || ' ' || coalesce(u.middle_name,'')) AS client_name
FROM orders o JOIN users u ON u.user_id = o.user_id ORDER BY o.order_id;

6. Остатки модели по каждому размеру
SELECT s.stock_item_id, p.product_name, z.size_value, s.quantity_available
FROM stock_items s
JOIN products p ON p.product_id = s.product_id
JOIN sizes z ON z.size_id = s.size_id
ORDER BY s.stock_item_id;

7. Представление с итоговой суммой заказов (дополнительное задание)
SELECT order_id, order_date, client_name, total_amount FROM v_orders_full ORDER BY order_id;
