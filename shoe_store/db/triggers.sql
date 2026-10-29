
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TEXT DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS trg_audit_price_update
AFTER UPDATE ON products
WHEN OLD.price != NEW.price
BEGIN
    INSERT INTO audit_log (table_name, operation, record_id, old_value, new_value)
    VALUES ('products', 'UPDATE', OLD.product_id, OLD.price, NEW.price);
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_order_delete
AFTER DELETE ON orders
BEGIN
    INSERT INTO audit_log (table_name, operation, record_id, old_value, new_value)
    VALUES ('orders', 'DELETE', OLD.order_id, NULL, NULL);
END;

CREATE TRIGGER IF NOT EXISTS trg_update_timestamp
AFTER UPDATE ON users
BEGIN
    UPDATE users 
    SET updated_at = datetime('now') 
    WHERE user_id = OLD.user_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_reduce_stock_after_insert
AFTER INSERT ON order_items
BEGIN
    UPDATE stock_items 
    SET quantity_available = quantity_available - NEW.quantity 
    WHERE stock_item_id = NEW.stock_item_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_protect_user_delete
BEFORE DELETE ON users
BEGIN
    SELECT CASE 
        WHEN (SELECT COUNT(*) FROM orders WHERE user_id = OLD.user_id) > 0 
        THEN RAISE(ABORT, 'Нельзя удалить пользователя с активными заказами')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_check_stock_quantity
BEFORE INSERT ON stock_items
WHEN NEW.quantity_available < 0
BEGIN
    SELECT RAISE(ABORT, 'Количество не может быть отрицательным');
END;