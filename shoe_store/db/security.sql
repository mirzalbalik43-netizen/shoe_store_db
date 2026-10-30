-- УП.11 №13. Идемпотентная часть DDL. Колонка users.password_hash
-- добавляется только при отсутствии через src/db_apply_security.py.
CREATE TABLE IF NOT EXISTS login_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('успех', 'отказ')),
    login_time TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_login_audit_time ON login_audit(login_time);
CREATE INDEX IF NOT EXISTS idx_login_audit_login ON login_audit(login);
