import sqlite3
from werkzeug.security import generate_password_hash

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

def get_all_items():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM items WHERE required_point > 0 ORDER BY item_id"
    ).fetchall()
    conn.close()
    return rows

def get_item(item_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM items WHERE item_id = ?", (item_id,)).fetchone()
    conn.close()
    return row

def get_owned_item_ids(student_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT item_id FROM exchanges WHERE student_id = ?", (student_id,)
    ).fetchall()
    conn.close()
    return [r["item_id"] for r in rows]

def exchange_item(student_id, item_id, required_point):
    conn = get_conn()
    conn.execute(
        "INSERT INTO exchanges (student_id, item_id, quantity) VALUES (?, ?, 1)",
        (student_id, item_id)
    )
    conn.execute(
        "INSERT INTO point_transactions (student_id, amount, reason) VALUES (?, ?, 'アイテム交換')",
        (student_id, -required_point)
    )
    conn.commit()
    conn.close()

def search_teachers(subject_id, date, exclude_student_id, topic_id=None):
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            u.student_id,
            u.nickname,
            u.icon,
            u.profile,
            u.icon_frame_item_id,
            u.effect_item_id,
            (SELECT item_name FROM items WHERE item_id = u.catchcopy_item_id) AS catchcopy,
            (SELECT GROUP_CONCAT(st.topic_name, '・')
             FROM teaching_topics tt
             JOIN subject_topics st ON st.topic_id = tt.topic_id
             WHERE tt.student_id = u.student_id AND st.subject_id = ?) AS topic_text,
            (SELECT COUNT(*) FROM teaching_topics tt2
             WHERE tt2.student_id = u.student_id AND tt2.topic_id = ?) AS topic_match,
            (SELECT COALESCE(SUM(point), 0) FROM reviews v
             WHERE v.receiver_id = u.student_id) AS review_point,
            (SELECT COUNT(*) FROM reviews v2
             WHERE v2.receiver_id = u.student_id) AS review_count,
            (SELECT GROUP_CONCAT(v3.comment, '|||') FROM (
                SELECT comment FROM reviews
                WHERE receiver_id = u.student_id AND comment IS NOT NULL AND comment != ''
                ORDER BY review_id DESC LIMIT 2
             ) v3) AS recent_comments,
            COUNT(a.slot_id) AS slot_count,
            COALESCE((SELECT SUM(amount) FROM point_transactions p
                      WHERE p.student_id = u.student_id), 0) AS balance
        FROM users u
        JOIN teaching_subjects ts ON ts.student_id = u.student_id
        JOIN availabilities a ON a.student_id = u.student_id
        WHERE ts.subject_id = ?
          AND a.date = ?
          AND a.status = '空き'
          AND u.student_id != ?
        GROUP BY u.student_id
        ORDER BY topic_match DESC, slot_count DESC
    """, (subject_id, topic_id or 0, subject_id, date, exclude_student_id)).fetchall()
    conn.close()
    return rows

def get_open_slots(teacher_id, date):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM availabilities WHERE student_id = ? AND date = ? AND status = '空き' ORDER BY period",
        (teacher_id, date)
    ).fetchall()
    conn.close()
    return rows

def create_request(student_id, teacher_id, subject_id, slot_ids):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO match_requests (student_id, teacher_id, subject_id) VALUES (?, ?, ?)",
        (student_id, teacher_id, subject_id)
    )
    request_id = cur.lastrowid
    for slot_id in slot_ids:
        conn.execute(
            "INSERT INTO match_request_slots (request_id, slot_id) VALUES (?, ?)",
            (request_id, slot_id)
        )
    conn.commit()
    conn.close()
    return request_id

def get_requests_for_teacher(teacher_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, u.nickname, s.subject_name,
               (SELECT GROUP_CONCAT(a.date || ' ' || a.period || '時限', ', ')
                FROM match_request_slots ms
                JOIN availabilities a ON a.slot_id = ms.slot_id
                WHERE ms.request_id = r.request_id) AS slot_text
        FROM match_requests r
        JOIN users u ON u.student_id = r.student_id
        JOIN subjects s ON s.subject_id = r.subject_id
        WHERE r.teacher_id = ? AND r.status = '申請中'
        ORDER BY r.created_at
    """, (teacher_id,)).fetchall()
    conn.close()
    return rows

