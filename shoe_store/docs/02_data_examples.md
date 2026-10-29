# Типы данных для полей базы данных shoe_store

## Таблица roles
- role_id - идентификатор роли (PK)
- role_name - название роли

## Таблица users
- user_id - идентификатор пользователя (PK)
- last_name - фамилия
- first_name - имя
- middle_name - отчество
- login - логин
- role_id - ссылка на роль (FK)

## Таблица products
- product_id - идентификатор товара (PK)
- product_name - наименование товара
- category - категория
- manufacturer - производитель
- price - цена
- image_path - путь к изображению

## Таблица sizes
- size_id - идентификатор размера (PK)
- size_value - значение размера

## Таблица stock_items
- stock_item_id - идентификатор товарной позиции (PK)
- product_id - ссылка на товар (FK)
- size_id - ссылка на размер (FK)
- quantity - доступное количество

## Таблица orders
- order_id - идентификатор заказа (PK)
- user_id - ссылка на пользователя (FK)
- order_date - дата заказа

## Таблица order_items
- order_item_id - идентификатор позиции заказа (PK)
- order_id - ссылка на заказ (FK)
- stock_item_id - ссылка на товарную позицию (FK)
- quantity - количество товара в заказе
- price - цена товарной позиции в заказе

