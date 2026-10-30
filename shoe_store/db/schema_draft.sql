-- Учебный промежуточный DDL, согласован с финальными именами (день 4).
-- УП.11 №4. «Чудо Обувь»: полная исполняемая схема базы данных SQLite.
-- Названия полей строго соответствуют формулировкам практической №4.
-- Запуск: sqlite3 shoe_store.sqlite < schema.sql (или python src/db_init.py).
PRAGMA foreign_keys = ON;

-- 1. roles — справочник ролей (PK, UNIQUE, NOT NULL).
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE CHECK (length(trim(role_name)) > 0)
);

-- 2. sizes — справочник размеров обуви, включая половинные (например, 36.5).
CREATE TABLE IF NOT EXISTS sizes (
    size_id INTEGER PRIMARY KEY AUTOINCREMENT,
    size_value REAL NOT NULL UNIQUE
        CHECK (typeof(size_value) IN ('integer', 'real') AND size_value > 20 AND size_value < 50)
);

-- 3. users — логин уникален и имеет длину 3–20; роль нельзя удалить,
-- пока на неё ссылается хотя бы один пользователь.
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name TEXT NOT NULL CHECK (length(trim(last_name)) > 0),
    first_name TEXT NOT NULL CHECK (length(trim(first_name)) > 0),
    middle_name TEXT,
    login TEXT NOT NULL UNIQUE
        CHECK (length(login) BETWEEN 3 AND 20 AND length(trim(login)) > 0),
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);

-- 4. products — карточка модели; цена положительна и меньше 1 млн руб.
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK (length(trim(category)) > 0),
    subcategory TEXT,
    manufacturer TEXT NOT NULL CHECK (length(trim(manufacturer)) > 0),
    product_name TEXT NOT NULL CHECK (length(trim(product_name)) > 0),
    image_path TEXT,
    composition TEXT,
    description TEXT,
    price REAL NOT NULL
        CHECK (typeof(price) IN ('integer', 'real') AND price > 0 AND price < 1000000)
);

-- 5. stock_items — одна строка для каждой уникальной пары товар/размер.
CREATE TABLE IF NOT EXISTS stock_items (
    stock_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    size_id INTEGER NOT NULL,
    quantity_available INTEGER NOT NULL DEFAULT 0
        CHECK (typeof(quantity_available) = 'integer' AND quantity_available >= 0),
    UNIQUE (product_id, size_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT,
    FOREIGN KEY (size_id) REFERENCES sizes(size_id) ON DELETE RESTRICT
);

-- 6. orders — дата ISO 8601; default текущая дата (допустимое выражение SQLite).
-- date(x,'+0 days') нормализует 2026-02-30, так что ошибочный день отклоняется.
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date TEXT NOT NULL DEFAULT (date('now'))
        CHECK (
            typeof(order_date) = 'text' AND
            length(order_date) = 10 AND
            order_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND
            date(order_date, '+0 days') IS NOT NULL AND
            date(order_date, '+0 days') = order_date
        ),
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

-- 7. order_items — количество и историческая цена на момент покупки.
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    stock_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (typeof(quantity) = 'integer' AND quantity > 0),
    price REAL NOT NULL CHECK (typeof(price) IN ('integer','real') AND price > 0),
    UNIQUE (order_id, stock_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(stock_item_id) ON DELETE RESTRICT
);

-- Индексы на всех шести внешних ключах.
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_stock_items_product_id ON stock_items(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_items_size_id ON stock_items(size_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_stock_item_id ON order_items(stock_item_id);
-- Индексы для фильтрации и сортировки каталога/заказов.
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_manufacturer ON products(manufacturer);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);

-- Дополнительное задание: представление заказов с итоговой суммой.
-- Не создаёт восьмую таблицу: сумма вычисляется по позициям.
CREATE VIEW IF NOT EXISTS v_orders_full AS
SELECT o.order_id, o.order_date, u.user_id,
       trim(u.last_name || ' ' || u.first_name || ' ' || coalesce(u.middle_name,'')) AS client_name,
       round(coalesce(sum(oi.quantity * oi.price), 0), 2) AS total_amount
FROM orders AS o
JOIN users AS u ON u.user_id = o.user_id
LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.order_date, u.user_id,
         u.last_name, u.first_name, u.middle_name;

-- Дополнительное представление из дня 3: общий остаток по каждой модели.
CREATE VIEW IF NOT EXISTS v_products_with_stock AS
SELECT p.product_id, p.product_name, p.manufacturer, p.price,
       coalesce(sum(s.quantity_available), 0) AS total_quantity
FROM products p LEFT JOIN stock_items s ON s.product_id=p.product_id
GROUP BY p.product_id, p.product_name, p.manufacturer, p.price;