def get_requests_for_student(student_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, u.nickname, s.subject_name,
               (SELECT GROUP_CONCAT(a.date || ' ' || a.period || '時限', ', ')
                FROM match_request_slots ms
                JOIN availabilities a ON a.slot_id = ms.slot_id
                WHERE ms.request_id = r.request_id) AS slot_text
        FROM match_requests r
        JOIN users u ON u.student_id = r.teacher_id
        JOIN subjects s ON s.subject_id = r.subject_id
        WHERE r.student_id = ? AND r.status = '申請中'
        ORDER BY r.created_at DESC
    """, (student_id,)).fetchall()
    conn.close()
    return rows

def get_slots_by_ids(slot_ids):
    conn = get_conn()
    placeholders = ",".join("?" * len(slot_ids))
    rows = conn.execute(
        f"SELECT * FROM availabilities WHERE slot_id IN ({placeholders})",
        slot_ids
    ).fetchall()
    conn.close()
    return rows

def approve_request(request_id, teacher_id):
    conn = get_conn()
    req = conn.execute(
        "SELECT * FROM match_requests WHERE request_id = ? AND teacher_id = ? AND status = '申請中'",
        (request_id, teacher_id)
    ).fetchone()
    if req is None:
        conn.close()
        return
    slot_rows = conn.execute(
        "SELECT slot_id FROM match_request_slots WHERE request_id = ?", (request_id,)
    ).fetchall()
    slot_ids = [r["slot_id"] for r in slot_rows]
    placeholders = ",".join("?" * len(slot_ids))
    conn.execute(
        f"UPDATE availabilities SET status = '予約済' WHERE slot_id IN ({placeholders})",
        slot_ids
    )
    conn.execute(
        f"""UPDATE match_requests SET status = '却下'
            WHERE status = '申請中' AND request_id != ?
              AND request_id IN (
                SELECT request_id FROM match_request_slots WHERE slot_id IN ({placeholders})
              )""",
        [request_id] + slot_ids
    )
    conn.execute(
        "UPDATE match_requests SET status = '承認' WHERE request_id = ?", (request_id,)
    )
    conn.execute(
        "INSERT OR IGNORE INTO chat_rooms (student_id, teacher_id) VALUES (?, ?)",
        (req["student_id"], teacher_id)
    )
    conn.execute("""
        UPDATE match_requests SET status = '却下'
        WHERE status = '申請中'
          AND student_id = ?
          AND request_id != ?
          AND request_id IN (
            SELECT ms.request_id
            FROM match_request_slots ms
            JOIN availabilities a ON a.slot_id = ms.slot_id
            WHERE (a.date, a.period) IN (
                SELECT a2.date, a2.period
                FROM match_request_slots ms2
                JOIN availabilities a2 ON a2.slot_id = ms2.slot_id
                WHERE ms2.request_id = ?
            )
          )
    """, (req["student_id"], request_id, request_id))
    conn.commit()
    conn.close()

def reject_request(request_id, teacher_id):
    conn = get_conn()
    conn.execute(
        "UPDATE match_requests SET status = '却下' WHERE request_id = ? AND teacher_id = ? AND status = '申請中'",
        (request_id, teacher_id)
    )
    conn.commit()
    conn.close()

def get_chat_rooms(student_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.room_id,
               u.student_id AS partner_id,
               u.nickname AS partner_name,
               u.icon AS partner_icon,
               u.icon_frame_item_id AS partner_frame,
               u.effect_item_id AS partner_effect
        FROM chat_rooms r
        JOIN users u ON u.student_id =
            CASE WHEN r.student_id = ? THEN r.teacher_id ELSE r.student_id END
        WHERE r.student_id = ? OR r.teacher_id = ?
    """, (student_id, student_id, student_id)).fetchall()
    conn.close()
    return rows

