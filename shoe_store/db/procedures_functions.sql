Задание 3.1. Функция для суммы заказа
CREATE OR REPLACE FUNCTION calc_total_pg(price NUMERIC, quantity INTEGER)
RETURNS NUMERIC AS $$
BEGIN
    RETURN price * quantity;
END;
$$ LANGUAGE plpgsql;

Задание 3.2. Процедура для создания заказа
CREATE OR REPLACE PROCEDURE create_order_pg(
    p_user_id INTEGER, 
    p_stock_item_id INTEGER, 
    p_qty INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_price NUMERIC;
BEGIN
Проверка остатка
    SELECT price INTO v_price FROM stock_items WHERE stock_item_id = p_stock_item_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Товар не найден на складе';
    END IF;

Вставка заказа
    INSERT INTO orders (user_id, order_date) 
    VALUES (p_user_id, NOW())
    RETURNING order_id INTO STRICT p_user_id; -- Перезаписываем ID для примера, лучше завести отдельную переменную

Вставка позиций
    INSERT INTO order_items (order_id, stock_item_id, quantity, price)
    VALUES (p_user_id, p_stock_item_id, p_qty, v_price);

Обновление остатков
    UPDATE stock_items 
    SET quantity_available = quantity_available - p_qty 
    WHERE stock_item_id = p_stock_item_id;
END;
$$;

Задание 3.3. Процедура с обработкой ошибок (EXCEPTION)
CREATE OR PROCEDURE safe_update_stock(
    p_stock_item_id INTEGER, 
    p_qty INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_qty INTEGER;
BEGIN
    SELECT quantity_available INTO v_current_qty 
    FROM stock_items 
    WHERE stock_item_id = p_stock_item_id;

    IF v_current_qty < p_qty THEN
        RAISE NOTICE 'Недостаточно товара на складе! Доступно: %, запрошено: %', v_current_qty, p_qty;
        RETURN;
    END IF;

    UPDATE stock_items 
    SET quantity_available = quantity_available - p_qty 
    WHERE stock_item_id = p_stock_item_id;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Произошла непредвиденная ошибка: %', SQLERRM;
END;
$$;