-- ДОПОЛНИТЕЛЬНОЕ ЗАДАНИЕ: выполнять только по желанию!
-- Главная учебная база содержит СТРОГО 7 таблиц, поэтому audit_log не включён
-- в основной schema.sql. Этот файл добавляет восьмую таблицу в расширенной схеме.
CREATE TABLE IF NOT EXISTS audit_log (
    audit_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation_name TEXT NOT NULL CHECK (operation_name IN ('INSERT','UPDATE','DELETE')),
    record_id INTEGER,
    user_login TEXT,
    changed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
