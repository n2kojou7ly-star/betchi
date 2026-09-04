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
    related_request_id  INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES users(student_id)
);

CREATE TABLE items (
    item_id         TEXT PRIMARY KEY,
    category        TEXT NOT NULL,
    item_name       TEXT NOT NULL,
    required_point  INTEGER NOT NULL
);

CREATE TABLE exchanges (
    exchange_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL,
    item_id         TEXT NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (student_id) REFERENCES users(student_id),
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);

DROP TABLE IF EXISTS match_requests;
DROP TABLE IF EXISTS match_request_slots;
DROP TABLE IF EXISTS chat_rooms;
DROP TABLE IF EXISTS messages;

CREATE TABLE match_requests (
    request_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL,
    teacher_id      TEXT NOT NULL,
    subject_id      INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT '申請中',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    completed_by    TEXT,
    waiting_since   TEXT,
    completed_at    TEXT,
    FOREIGN KEY (student_id) REFERENCES users(student_id),
    FOREIGN KEY (teacher_id) REFERENCES users(student_id)
);

CREATE TABLE match_request_slots (
    request_id      INTEGER NOT NULL,
    slot_id         INTEGER NOT NULL,
    PRIMARY KEY (request_id, slot_id),
    FOREIGN KEY (request_id) REFERENCES match_requests(request_id),
    FOREIGN KEY (slot_id) REFERENCES availabilities(slot_id)
);

CREATE TABLE chat_rooms (
    room_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL,
    teacher_id      TEXT NOT NULL,
    UNIQUE (student_id, teacher_id),
    FOREIGN KEY (student_id) REFERENCES users(student_id),
    FOREIGN KEY (teacher_id) REFERENCES users(student_id)
);

CREATE TABLE messages (
    message_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id         INTEGER NOT NULL,
    sender_id       TEXT NOT NULL,
    kind            TEXT NOT NULL DEFAULT '文字',
    body            TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id),
    FOREIGN KEY (sender_id) REFERENCES users(student_id)
);