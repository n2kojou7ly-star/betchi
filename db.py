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

def add_availability(student_id, date, period):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO availabilities (student_id, date, period) VALUES (?, ?, ?)",
            (student_id, date, period)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def delete_availability(slot_id, student_id):
    conn = get_conn()
    conn.execute(
        "DELETE FROM availabilities WHERE slot_id = ? AND student_id = ?",
        (slot_id, student_id)
    )
    conn.commit()
    conn.close()

def get_availabilities(student_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM availabilities WHERE student_id = ? ORDER BY date, period",
        (student_id,)
    ).fetchall()
    conn.close()
    return rows

def get_point_balance(student_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS balance FROM point_transactions WHERE student_id = ?",
        (student_id,)
    ).fetchone()
    conn.close()
    return row["balance"]

def update_profile(student_id, nickname, profile, icon):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET nickname = ?, profile = ?, icon = ? WHERE student_id = ?",
        (nickname, profile, icon, student_id)
    )
    conn.commit()
    conn.close()

def set_teaching_subjects(student_id, subject_ids):
    conn = get_conn()
    conn.execute("DELETE FROM teaching_subjects WHERE student_id = ?", (student_id,))
    for sid in subject_ids:
        conn.execute(
            "INSERT INTO teaching_subjects (student_id, subject_id) VALUES (?, ?)",
            (student_id, sid)
        )
    conn.commit()
    conn.close()