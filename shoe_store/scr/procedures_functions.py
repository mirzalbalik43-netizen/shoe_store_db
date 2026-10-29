import sqlite3
from datetime import datetime

def calc_order_total(price, quantity):

    if price is None or quantity is None:
        return 0.0
    try:
        price = float(price)
        quantity = int(quantity)
    except (ValueError, TypeError):
        return 0.0

    if quantity <= 0:
        return 0.0
    
    return round(price * quantity, 2)

def get_category_count(conn, category_name):
    
    if not conn or not category_name:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE category = ?", 
            (category_name.strip(),)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception:
        return 0

def format_phone(phone):
    
    if phone is None:
        return ""
    
    digits = ''.join(filter(str.isdigit, str(phone)))
    
    if len(digits) == 11 and digits[0] in ['8', '7']:
        if digits[0] == '8':
            digits = '7' + digits[1:]
        return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return str(phone)

def create_order(conn, user_id, stock_item_id, quantity):
    """Процедура создания нового заказа."""
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT quantity_available FROM stock_items WHERE stock_item_id = ?", 
            (stock_item_id,)
        )
        stock = cursor.fetchone()
        if not stock or stock[0] < quantity:
            print("Ошибка: недостаточно товара на складе.")
            return False

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO orders (user_id, order_date) VALUES (?, ?)", 
            (user_id, current_date)
        )
        order_id = cursor.lastrowid

        cursor.execute(
            "SELECT price FROM stock_items WHERE stock_item_id = ?", 
            (stock_item_id,)
        )
        price = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO order_items (order_id, stock_item_id, quantity, price) VALUES (?, ?, ?, ?)",
            (order_id, stock_item_id, quantity, price)
        )

        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Транзакция create_order отменена: {e}")
        return False

def update_stock(conn, stock_item_id, quantity_sold):
    
    try:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT quantity_available FROM stock_items WHERE stock_item_id = ? FOR UPDATE", 
            (stock_item_id,)
        )
        
        
        current_qty = cursor.fetchone()[0]
        
        if current_qty < quantity_sold:
            raise ValueError("Попытка списать больше, чем есть на складе.")
            
        cursor.execute(
            "UPDATE stock_items SET quantity_available = quantity_available - ? WHERE stock_item_id = ?", 
            (quantity_sold, stock_item_id)
        )
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка update_stock, откат: {e}")
        return False

def get_sales_report(conn, start_date, end_date):

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT SUM(oi.quantity * oi.price) as total_revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_date BETWEEN ? AND ?
            """, 
            (start_date, end_date)
        )
        total = cursor.fetchone()[0]
        
        if total is None:
            total = 0.0
            
        return f"С {start_date} по {end_date} продано товаров на сумму {round(total, 2)} руб."
        
    except Exception as e:
        print(f"Ошибка генерации отчета: {e}")
        return "Ошибка при формировании отчета"


def register_functions(conn):
    conn.create_function("calculate_total", 2, calc_order_total)
    conn.create_function("count_in_category", 1, lambda conn, name: get_category_count(conn, name))
    conn.create_function("format_phone", 1, format_phone)