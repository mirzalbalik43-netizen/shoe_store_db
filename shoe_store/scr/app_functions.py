import sqlite3
from datetime import datetime


def calc_discount(price, discount_percent):
    if price is None or discount_percent is None:
        return 0.0
    
    try:
        price = float(price)
        discount_percent = float(discount_percent)
    except (ValueError, TypeError):
        return 0.0

    if discount_percent < 0:
        discount_percent = 0
    if discount_percent > 100:
        discount_percent = 100
        
    discounted_price = price - (price * discount_percent / 100)
    return round(discounted_price, 2)

def pluralize_items(count):
    if count is None:
        return "0 товаров"
    
    try:
        n = int(count)
    except (ValueError, TypeError):
        return "0 товаров"

    if n % 10 == 1 and n % 100 != 11:
        return f"{n} товар"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return f"{n} товара"
    else:
        return f"{n} товаров"

def format_full_name(last, first, middle):
    if not last or not first or last.isspace() or first.isspace():
        return "Аноним"
    
    last = last.strip().title()
    first = first.strip().title()
    
    if middle and not middle.isspace():
        middle = middle.strip().title()
        return f"{last} {first[0]}.{middle[0]}."
    else:
        return f"{last} {first[0]}."

def get_client_tier(total_spent):
    if total_spent is None:
        total_spent = 0
    
    try:
        total_spent = float(total_spent)
    except (ValueError, TypeError):
        return "Без статуса"
        
    if total_spent < 0:
        return "Без статуса"
    if total_spent < 5000:
        return "Новичок"
    if total_spent < 20000:
        return "Бронза"
    if total_spent < 50000:
        return "Серебро"
    if total_spent < 100000:
        return "Золото"
    return "Платина"

def get_client_loyalty_days(first_order_date_str):
    if not first_order_date_str:
        return 0
    try:
        first_date = datetime.strptime(first_order_date_str, "%Y-%m-%d")
        delta = datetime.now() - first_date
        return delta.days
    except ValueError:
        return 0


def place_order(conn, user_id, product_id, size_id, quantity):
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            return False
            
        cursor.execute(
            "SELECT stock_item_id, quantity_available, price FROM stock_items WHERE product_id = ? AND size_id = ?", 
            (product_id, size_id)
        )
        stock_item = cursor.fetchone()
        if not stock_item:
            return False
            
        stock_item_id, quantity_available, price = stock_item
        
        if quantity_available < quantity:
            print(f"Ошибка: недостаточно товара на складе (есть {quantity_available}, запрошено {quantity})")
            return False
            
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO orders (user_id, order_date) VALUES (?, ?)", 
            (user_id, current_date)
        )
        order_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, size_id, quantity, price) VALUES (?, ?, ?, ?, ?)",
            (order_id, product_id, size_id, quantity, price)
        )
        
        cursor.execute(
            "UPDATE stock_items SET quantity_available = quantity_available - ? WHERE stock_item_id = ?", 
            (quantity, stock_item_id)
        )
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Транзакция отменена из-за ошибки: {e}")
        return False

def cancel_order(conn, order_id):
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM orders WHERE order_id = ?", (order_id,))
        if not cursor.fetchone():
            return False
            
        cursor.execute(
            "SELECT stock_item_id, quantity FROM order_items WHERE order_id = ?", 
            (order_id,)
        )
        items = cursor.fetchall()
        
        for stock_item_id, quantity in items:
            cursor.execute(
                "UPDATE stock_items SET quantity_available = quantity_available + ? WHERE stock_item_id = ?", 
                (quantity, stock_item_id)
            )

        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при отмене заказа: {e}")
        return False


def register_functions(conn):
    conn.create_function("calc_discount", 2, calc_discount)
    conn.create_function("pluralize_items", 1, pluralize_items)
    conn.create_function("format_full_name", 3, format_full_name)
    conn.create_function("get_client_tier", 1, get_client_tier)
    conn.create_function("get_client_loyalty_days", 1, get_client_loyalty_days)