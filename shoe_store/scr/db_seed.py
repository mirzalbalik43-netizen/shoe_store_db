
import argparse
from pathlib import Path
from db_init import DB_PATH, get_connection, init_db

ROLES = [(1, 'Администратор'), (2, 'Менеджер'), (3, 'Авторизованный пользователь')]
USERS = [
    (1, 'Иванов', 'Пётр', 'Сергеевич', 'admin', 1),
    (2, 'Смирнова', 'Анна', 'Олеговна', 'manager', 2),
    (3, 'Кузнецов', 'Алексей', 'Викторович', 'user', 3),
]
SIZES = [(1, 36.0), (2, 37.0), (3, 38.0), (4, 39.0), (5, 40.0)]
PRODUCTS = [
    (1, 'Мужская обувь', 'Кроссовки', 'NordStep', 'Runner Pro', 'images/runner_pro.jpg',
     'Текстиль, резина', 'Для повседневной носки', 3499.90),
    (2, 'Женская обувь', 'Кеды', 'UrbanWay', 'City Light', 'images/city_light.jpg',
     'Хлопок, резина', 'Лёгкие городские кеды', 2890.00),
    (3, 'Мужская обувь', 'Ботинки', 'TerraWalk', 'Winter Trail', 'images/winter_trail.jpg',
     'Кожа, мех', 'Утеплённые ботинки', 7490.50),
    (4, 'Женская обувь', 'Туфли', 'Elegance', 'Classic Line', 'images/classic_line.jpg',
     'Экокожа', 'Классические туфли', 4299.00),
    (5, 'Детская обувь', 'Кроссовки', 'MiniMove', 'Jump Kids', 'images/jump_kids.jpg',
     'Текстиль, ЭВА', 'Для активных прогулок', 2190.00),
]
STOCK_ITEMS = [
    (1,1,1,9),(2,1,2,12),(3,1,3,5),(4,2,3,7),(5,2,4,0),
    (6,3,4,3),(7,3,5,6),(8,4,1,8),(9,4,5,4),(10,5,2,11),
]
ORDERS = [(1, '2026-10-10', 1), (2, '2026-10-11', 2), (3, '2026-10-12', 3)]
ORDER_ITEMS = [
    (1,1,1,1,3299.90),(2,1,8,1,4299.00),
    (3,2,4,2,2890.00),(4,2,6,1,7490.50),
    (5,3,7,1,7490.50),(6,3,10,2,2190.00),
]
SEED = [
    ('roles', ('role_id', 'role_name'), ROLES),
    ('sizes', ('size_id', 'size_value'), SIZES),
    ('users', ('user_id', 'last_name', 'first_name', 'middle_name', 'login', 'role_id'), USERS),
    ('products', ('product_id', 'category', 'subcategory', 'manufacturer', 'product_name',
                  'image_path', 'composition', 'description', 'price'), PRODUCTS),
    ('stock_items', ('stock_item_id', 'product_id', 'size_id', 'quantity_available'), STOCK_ITEMS),
    ('orders', ('order_id', 'order_date', 'user_id'), ORDERS),
    ('order_items', ('order_item_id','order_id','stock_item_id','quantity','price'), ORDER_ITEMS),
]


def seed_roles(conn):
    return _seed_one(conn, SEED[0])


def seed_sizes(conn):
    return _seed_one(conn, SEED[1])


def seed_users(conn):
    return _seed_one(conn, SEED[2])


def seed_products(conn):
    return _seed_one(conn, SEED[3])


def seed_stock_items(conn):
    return _seed_one(conn, SEED[4])


def seed_orders(conn):
    return _seed_one(conn, SEED[5])


def seed_order_items(conn):
    return _seed_one(conn, SEED[6])


def _seed_one(conn, spec):
    table, columns, data = spec
    placeholders = ', '.join('?' for _ in columns)
    statement = f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({placeholders}) ON CONFLICT({columns[0]}) DO NOTHING'
    conn.executemany(statement, data)
    return len(data)


def seed_database(conn):
    for spec in SEED:
        _seed_one(conn, spec)
    conn.commit()
    return {table: conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
            for table, _, _ in SEED}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Заполнение тестовыми данными')
    parser.add_argument('--db', type=Path, default=DB_PATH)
    args = parser.parse_args(argv)
    init_db(args.db)
    with get_connection(args.db) as conn:
        counts = seed_database(conn)
        # Триггеры ставим после учебного наполнения, чтобы исторические заказы
        # повторно не списали исходные остатки.
        from db_apply_triggers import apply_triggers
        apply_triggers(conn)
    print('Заполнены таблицы:', ', '.join(f'{t}={count}' for t,count in counts.items()))


if __name__ == '__main__':
    main()