def get_room(room_id, student_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT r.*,
               CASE WHEN r.student_id = ? THEN r.teacher_id ELSE r.student_id END AS partner_id
        FROM chat_rooms r
        WHERE r.room_id = ? AND (r.student_id = ? OR r.teacher_id = ?)
    """, (student_id, room_id, student_id, student_id)).fetchone()
    conn.close()
    return row

def get_messages(room_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.*, u.nickname, u.icon
        FROM messages m
        JOIN users u ON u.student_id = m.sender_id
        WHERE m.room_id = ?
        ORDER BY m.message_id
    """, (room_id,)).fetchall()
    conn.close()
    return rows

def add_message(room_id, sender_id, body):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (room_id, sender_id, body) VALUES (?, ?, ?)",
        (room_id, sender_id, body)
    )
    conn.commit()
    conn.close()

POINT_PER_SLOT = 20
AUTO_COMPLETE_MINUTES = 1440  # デモ用に短くするならここを変える

def get_pending_completions(student_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, u.nickname, s.subject_name,
               (SELECT COUNT(*) FROM match_request_slots ms WHERE ms.request_id = r.request_id) AS slot_count
        FROM match_requests r
        JOIN users u ON u.student_id =
            CASE WHEN r.student_id = ? THEN r.teacher_id ELSE r.student_id END
        JOIN subjects s ON s.subject_id = r.subject_id
        WHERE (r.student_id = ? OR r.teacher_id = ?)
          AND r.status IN ('承認', '完了待ち')
        ORDER BY r.created_at
    """, (student_id, student_id, student_id)).fetchall()
    conn.close()
    return rows

def press_complete(request_id, student_id):
    conn = get_conn()
    req = conn.execute("""
        SELECT * FROM match_requests
        WHERE request_id = ? AND (student_id = ? OR teacher_id = ?)
    """, (request_id, student_id, student_id)).fetchone()
    if req is None:
        conn.close()
        return
    if req["status"] == "承認":
        conn.execute("""
            UPDATE match_requests
            SET status = '完了待ち', completed_by = ?,
                waiting_since = datetime('now', 'localtime')
            WHERE request_id = ?
        """, (student_id, request_id))
        conn.commit()
    elif req["status"] == "完了待ち" and req["completed_by"] != student_id:
        _finish(conn, req)
    conn.close()

def _finish(conn, req):
    already = conn.execute(
        "SELECT 1 FROM point_transactions WHERE related_request_id = ? AND reason = '授業完了'",
        (req["request_id"],)
    ).fetchone()
    if already:
        return
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM match_request_slots WHERE request_id = ?",
        (req["request_id"],)
    ).fetchone()["c"]
    conn.execute("""
        UPDATE match_requests SET status = '完了',
            completed_at = datetime('now', 'localtime')
        WHERE request_id = ?
    """, (req["request_id"],))
    conn.execute("""
        INSERT INTO point_transactions (student_id, amount, reason, related_request_id)
        VALUES (?, ?, '授業完了', ?)
    """, (req["teacher_id"], count * POINT_PER_SLOT, req["request_id"]))
    conn.commit()

def auto_complete_expired():
    conn = get_conn()
    rows = conn.execute(f"""
        SELECT * FROM match_requests
        WHERE status = '完了待ち'
          AND datetime(waiting_since, '+{AUTO_COMPLETE_MINUTES} minutes') <= datetime('now', 'localtime')
    """).fetchall()
    for req in rows:
        _finish(conn, req)
    conn.close()

def get_busy_periods(student_id, date):
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.period, u.nickname, s.subject_name, r.status
        FROM match_requests r
        JOIN match_request_slots ms ON ms.request_id = r.request_id
        JOIN availabilities a ON a.slot_id = ms.slot_id
        JOIN users u ON u.student_id = r.teacher_id
        JOIN subjects s ON s.subject_id = r.subject_id
        WHERE r.student_id = ? AND a.date = ?
          AND r.status IN ('申請中', '承認', '完了待ち')
        ORDER BY a.period
    """, (student_id, date)).fetchall()
    conn.close()
    return rows

