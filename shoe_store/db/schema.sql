PRAGMA foreign_keys = ON;

CREATE TABLE audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE
        );

CREATE TABLE sizes (
            size_id INTEGER PRIMARY KEY AUTOINCREMENT,
            size_value REAL NOT NULL UNIQUE CHECK (size_value > 20 AND size_value < 50)
        );

CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL CHECK (length(product_name) > 0),
            category TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            price NUMERIC NOT NULL CHECK (price > 0 AND price < 1000000),
            image_path TEXT
        );

CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            login TEXT NOT NULL UNIQUE CHECK (length(login) >= 3 AND length(login) <= 20),
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
        );

CREATE TABLE stock_items (
            stock_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            size_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
            FOREIGN KEY (size_id) REFERENCES sizes(size_id) ON DELETE RESTRICT
        );

CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date TEXT NOT NULL DEFAULT CURRENT_DATE CHECK (date(order_date) IS NOT NULL),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
        );

CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            stock_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            price NUMERIC NOT NULL CHECK (price > 0),
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (stock_item_id) REFERENCES stock_items(stock_item_id) ON DELETE RESTRICT
        );

CREATE INDEX idx_users_role_id ON users(role_id);

CREATE INDEX idx_orders_user_id ON orders(user_id);

CREATE INDEX idx_orders_order_date ON orders(order_date);

CREATE INDEX idx_products_category ON products(category);

CREATE INDEX idx_products_manufacturer ON products(manufacturer);

CREATE INDEX idx_stock_items_product_id ON stock_items(product_id);

CREATE INDEX idx_stock_items_size_id ON stock_items(size_id);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);

CREATE INDEX idx_order_items_stock_item_id ON order_items(stock_item_id);

