import sqlite3
import time
import json

DB = "casino.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 1000,
            games INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            biggest_win INTEGER DEFAULT 0,
            total_won INTEGER DEFAULT 0,
            total_lost INTEGER DEFAULT 0,
            last_bonus INTEGER DEFAULT 0,
            last_wheel INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            max_streak INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '',
            daily_quests TEXT DEFAULT '',
            quests_date TEXT DEFAULT ''
        )
    """)
    # На случай старых БД — добавляем недостающие колонки
    for col, default in [
        ("last_wheel", "0"), ("xp", "0"), ("streak", "0"),
        ("max_streak", "0"), ("achievements", "''"),
        ("daily_quests", "''"), ("quests_date", "''")
    ]:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} DEFAULT {default}")
        except Exception:
            pass
    conn.commit()
    conn.close()


def get_user(user_id, username=None, first_name=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
    conn.close()
    return {
        'user_id': row[0], 'username': row[1], 'first_name': row[2],
        'balance': row[3], 'games': row[4], 'wins': row[5],
        'biggest_win': row[6], 'total_won': row[7], 'total_lost': row[8],
        'last_bonus': row[9], 'last_wheel': row[10],
        'xp': row[11], 'streak': row[12], 'max_streak': row[13],
        'achievements': row[14].split(',') if row[14] else [],
        'daily_quests': json.loads(row[15]) if row[15] else {},
        'quests_date': row[16]
    }


def update_balance(user_id, delta):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id))
    conn.commit()
    conn.close()


def record_game(user_id, bet, win, xp_gain=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if win > 0:
        cur.execute(
            "UPDATE users SET games=games+1, wins=wins+1, xp=xp+?, "
            "streak=streak+1, max_streak=MAX(max_streak, streak+1), "
            "total_won=total_won+?, biggest_win=MAX(biggest_win,?) "
            "WHERE user_id=?",
            (xp_gain, win, win, user_id)
        )
    else:
        cur.execute(
            "UPDATE users SET games=games+1, xp=xp+?, streak=0, "
            "total_lost=total_lost+? WHERE user_id=?",
            (xp_gain // 2, bet, user_id)
        )
    conn.commit()
    conn.close()


def update_daily_bonus(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_bonus=? WHERE user_id=?",
                (int(time.time()), user_id))
    conn.commit()
    conn.close()


def update_wheel_time(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_wheel=? WHERE user_id=?",
                (int(time.time()), user_id))
    conn.commit()
    conn.close()


def unlock_achievement(user_id, ach_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT achievements FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row:
        current = row[0].split(',') if row[0] else []
        if ach_id not in current:
            current.append(ach_id)
            cur.execute("UPDATE users SET achievements=? WHERE user_id=?",
                        (','.join(current), user_id))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False


def set_quests(user_id, quests):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET daily_quests=?, quests_date=? WHERE user_id=?",
        (json.dumps(quests), time.strftime('%Y-%m-%d'), user_id)
    )
    conn.commit()
    conn.close()


def top_players(limit=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username, balance FROM users "
                "ORDER BY balance DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