def get_dev_stats():
    conn = get_conn()
    stats = {}
    for name in ("users", "subjects", "subject_topics", "teaching_subjects",
                 "teaching_topics", "availabilities", "match_requests",
                 "chat_rooms", "messages", "point_transactions", "exchanges"):
        stats[name] = conn.execute(f"SELECT COUNT(*) AS c FROM {name}").fetchone()["c"]
    users = conn.execute("""
        SELECT u.student_id, u.nickname,
               COALESCE((SELECT SUM(amount) FROM point_transactions p
                         WHERE p.student_id = u.student_id), 0) AS balance,
               (SELECT COUNT(*) FROM teaching_subjects t
                WHERE t.student_id = u.student_id) AS subject_count,
               (SELECT COUNT(*) FROM availabilities a
                WHERE a.student_id = u.student_id AND a.status = '空き') AS open_slots
        FROM users u ORDER BY u.student_id
    """).fetchall()
    requests = conn.execute("""
        SELECT r.request_id, r.status, su.nickname AS student_name,
               tu.nickname AS teacher_name, s.subject_name
        FROM match_requests r
        JOIN users su ON su.student_id = r.student_id
        JOIN users tu ON tu.student_id = r.teacher_id
        JOIN subjects s ON s.subject_id = r.subject_id
        ORDER BY r.request_id DESC
    """).fetchall()
    conn.close()
    return stats, users, requests

def dev_reset_matching():
    conn = get_conn()
    conn.execute("DELETE FROM match_request_slots")
    conn.execute("DELETE FROM match_requests")
    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM chat_rooms")
    conn.execute("UPDATE availabilities SET status = '空き'")
    conn.commit()
    conn.close()

def dev_add_points(student_id, amount):
    conn = get_conn()
    conn.execute(
        "INSERT INTO point_transactions (student_id, amount, reason) VALUES (?, ?, 'テスト')",
        (student_id, amount)
    )
    conn.commit()
    conn.close()

def create_user(student_id, password, nickname, profile, icon):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (student_id, password_hash, nickname, profile, icon) VALUES (?, ?, ?, ?, ?)",
            (student_id, generate_password_hash(password, method="pbkdf2"),
             nickname, profile, icon)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def get_messages_after(room_id, after_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.*, u.nickname
        FROM messages m
        JOIN users u ON u.student_id = m.sender_id
        WHERE m.room_id = ? AND m.message_id > ?
        ORDER BY m.message_id
    """, (room_id, after_id)).fetchall()
    conn.close()
    return rows

def get_owned_items_by_category(student_id, category):
    conn = get_conn()
    rows = conn.execute("""
        SELECT items.item_id, items.item_name
        FROM exchanges
        JOIN items ON exchanges.item_id = items.item_id
        WHERE exchanges.student_id = ? AND items.category = ?
    """, (student_id, category)).fetchall()
    conn.close()
    return rows

def set_equipped_items(student_id, icon_frame_item_id, catchcopy_item_id, effect_item_id):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET icon_frame_item_id = ?, catchcopy_item_id = ?, effect_item_id = ? WHERE student_id = ?",
        (icon_frame_item_id or None, catchcopy_item_id or None,
         effect_item_id or None, student_id)
    )
    conn.commit()
    conn.close()

def get_topics_by_subject():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM subject_topics ORDER BY subject_id, topic_id"
    ).fetchall()
    conn.close()
    result = {}
    for r in rows:
        result.setdefault(r["subject_id"], []).append(
            {"topic_id": r["topic_id"], "topic_name": r["topic_name"]}
        )
    return result

def get_teaching_topic_ids(student_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT topic_id FROM teaching_topics WHERE student_id = ?", (student_id,)
    ).fetchall()
    conn.close()
    return [r["topic_id"] for r in rows]

def set_teaching_topics(student_id, topic_ids):
    conn = get_conn()
    conn.execute("DELETE FROM teaching_topics WHERE student_id = ?", (student_id,))
    for tid in topic_ids:
        conn.execute(
            "INSERT INTO teaching_topics (student_id, topic_id) VALUES (?, ?)",
            (student_id, tid)
        )
    conn.commit()
    conn.close()

def get_usable_stamps(student_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT i.item_id, i.item_name
        FROM items i
        WHERE i.category = 'スタンプ'
          AND (i.required_point = 0
               OR i.item_id IN (SELECT item_id FROM exchanges WHERE student_id = ?))
        ORDER BY i.required_point, i.item_id
    """, (student_id,)).fetchall()
    conn.close()
    return rows

