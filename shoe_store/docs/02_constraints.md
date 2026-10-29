Таблица roles
Поле       NOT NULL  UNIQUE  CHECK  DEFAULT
role_id    да        да      -      -
role_name  да        да      -      -


Таблица users
Поле         NOT NULL  UNIQUE  CHECK  DEFAULT
user_id      да        да      -      -
last_name    да        нет     -      -
first_name   да        нет     -      -
middle_name  нет       нет     -      NULL
login        да        да      -      -
role_id      да        нет     -      -

Таблица products
Поле          NOT NULL  UNIQUE  CHECK        DEFAULT
product_id    да        да      -            -
product_name  да        нет     -            -
category      да        нет     -            -
manufacturer  да        нет     -            -
price         да        нет     price > 0    -
image_path    нет       нет     -            NULL


Таблица sizes
Поле        NOT NULL  UNIQUE  CHECK  DEFAULT
size_id     да        да      -      -
size_value  да        да      -      -


Таблица stock_items
Поле           NOT NULL  UNIQUE  CHECK           DEFAULT
stock_item_id  да        да      -               -
product_id     да        нет     -               -
size_id        да        нет     -               -
quantity       да        нет     quantity >= 0   0


Таблица orders
Поле        NOT NULL  UNIQUE  CHECK  DEFAULT
order_id    да        да      -      -
user_id     да        нет     -      -
order_date  да        нет     -      CURRENT_DATE


Таблица order_items
Поле           NOT NULL  UNIQUE  CHECK          DEFAULT
order_item_id  да        да      -              -
order_id       да        нет     -              -
stock_item_id  да        нет     -              -
quantity       да        нет     quantity > 0   -
price          да        нет     price > 0      -