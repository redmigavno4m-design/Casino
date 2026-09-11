import sqlite3
import time
from database import DB
from config import TOURNAMENT_DURATION, TOURNAMENT_RAKE


def get_referral_link(bot_username, user_id):
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


def referral_stats(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT referrals, referral_earnings FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return (row[0] or 0, row[1] or 0) if row else (0, 0)


def get_active_tournament():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    now = int(time.time())
    cur.execute("SELECT id, start_at, end_at, prize_pool FROM tournaments WHERE finished=0 ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if not row or row[2] < now:
        cur.execute("INSERT INTO tournaments (start_at, end_at, prize_pool) VALUES (?, ?, 0)",
                    (now, now + TOURNAMENT_DURATION))
        tid = cur.lastrowid
        conn.commit()
        conn.close()
        return {'id': tid, 'start_at': now, 'end_at': now + TOURNAMENT_DURATION, 'prize_pool': 0}
    conn.close()
    return {'id': row[0], 'start_at': row[1], 'end_at': row[2], 'prize_pool': row[3]}


def join_tournament(user_id, tid, entry):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO tournament_players (tournament_id, user_id, profit) VALUES (?, ?, 0)",
                (tid, user_id))
    cur.execute("UPDATE tournaments SET prize_pool = prize_pool + ? WHERE id=?",
                (int(entry * (1 - TOURNAMENT_RAKE)), tid))
    conn.commit()
    conn.close()


def is_in_tournament(user_id, tid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM tournament_players WHERE tournament_id=? AND user_id=?", (tid, user_id))
    ok = cur.fetchone() is not None
    conn.close()
    return ok


def tournament_top(tid, limit=10):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""SELECT u.first_name, u.username, tp.profit
                   FROM tournament_players tp JOIN users u ON u.user_id = tp.user_id
                   WHERE tp.tournament_id = ? ORDER BY tp.profit DESC LIMIT ?""", (tid, limit))
    rows = cur.fetchall()
    conn.close()
    return rows