def add_stamp_message(room_id, sender_id, item_id):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (room_id, sender_id, kind, body) VALUES (?, ?, 'スタンプ', ?)",
        (room_id, sender_id, item_id)
    )
    conn.commit()
    conn.close()

def get_upcoming_lessons(student_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.request_id, r.status,
               CASE WHEN r.student_id = ? THEN r.teacher_id ELSE r.student_id END AS partner_id,
               u.nickname AS partner_name,
               s.subject_name,
               (SELECT GROUP_CONCAT(a.date || ' ' || a.period || '時限', ', ')
                FROM match_request_slots ms
                JOIN availabilities a ON a.slot_id = ms.slot_id
                WHERE ms.request_id = r.request_id) AS slot_text,
               (SELECT room_id FROM chat_rooms c
                WHERE (c.student_id = r.student_id AND c.teacher_id = r.teacher_id)) AS room_id
        FROM match_requests r
        JOIN users u ON u.student_id =
            CASE WHEN r.student_id = ? THEN r.teacher_id ELSE r.student_id END
        JOIN subjects s ON s.subject_id = r.subject_id
        WHERE (r.student_id = ? OR r.teacher_id = ?)
          AND r.status IN ('承認', '完了待ち')
        ORDER BY slot_text
    """, (student_id, student_id, student_id, student_id)).fetchall()
    conn.close()
    return rows

WEEKLY_REVIEW_LIMIT = 100

def get_reviewable(student_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.request_id, u.nickname, s.subject_name, r.teacher_id
        FROM match_requests r
        JOIN users u ON u.student_id = r.teacher_id
        JOIN subjects s ON s.subject_id = r.subject_id
        WHERE r.student_id = ? AND r.status = '完了'
          AND NOT EXISTS (SELECT 1 FROM reviews v WHERE v.request_id = r.request_id)
        ORDER BY r.completed_at DESC
    """, (student_id,)).fetchall()
    conn.close()
    return rows

def get_weekly_review_used(student_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT COALESCE(SUM(point), 0) AS used FROM reviews
        WHERE giver_id = ?
          AND date(created_at) >= date('now', 'localtime', 'weekday 0', '-6 days')
    """, (student_id,)).fetchone()
    conn.close()
    return row["used"]

def add_review(request_id, giver_id, point, comment):
    conn = get_conn()
    req = conn.execute(
        "SELECT * FROM match_requests WHERE request_id = ? AND student_id = ? AND status = '完了'",
        (request_id, giver_id)
    ).fetchone()
    if req is None:
        conn.close()
        return False
    try:
        conn.execute(
            "INSERT INTO reviews (request_id, giver_id, receiver_id, point, comment) VALUES (?, ?, ?, ?, ?)",
            (request_id, giver_id, req["teacher_id"], point, comment)
        )
        if point > 0:
            conn.execute(
                "INSERT INTO point_transactions (student_id, amount, reason, related_request_id) VALUES (?, ?, 'レビュー', ?)",
                (req["teacher_id"], point, request_id)
            )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def get_reviews_for(student_id, limit=3):
    conn = get_conn()
    rows = conn.execute("""
        SELECT v.point, v.comment, v.created_at, u.nickname
        FROM reviews v
        JOIN users u ON u.student_id = v.giver_id
        WHERE v.receiver_id = ? AND v.comment IS NOT NULL AND v.comment != ''
        ORDER BY v.review_id DESC LIMIT ?
    """, (student_id, limit)).fetchall()
    conn.close()
    return rows