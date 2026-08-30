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