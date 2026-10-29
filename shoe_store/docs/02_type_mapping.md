Сопоставление с типами демоэкзамена
Тип SQLite        Тип из демоэкзамена  Комментарий
INTEGER           INTEGER / INT        совпадает напрямую
TEXT              VARCHAR / NVARCHAR   строка произвольной длины
TEXT (ISO 8601)   DATE                 дата хранится как строка
REAL              NUMERIC / DECIMAL    число с плавающей точкой
NUMERIC           NUMERIC / DECIMAL    число с фиксированной точностью


Разбор 12 полей из задания 1.5 демоэкзамена
Поле  Назначение                          Тип SQLite        Тип из демоэкзамена
А     Идентификатор пользователя          INTEGER           INTEGER / INT
Б     Фамилия пользователя                TEXT              VARCHAR / NVARCHAR
В     Логин пользователя                  TEXT              VARCHAR / NVARCHAR
Г     Дата заказа                         TEXT (ISO 8601)   DATE
Д     Наименование товара                 TEXT              VARCHAR / NVARCHAR
Е     Путь к изображению товара           TEXT              VARCHAR / NVARCHAR
Ж     Размер обуви                        REAL              NUMERIC / DECIMAL
З     Доступное количество позиции        INTEGER           INTEGER / INT
И     Цена товара                         NUMERIC           NUMERIC / DECIMAL
К     Количество товара в заказе          INTEGER           INTEGER / INT
Л     Цена товарной позиции в заказе      NUMERIC           NUMERIC / DECIMAL
М     Идентификатор заказа                INTEGER           INTEGER / INT
