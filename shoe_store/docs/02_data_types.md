Таблица roles
Поле	   Тип SQLite  Назначение	  NOT  NULL	 DEFAULT	Ограничения
role_id	   INTEGER	   идентификатор  да	-	 PRIMARY KEY AUTOINCREMENT
role_name  TEXT	       название роли  да	-	 UNIQUE


Таблица users
Поле	     Тип SQLite  Назначение	    NOT NULL      DEFAULT  Ограничения
user_id	     INTEGER	 идентификатор    да	      -	       PRIMARY KEY AUTOINCREMENT
last_name	 TEXT	     фамилия	      да	      -	       -
first_name	 TEXT	     имя	          да	      -	       -
middle_name  TEXT	     отчество	      нет	      NULL	   -
login	     TEXT	     логин	          да	      -	       UNIQUE
role_id	     INTEGER	 ссылка на роль	  да	      -	       FOREIGN KEY REFERENCES roles(role_id)    ON DELETE RESTRICT


Таблица products
Поле          Тип SQLite  Назначение            NOT NULL  DEFAULT  Ограничения
product_id    INTEGER     идентификатор         да        -        PRIMARY KEY AUTOINCREMENT
product_name  TEXT        наименование          да        -        -
category      TEXT        категория             да        -        -
manufacturer  TEXT        производитель         да        -        -
price         NUMERIC     цена                  да        -        CHECK(price > 0)
image_path    TEXT        путь к изображению    нет       NULL     -


Таблица sizes
Поле        Тип SQLite  Назначение          NOT NULL  DEFAULT  Ограничения
size_id     INTEGER     идентификатор       да        -        PRIMARY KEY AUTOINCREMENT
size_value  REAL        значение размера    да        -        UNIQUE


Таблица stock_items
Поле           Тип SQLite  Назначение              NOT NULL  DEFAULT  Ограничения
stock_item_id  INTEGER     идентификатор           да        -        PRIMARY KEY AUTOINCREMENT
product_id     INTEGER     ссылка на товар         да        -        FOREIGN KEY REFERENCES products(product_id) ON DELETE CASCADE
size_id        INTEGER     ссылка на размер        да        -        FOREIGN KEY REFERENCES sizes(size_id) ON DELETE RESTRICT
quantity       INTEGER     доступное количество    да        0        CHECK(quantity >= 0)


Таблица orders
Поле        Тип SQLite  Назначение                NOT NULL  DEFAULT        Ограничения
order_id    INTEGER     идентификатор             да        -              PRIMARY KEY AUTOINCREMENT
user_id     INTEGER     ссылка на пользователя    да        -              FOREIGN KEY REFERENCES users(user_id) ON DELETE RESTRICT
order_date  TEXT        дата заказа               да        CURRENT_DATE   -


Таблица order_items
Поле           Тип SQLite  Назначение                       NOT NULL  DEFAULT  Ограничения
order_item_id  INTEGER     идентификатор                    да        -        PRIMARY KEY AUTOINCREMENT
order_id       INTEGER     ссылка на заказ                  да        -        FOREIGN KEY REFERENCES orders(order_id) ON DELETE CASCADE
stock_item_id  INTEGER     ссылка на товарную позицию       да        -        FOREIGN KEY REFERENCES stock_items(stock_item_id) ON DELETE RESTRICT
quantity       INTEGER     количество товара в заказе       да        -        CHECK(quantity > 0)
price          NUMERIC     цена товарной позиции в заказе   да        -        CHECK(price > 0)