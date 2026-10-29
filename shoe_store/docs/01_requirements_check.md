ПРОВЕРКА НА СООТВЕТСТВИЕ ТРЕБОВАНИЯМ ДЕМОЭКЗАМЕНА

ПРОВЕРКА ФУНКЦИОНАЛЬНЫХ ТРЕБОВАНИЙ
Требование 1: в каталоге должно храниться актуальное количество товарных позиций.

Таблица: stock_items
Поле: quantity_available
Операция: SELECT и UPDATE

Тут хранится, сколько товара доступно для заказа по каждой комбинации модели и размера. При заказе количество уменьшается.

Требование 2: для каждой модели должно сохраняться изображение.

Таблица: products
Поле: image_path
Операция: SELECT

Тут хранится путь к файлу с картинкой товара.

Требование 3: пользователь может выбрать одну или несколько пар обуви по модели и размеру.

Таблицы: products, sizes, stock_items, order_items
Поля: product_id, size_id, stock_item_id, quantity
Операция: SELECT и INSERT

Пользователь выбирает модель и размер. Это создаёт запись в order_items с указанием товарной позиции и количества.

Требование 4: просмотр списка заказов с датой и ФИО клиента. Управление заказами.

Таблицы: orders, users
Поля: order_date, last_name, first_name, middle_name
Операция: SELECT и UPDATE и DELETE

Дата берётся из orders. ФИО - из users через внешний ключ user_id. Управление заказами делается через UPDATE и DELETE.

Требование 5: вход в систему по логину без пароля.

Таблица: users
Поле: login
Операция: SELECT

Логин должен быть уникальным. Пароль не хранится.

ПРОВЕРКА РОЛЕЙ ПОЛЬЗОВАТЕЛЕЙ

Неавторизованный пользователь
Что может: смотреть каталог без фильтрации, сортировки и поиска.

Какие таблицы нужны: products, stock_items, sizes
Какие поля: product_id, name, image_path, price, quantity_available
Операция: только SELECT

Роль в базе не хранится, потому что пользователь ещё не вошёл.


Авторизованный пользователь
Что может: смотреть каталог с фильтрацией, сортировкой и поиском. Оформлять заказы. Добавлять и удалять позиции. Менять количество.

Какие таблицы нужны: products, stock_items, sizes, orders, order_items
Какие поля: все поля товара, quantity, price_at_order
Операция: SELECT, INSERT, UPDATE, DELETE

В таблице users есть поле role_id, которое ссылается на роль. У роли «авторизованный пользователь» свои права.


Менеджер
Что может: всё, что авторизованный пользователь. Плюс просмотр заказов, состава заказа, добавление и удаление заказов.

Какие таблицы нужны: orders, order_items, users
Какие поля: order_id, order_date, user_id, quantity, price_at_order
Операция: SELECT, INSERT, UPDATE, DELETE

Менеджер может работать со всеми заказами.


Администратор
Что может: всё, что менеджер. Плюс редактирование заказа.

Какие таблицы нужны: orders, order_items
Какие поля: все поля заказа и состава заказа
Операция: SELECT, INSERT, UPDATE, DELETE

Администратор может менять заказ. Для этого в orders и order_items должны быть поля, которые можно обновлять. Например, order_date в orders и quantity в order_items.


ТАБЛИЦА СООТВЕТСТВИЯ
Требование	                            Таблица	                             Поле	                                  Операция
Хранить количество товарных позиций	   stock_items	                   quantity_available	                       SELECT, UPDATE
Хранить изображение модели	           products	                       image_path	                                   SELECT
Выбор модели и размера	               products, sizes, stock_items    product_id, size_id, stock_item_id	           SELECT
Добавление пары обуви в заказ	       order_items	                   order_id, stock_item_id, quantity	           INSERT
Изменение количества в заказе	       order_items	                   quantity	                                       UPDATE
Удаление позиции из заказа	           order_items	                   order_item_id	                               DELETE
Просмотр списка заказов	               orders	                       order_id, order_date, user_id	               SELECT
Показать ФИО клиента в заказе	       users	                       last_name, first_name, middle_name	           SELECT
Управление заказами	                   orders		                   order_date, user_id                   INSERT, UPDATEDELETE, DELETE
Редактирование заказа	               orders, order_items	           order_date, quantity, price_at_order	           UPDATE
Вход по логину      	               users	                       login                                           SELECT
Разделение по ролям     	           roles, users	                   role_id	                                       SELECT
Фильтрация каталога	                   products	                       category, subcategory, producer	               SELECT
Сортировка каталога	                   products	                       price, name, producer	                       SELECT
Поиск по каталогу	                   products	                       name, producer	                               SELECT


Проверка по ролям
Роль	                       Что нужно в базе	                                        Есть в схеме
Неавторизованный	     SELECT по products и stock_items	                            Да
Авторизованный	         SELECT, INSERT, UPDATE, DELETE по orders и order_items	        Да
Менеджер	             То же плюс работа со всеми заказами	                        Да
Администратор	         То же плюс UPDATE по orders и order_items	                    Да
Все роли покрыты.

Вывод
Схема покрывает все пять функциональных требований.

Все четыре роли могут работать с нужными им таблицами.

В таблице users есть role_id, который связывает пользователя с ролью. По роли определяется, что пользователю можно, а что нельзя.

Поле login уникальное. Это нужно для входа без пароля. Если логин не уникальный, система не поймёт, кто вошёл.