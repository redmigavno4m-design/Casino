import sqlite3
import time
from database import DB


def get_house_stats():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT SUM(total_won), SUM(total_lost), COUNT(*) FROM users")
    row = cur.fetchone()
    conn.close()
    won = row[0] or 0
    lost = row[1] or 0
    total = won + lost
    return {
        'total_won': won, 'total_lost': lost,
        'players': row[2] or 0,
        'house_edge': (lost - won) / total * 100 if total > 0 else 0,
        'profit': lost - won
    }


def get_top_by_profit(limit=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""SELECT first_name, username, total_lost, total_won,
                   (total_lost - total_won) FROM users WHERE total_lost > 0
                   ORDER BY (total_lost - total_won) DESC LIMIT ?""", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_inactive_users(days=3):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cutoff = int(time.time()) - days * 86400
    cur.execute("""SELECT user_id, first_name FROM users
                   WHERE banned=0 AND (last_bonus < ? OR last_bonus = 0) LIMIT 500""", (cutoff,))
    rows = cur.fetchall()
    conn.close()
    return rows
