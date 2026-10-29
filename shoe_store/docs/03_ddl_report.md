Отчёт о финальном DDL-скрипте

Назначение

Файл src/db_init.py содержит финальный DDL-скрипт
Скрипт создаёт все таблицы ограничения и индексы
Скрипт исполняем с нуля
Запустил получил работающую базу

Создаваемые таблицы

Таблица roles справочник ролей
Таблица sizes справочник размеров
Таблица products товары
Таблица users пользователи
Таблица stock_items товарные позиции
Таблица orders заказы
Таблица order_items позиции заказов

Порядок создания таблиц

Сначала справочники roles sizes
Потом независимые products users
Потом stock_items потому что ссылается на products и sizes
Потом orders потому что ссылается на users
Потом order_items потому что ссылается на orders и stock_items

Такой порядок нужен потому что внешние ключи ссылаются на уже созданные таблицы

Ограничения в скрипте

NOT NULL на все обязательные поля
UNIQUE на roles role_name sizes size_value users login
CHECK на products product_name price
CHECK на sizes size_value
CHECK на users login
CHECK на stock_items quantity
CHECK на orders order_date
CHECK на order_items quantity price
PRIMARY KEY AUTOINCREMENT на все id
FOREIGN KEY на все внешние ключи
DEFAULT на stock_items quantity и orders order_date

Индексы в скрипте

idx_users_role_id
idx_orders_user_id
idx_orders_order_date
idx_products_category
idx_products_manufacturer
idx_stock_items_product_id
idx_stock_items_size_id
idx_order_items_order_id
idx_order_items_stock_item_id

Всего 9 индексов

Стратегии удаления

ON DELETE RESTRICT для ролей размеров пользователей и товарных позиций
ON DELETE CASCADE для товаров и заказов

Внешние ключи

Включены через PRAGMA foreign_keys = ON в функции get_connection