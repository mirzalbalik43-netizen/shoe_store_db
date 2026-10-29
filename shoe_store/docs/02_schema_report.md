# Отчёт о созданной структуре базы данных

## Созданные таблицы

Всего создано 7 таблиц


roles
Поле       Тип SQLite  Назначение        NOT NULL  DEFAULT  Ограничения
role_id    INTEGER     идентификатор     да        -        PRIMARY KEY AUTOINCREMENT
role_name  TEXT        название роли     да        -        UNIQUE


sizes
Поле        Тип SQLite  Назначение          NOT NULL  DEFAULT  Ограничения
size_id     INTEGER     идентификатор       да        -        PRIMARY KEY AUTOINCREMENT
size_value  REAL        значение размера    да        -        UNIQUE


products
Поле          Тип SQLite  Назначение            NOT NULL  DEFAULT  Ограничения
product_id    INTEGER     идентификатор         да        -        PRIMARY KEY AUTOINCREMENT
product_name  TEXT        наименование          да        -        -
category      TEXT        категория             да        -        -
manufacturer  TEXT        производитель         да        -        -
price         NUMERIC     цена                  да        -        CHECK(price > 0)
image_path    TEXT        путь к изображению    нет       NULL     -


users
Поле         Тип SQLite  Назначение        NOT NULL  DEFAULT  Ограничения
user_id      INTEGER     идентификатор     да        -        PRIMARY KEY AUTOINCREMENT
last_name    TEXT        фамилия           да        -        -
first_name   TEXT        имя               да        -        -
middle_name  TEXT        отчество          нет       NULL     -
login        TEXT        логин             да        -        UNIQUE
role_id      INTEGER     ссылка на роль    да        -        FOREIGN KEY REFERENCES roles(role_id) ON DELETE RESTRICT


stock_items
Поле           Тип SQLite  Назначение              NOT NULL  DEFAULT  Ограничения
stock_item_id  INTEGER     идентификатор           да        -        PRIMARY KEY AUTOINCREMENT
product_id     INTEGER     ссылка на товар         да        -        FOREIGN KEY REFERENCES products(product_id) ON DELETE CASCADE
size_id        INTEGER     ссылка на размер        да        -        FOREIGN KEY REFERENCES sizes(size_id) ON DELETE RESTRICT
quantity       INTEGER     доступное количество    да        0        CHECK(quantity >= 0)


orders
Поле        Тип SQLite  Назначение                NOT NULL  DEFAULT        Ограничения
order_id    INTEGER     идентификатор             да        -              PRIMARY KEY AUTOINCREMENT
user_id     INTEGER     ссылка на пользователя    да        -              FOREIGN KEY REFERENCES users(user_id) ON DELETE RESTRICT
order_date  TEXT        дата заказа               да        CURRENT_DATE   -


order_items
Поле           Тип SQLite  Назначение                       NOT NULL  DEFAULT  Ограничения
order_item_id  INTEGER     идентификатор                    да        -        PRIMARY KEY AUTOINCREMENT
order_id       INTEGER     ссылка на заказ                  да        -        FOREIGN KEY REFERENCES orders(order_id) ON DELETE CASCADE
stock_item_id  INTEGER     ссылка на товарную позицию       да        -        FOREIGN KEY REFERENCES stock_items(stock_item_id) ON DELETE RESTRICT
quantity       INTEGER     количество товара в заказе       да        -        CHECK(quantity > 0)
price          NUMERIC     цена товарной позиции в заказе   да        -        CHECK(price > 0)

Ключи и ограничения

Первичные ключи

первичные ключи с AUTOINCREMENT

roles.role_id
sizes.size_id
products.product_id
users.user_id
stock_items.stock_item_id
orders.order_id
order_items.order_item_id

Внешние ключи

users.role_id ссылается на roles.role_id
stock_items.product_id ссылается на products.product_id
stock_items.size_id ссылается на sizes.size_id
orders.user_id ссылается на users.user_id
order_items.order_id ссылается на orders.order_id
order_items.stock_item_id ссылается на stock_items.stock_item_id

Стратегии удаления

ON DELETE RESTRICT для связей где удаление родителя запрещено пока есть зависимые записи
users.role_id
stock_items.size_id
orders.user_id
order_items.stock_item_id

ON DELETE CASCADE для связей где удаление родителя удаляет зависимые записи
stock_items.product_id
order_items.order_id

Ограничения CHECK

products.price > 0
stock_items.quantity >= 0
order_items.quantity > 0
order_items.price > 0

Ограничения UNIQUE

roles.role_name
sizes.size_value
users.login

Ограничения NOT NULL

Все поля кроме products.image_path и users.middle_name обязательны

Значения по умолчанию

stock_items.quantity DEFAULT 0
orders.order_date DEFAULT CURRENT_DATE

Порядок создания таблиц

Сначала справочники roles sizes

Потом независимые таблицы products users

Потом stock_items потому что ссылается на products и sizes

Потом orders потому что ссылается на users

Потом order_items потому что ссылается на orders и stock_items

Такой порядок нужен потому что внешние ключи ссылаются на уже созданные таблицы

Включение внешних ключей

В SQLite внешние ключи по умолчанию отключены

В функции get_connection выполняется команда PRAGMA foreign_keys = ON

Без неё ограничения FOREIGN KEY не работают

Служебная таблица sqlite_sequence

При использовании AUTOINCREMENT SQLite автоматически создаёт таблицу sqlite_sequence

Она хранит последние использованные значения счётчиков для каждой таблицы

Эта таблица появляется автоматически и не требует ручного создания