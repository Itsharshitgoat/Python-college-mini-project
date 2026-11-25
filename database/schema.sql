-- EVENTRA SQLite schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name          TEXT NOT NULL,
    description         TEXT NOT NULL DEFAULT '',
    event_date          TEXT NOT NULL,
    start_time          TEXT NOT NULL DEFAULT '',
    end_time            TEXT NOT NULL DEFAULT '',
    venue               TEXT NOT NULL,
    capacity            INTEGER NOT NULL,
    registration_status TEXT NOT NULL DEFAULT 'DRAFT',
    checkin_status      TEXT NOT NULL DEFAULT 'DISABLED',
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS participants (
    participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name      TEXT NOT NULL,
    email          TEXT NOT NULL DEFAULT '',
    phone          TEXT NOT NULL,
    college        TEXT NOT NULL DEFAULT '',
    department     TEXT NOT NULL DEFAULT '',
    year           TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registrations (
    registration_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id       INTEGER NOT NULL,
    event_id             INTEGER NOT NULL,
    qr_token_hash        TEXT NOT NULL UNIQUE,
    registration_status  TEXT NOT NULL DEFAULT 'ACTIVE',
    registered_at        TEXT NOT NULL,
    ticket_path          TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (participant_id) REFERENCES participants(participant_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
    UNIQUE (participant_id, event_id)
);

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id INTEGER NOT NULL UNIQUE,
    operator_id     INTEGER,
    checked_in_at   TEXT NOT NULL,
    check_in_status TEXT NOT NULL DEFAULT 'PRESENT',
    FOREIGN KEY (registration_id) REFERENCES registrations(registration_id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS application_settings (
    setting_key   TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    event_id   INTEGER,
    action     TEXT NOT NULL,
    details    TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_reg_event ON registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_reg_participant ON registrations(participant_id);
CREATE INDEX IF NOT EXISTS idx_reg_hash ON registrations(qr_token_hash);
CREATE INDEX IF NOT EXISTS idx_att_reg ON attendance(registration_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
