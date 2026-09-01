import sqlite3

DB_PATH = "betchi.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_user_by_id(student_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE student_id = ?", (student_id,)
    ).fetchone()
    conn.close()
    return row

def get_all_subjects():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM subjects ORDER BY subject_id").fetchall()
    conn.close()
    return rows

def get_teaching_subject_ids(student_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT subject_id FROM teaching_subjects WHERE student_id = ?", (student_id,)
    ).fetchall()
    conn.close()
    return [r["subject_id"] for r in rows]