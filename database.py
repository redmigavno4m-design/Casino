import sqlite3
import time

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
            last_bonus INTEGER DEFAULT 0
        )
    """)
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
        'last_bonus': row[9]
    }


def update_balance(user_id, delta):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id))
    conn.commit()
    conn.close()


def record_game(user_id, bet, win):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if win > 0:
        cur.execute(
            "UPDATE users SET games=games+1, wins=wins+1, "
            "total_won=total_won+?, biggest_win=MAX(biggest_win,?) "
            "WHERE user_id=?",
            (win, win, user_id)
        )
    else:
        cur.execute(
            "UPDATE users SET games=games+1, total_lost=total_lost+? WHERE user_id=?",
            (bet, user_id)
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


def top_players(limit=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username, balance FROM users "
                "ORDER BY balance DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
