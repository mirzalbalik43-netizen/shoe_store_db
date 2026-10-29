Финальный набор ограничений

Таблица  Поле         Ограничение                                          Обоснование
products product_name CHECK (length(product_name) > 0)                      наименование не может быть пустым
products price        CHECK (price > 0 AND price < 1000000)                цена в разумных пределах
stock_items quantity  CHECK (quantity >= 0)                                 количество не может быть отрицательным
order_items quantity  CHECK (quantity > 0)                                  количество в заказе всегда больше нуля
order_items price     CHECK (price > 0)                                     цена позиции в заказе всегда больше нуля
users    login        CHECK (length(login) >= 3 AND length(login) <= 20)    логин разумной длины от 3 до 20
sizes    size_value   CHECK (size_value > 20 AND size_value < 50)           размеры обуви в разумном диапазоне
orders   order_date   CHECK (date(order_date) IS NOT NULL)                  дата в формате ISO 8601

Существующие ограничения из дня 2

NOT NULL на все обязательные поля
UNIQUE на roles.role_name sizes.size_value users.login
PRIMARY KEY AUTOINCREMENT на все id
FOREIGN KEY на все внешние ключи
DEFAULT на stock_items.quantity и orders.order_date

Обоснование новых ограничений

CHECK на product_name
Наименование товара не должно быть пустой строкой
Пустое наименование не имеет смысла

CHECK на price
Цена должна быть больше нуля
Верхняя граница миллион рублей отсекает ошибки ввода
Например лишний ноль при вводе

CHECK на quantity в stock_items
Количество не может быть отрицательным
Отрицательное количество на складе невозможно

CHECK на quantity в order_items
Количество в заказе всегда больше нуля
Заказ нулевого количества не имеет смысла

CHECK на price в order_items
Цена позиции в заказе должна быть больше нуля

CHECK на login
Логин от 3 до 20 символов
Слишком короткий логин небезопасен
Слишком длинный неудобен

CHECK на size_value
Размер обуви от 20 до 50
Реальные размеры обуви в этом диапазоне

CHECK на order_date
Дата должна соответствовать формату ISO 8601
Функция date() возвращает NULL если формат неправильный