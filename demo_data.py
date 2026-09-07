"""
発表用のデモデータを投入するスクリプト。

使い方:
    sqlite3 betchi.db < schema.sql
    sqlite3 betchi.db < seed.sql
    python3 demo_data.py

先生4人（アイコン・フレーム・エフェクト・キャッチコピー・教科・トピック・
空き枠・レビュー・ポイント残高つき）と、生徒役のなおきを作る。
空き枠は実行日から3日分を自動生成するので、いつ実行しても当日の日付になる。
"""

import sqlite3
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = "betchi.db"
PASSWORD = "test1234"


def h(pw):
    return generate_password_hash(pw, method="pbkdf2")


# ==========================================================
# 登録するユーザー
# ==========================================================
# (学番, ニックネーム, アイコン, フレーム, エフェクト, キャッチコピー, プロフィール文)
TEACHERS = [
    ("K26001", "こうた", "icons/icon1.png", "icon-frame-a", "effect-a", "catchcopy-a",
     "数学の質問ならなんでも聞いてください。過去問の解説が得意です。"),
    ("K26002", "かとはる", "icons/icon2.png", "icon-frame-b", None, "catchcopy-c",
     "英語のリスニングとTOEIC対策をやっています。ゆっくり進めます。"),
    ("K26003", "りゅーと", "icons/icon3.png", "icon-frame-c", "effect-b", "catchcopy-b",
     "プログラミング全般。環境構築でつまずいてる人、まず声かけてください。"),
    ("K26004", "みなみ", "icons/icon4.png", None, "effect-c", None,
     "物理と化学。公式を丸暗記しない教え方を心がけています。"),
]

STUDENT = ("K26045", "なおき", "icons/icon5.png", "これから勉強します。")

# 教科ID: 1数学 2英語 3国語 4日本史 5物理 6化学 7プログラミング
TEACHING = {
    "K26001": [1],
    "K26002": [2],
    "K26003": [7, 1],
    "K26004": [5, 6],
}

# トピック名で指定（IDは自動で引く）
TOPICS = {
    "K26001": ["線形代数", "微分積分", "統計"],
    "K26002": ["リスニング", "TOEIC対策", "英文法"],
    "K26003": ["Web開発", "アルゴリズム", "情報数学"],
    "K26004": ["力学", "電磁気学", "理論化学"],
}

# 各先生が持つ空き枠の時限（実行日から3日分すべてに適用）
SLOTS = {
    "K26001": [1, 2, 3, 4],
    "K26002": [2, 3, 5],
    "K26003": [1, 3, 4, 5, 6],
    "K26004": [2, 4],
}

# (受け取る先生, 書いた人, ポイント, コメント)
REVIEWS = [
    ("K26001", "K26045", 30, "線形代数の固有値がずっと分からなかったんですが、図で説明してもらえて一気に理解できました。"),
    ("K26001", "K26002", 20, "説明が丁寧で、質問しやすい雰囲気でした。"),
    ("K26001", "K26003", 25, "過去問の解き方が参考になりました。またお願いします。"),
    ("K26002", "K26045", 20, "発音のコツを教えてもらえて助かりました。"),
    ("K26002", "K26004", 30, "TOEICのスコアが上がりました。ありがとうございます。"),
    ("K26003", "K26045", 40, "環境構築で2日詰まっていたのが30分で解決しました。"),
    ("K26003", "K26001", 20, "エラーの読み方から教えてもらえたのが良かったです。"),
    ("K26003", "K26002", 25, "初心者にも分かる説明でした。"),
    ("K26004", "K26045", 20, "公式の意味から教えてもらえて納得できました。"),
    ("K26004", "K26003", 30, "苦手だった電磁気が少し好きになりました。"),
]

# 先生に持たせる初期ポイント（アイテム交換のデモ用）
INITIAL_POINTS = {
    "K26001": 500,
    "K26002": 400,
    "K26003": 600,
    "K26004": 300,
    "K26045": 500,
}

