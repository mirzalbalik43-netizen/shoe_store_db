# Отчет по практической работе №11: Триггеры и аудит

## 1. Назначение созданных триггеров

| Триггер | Событие | Время | Назначение |
| `trg_audit_price_update` | UPDATE | AFTER | Логирование изменения цен в `audit_log` |
| `trg_audit_order_delete` | DELETE | AFTER | Логирование удаления заказов |
| `trg_update_timestamp` | UPDATE | AFTER | Автоматическое обновление поля `updated_at` |
| `trg_reduce_stock_after_insert` | INSERT | AFTER | Автоматическое списание остатков со склада |
| `trg_protect_user_delete` | DELETE | BEFORE | Запрет удаления пользователя с активными заказами |
| `trg_check_stock_quantity` | INSERT | BEFORE | Запрет вставки отрицательного количества товара |

## 2. Разница между BEFORE и AFTER

BEFORE: Срабатывает до записи данных. Используется длявалидации (проверка `NEW.quantity_available < 0`) или отмены операции(через `RAISE(ABORT)`). Позволяет изменить значения `NEW` перед сохранением.
AFTER: Срабатывает после фиксации данных. Используется для каскадных изменений (списание остатков в другой таблице) и аудита(запись в `audit_log`), так как мы уверены, что основная операция прошла успешно.

## 3. Использование OLD и NEW

NEW: Использовался в `trg_reduce_stock_after_insert` (для получения `NEW.stock_item_id` и `NEW.quantity`) и в `trg_check_stock_quantity` (для проверки `NEW.quantity_available`).
OLD: Использовался в `trg_audit_price_update` (для сравнения `OLD.price` и `NEW.price`) и в `trg_protect_user_delete` (для поиска заказов по `OLD.user_id`).

