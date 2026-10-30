
from db_init import get_connection

CHECKS = {
    'Нарушенные FK': 'SELECT count(*) FROM pragma_foreign_key_check',
    'Дубли логинов': 'SELECT count(*) FROM (SELECT login FROM users GROUP BY login HAVING count(*) > 1)',
    'Пустые логины': "SELECT count(*) FROM users WHERE length(trim(login)) = 0",
    'Некорректная длина логина': 'SELECT count(*) FROM users WHERE length(login) NOT BETWEEN 3 AND 20',
    'Некорректные цены товаров': 'SELECT count(*) FROM products WHERE price <= 0 OR price >= 1000000',
    'Пустые названия товаров': "SELECT count(*) FROM products WHERE length(trim(product_name)) = 0",
    'Некорректные остатки': 'SELECT count(*) FROM stock_items WHERE quantity_available < 0',
    'Некорректные размеры': 'SELECT count(*) FROM sizes WHERE size_value <= 20 OR size_value >= 50',
    'Некорректные количества заказа': 'SELECT count(*) FROM order_items WHERE quantity <= 0',
    'Некорректные цены в заказе': 'SELECT count(*) FROM order_items WHERE price <= 0',
    'Некорректные даты заказа':
        "SELECT count(*) FROM orders WHERE order_date <> date(order_date, '+0 days') "
        "OR date(order_date, '+0 days') IS NULL OR length(order_date) <> 10",
    'Повторные размеры товара': 'SELECT count(*) FROM (SELECT product_id, size_id FROM stock_items '
        'GROUP BY product_id, size_id HAVING count(*) > 1)',
}


def validate():
    with get_connection() as conn:
        result = {name: conn.execute(sql).fetchone()[0] for name, sql in CHECKS.items()}
        result['PRAGMA integrity_check'] = conn.execute('PRAGMA integrity_check').fetchone()[0]
    return result


if __name__ == '__main__':
    r = validate()
    for name, value in r.items():
        print(f'{name}: {value}')
    raise SystemExit(0 if all(v == 0 if k != 'PRAGMA integrity_check' else v == 'ok'
                              for k, v in r.items()) else 1)
