DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS teaching_subjects;

CREATE TABLE users (
    student_id     TEXT PRIMARY KEY,
    password_hash  TEXT NOT NULL,
    nickname       TEXT NOT NULL,
    icon           TEXT,
    profile        TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE subjects (
    subject_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name   TEXT NOT NULL UNIQUE
);

CREATE TABLE teaching_subjects (
    student_id     TEXT NOT NULL,
    subject_id     INTEGER NOT NULL,
    PRIMARY KEY (student_id, subject_id),
    FOREIGN KEY (student_id) REFERENCES users(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

DROP TABLE IF EXISTS availabilities;

CREATE TABLE availabilities (
    slot_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT NOT NULL,
    date         TEXT NOT NULL,
    period       INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT '空き',
    UNIQUE (student_id, date, period),
    FOREIGN KEY (student_id) REFERENCES users(student_id)
);

DROP TABLE IF EXISTS point_transactions;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS exchanges;

CREATE TABLE point_transactions (
    transaction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL,
    amount          INTEGER NOT NULL,
    reason          TEXT NOT NULL,
    request_id      INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES users(student_id)
);

CREATE TABLE items (
    item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name       TEXT NOT NULL,
    required_point  INTEGER NOT NULL
);

CREATE TABLE exchanges (
    exchange_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL,
    item_id         INTEGER NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES users(student_id),
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);