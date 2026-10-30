-- УП.11 №3: 10 SQL-проверок корректности данных (ожидается 0 строк / 0 нарушений).
-- 1. Проверка внешних ключей (0 строк)
PRAGMA foreign_key_check;
-- 2. Товары с неправильной ценой (0 строк)
SELECT * FROM products WHERE price <= 0 OR price >= 1000000;
-- 3. Пустые наименования товара (0 строк)
SELECT * FROM products WHERE length(trim(product_name)) = 0;
-- 4. Повторяющиеся логины (0 строк)
SELECT login, count(*) AS cnt FROM users GROUP BY login HAVING count(*) > 1;
-- 5. Невалидные логины (0 строк)
SELECT * FROM users WHERE length(login) NOT BETWEEN 3 AND 20;
-- 6. Отрицательные складские остатки (0 строк)
SELECT * FROM stock_items WHERE quantity_available < 0;
-- 7. Ошибочные размеры обуви (0 строк)
SELECT * FROM sizes WHERE size_value <= 20 OR size_value >= 50;
-- 8. Неположительные количества в заказах (0 строк)
SELECT * FROM order_items WHERE quantity <= 0;
-- 9. Неположительные цены позиций заказов (0 строк)
SELECT * FROM order_items WHERE price <= 0;
-- 10. Дубли сочетаний товар/размер (0 строк)
SELECT product_id, size_id, count(*) AS cnt FROM stock_items
GROUP BY product_id, size_id HAVING count(*) > 1;