# 先生が交換済みのアイテム（装備するために必要）
OWNED = {
    "K26001": ["icon-frame-a", "effect-a", "catchcopy-a"],
    "K26002": ["icon-frame-b", "catchcopy-c"],
    "K26003": ["icon-frame-c", "effect-b", "catchcopy-b"],
    "K26004": ["effect-c"],
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ---------- 既存のデモデータを消す ----------
    cur.execute("DELETE FROM reviews")
    cur.execute("DELETE FROM match_request_slots")
    cur.execute("DELETE FROM match_requests")
    cur.execute("DELETE FROM messages")
    cur.execute("DELETE FROM chat_rooms")
    cur.execute("DELETE FROM point_transactions")
    cur.execute("DELETE FROM exchanges")
    cur.execute("DELETE FROM availabilities")
    cur.execute("DELETE FROM teaching_topics")
    cur.execute("DELETE FROM teaching_subjects")
    cur.execute("DELETE FROM users")

    # ---------- ユーザー ----------
    for sid, nick, icon, frame, effect, catch, profile in TEACHERS:
        cur.execute("""
            INSERT INTO users
                (student_id, password_hash, nickname, icon, profile,
                 icon_frame_item_id, catchcopy_item_id, effect_item_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sid, h(PASSWORD), nick, icon, profile, frame, catch, effect))

    sid, nick, icon, profile = STUDENT
    cur.execute("""
        INSERT INTO users (student_id, password_hash, nickname, icon, profile)
        VALUES (?, ?, ?, ?, ?)
    """, (sid, h(PASSWORD), nick, icon, profile))

    # ---------- 教える教科 ----------
    for sid, subject_ids in TEACHING.items():
        for subject_id in subject_ids:
            cur.execute(
                "INSERT INTO teaching_subjects (student_id, subject_id) VALUES (?, ?)",
                (sid, subject_id))

    # ---------- 教えるトピック ----------
    for sid, names in TOPICS.items():
        for name in names:
            row = cur.execute(
                "SELECT topic_id FROM subject_topics WHERE topic_name = ?",
                (name,)).fetchone()
            if row:
                cur.execute(
                    "INSERT INTO teaching_topics (student_id, topic_id) VALUES (?, ?)",
                    (sid, row["topic_id"]))
            else:
                print(f"  ! トピックが見つかりません: {name}")

    # ---------- 空き枠（実行日から3日分） ----------
    today = date.today()
    days = [(today + timedelta(days=i)).isoformat() for i in range(3)]
    for sid, periods in SLOTS.items():
        for d in days:
            for p in periods:
                cur.execute("""
                    INSERT INTO availabilities (student_id, date, period, status)
                    VALUES (?, ?, ?, '空き')
                """, (sid, d, p))

    # ---------- 交換済みアイテム ----------
    for sid, items in OWNED.items():
        for item_id in items:
            cur.execute(
                "INSERT INTO exchanges (student_id, item_id, quantity) VALUES (?, ?, 1)",
                (sid, item_id))

    # ---------- ポイント残高 ----------
    for sid, amount in INITIAL_POINTS.items():
        cur.execute("""
            INSERT INTO point_transactions (student_id, amount, reason)
            VALUES (?, ?, '授業完了')
        """, (sid, amount))

    # ---------- レビュー ----------
    # reviews.request_id は UNIQUE かつ NOT NULL なので、
    # 表示専用のダミー申込を1件ずつ作ってから紐づける
    for i, (receiver, giver, point, comment) in enumerate(REVIEWS, start=1):
        cur.execute("""
            INSERT INTO match_requests
                (student_id, teacher_id, subject_id, status, completed_at)
            VALUES (?, ?, 1, '完了', datetime('now', 'localtime'))
        """, (giver, receiver))
        request_id = cur.lastrowid
        cur.execute("""
            INSERT INTO reviews (request_id, giver_id, receiver_id, point, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (request_id, giver, receiver, point, comment))
        cur.execute("""
            INSERT INTO point_transactions
                (student_id, amount, reason, related_request_id)
            VALUES (?, ?, 'レビュー', ?)
        """, (receiver, point, request_id))

    conn.commit()

    # ---------- 結果表示 ----------
    print("デモデータを投入しました。")
    print(f"空き枠の日付: {days[0]} 〜 {days[-1]}")
    print("パスワードは全員 test1234")
    print()
    rows = cur.execute("""
        SELECT u.student_id, u.nickname,
               COALESCE((SELECT SUM(amount) FROM point_transactions p
                         WHERE p.student_id = u.student_id), 0) AS balance,
               (SELECT COUNT(*) FROM availabilities a
                WHERE a.student_id = u.student_id) AS slots,
               (SELECT COUNT(*) FROM reviews v
                WHERE v.receiver_id = u.student_id) AS reviews
        FROM users u ORDER BY u.student_id
    """).fetchall()
    for r in rows:
        print(f"  {r['student_id']}  {r['nickname']:<8} "
              f"残高{r['balance']:>5}P  空き枠{r['slots']:>3}  レビュー{r['reviews']:>2}件")

    conn.close()


if __name__ == "__main__":
    main()