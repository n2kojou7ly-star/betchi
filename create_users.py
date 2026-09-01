import sqlite3
from werkzeug.security import generate_password_hash

users = [
    ("K26045", "test1234", "なおき"),
    ("K26001", "test1234", "こうた"),
    ("K26002", "test1234", "かとはる"),
]

conn = sqlite3.connect("betchi.db")
for student_id, password, nickname in users:
    conn.execute(
        "INSERT INTO users (student_id, password_hash, nickname) VALUES (?, ?, ?)",
        (student_id, generate_password_hash(password, method="pbkdf2"), nickname)
    )
conn.commit()
conn.close()
print("登録しました")