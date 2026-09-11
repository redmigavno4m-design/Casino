import sqlite3
import time
import json

DB = "casino.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Основная таблица
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 1000,
            crystals INTEGER DEFAULT 0,
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
            quests_date TEXT DEFAULT '',
            language TEXT DEFAULT 'ru',
            referrer_id INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referral_earnings INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0
        )
    """)

    # Транзакции
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            currency TEXT,
            method TEXT,
            status TEXT,
            ext_id TEXT,
            created_at INTEGER
        )
    """)

    # Лотерея
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lottery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ticket_count INTEGER,
            draw_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lottery_draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jackpot INTEGER,
            winner_id INTEGER,
            drawn_at INTEGER
        )
    """)

    # Турниры
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_at INTEGER,
            end_at INTEGER,
            prize_pool INTEGER,
            finished INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tournament_players (
            tournament_id INTEGER,
            user_id INTEGER,
            profit INTEGER DEFAULT 0,
            PRIMARY KEY (tournament_id, user_id)
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
        'balance': row[3], 'crystals': row[4],
        'games': row[5], 'wins': row[6], 'biggest_win': row[7],
        'total_won': row[8], 'total_lost': row[9],
        'last_bonus': row[10], 'last_wheel': row[11],
        'xp': row[12], 'streak': row[13], 'max_streak': row[14],
        'achievements': row[15].split(',') if row[15] else [],
        'daily_quests': json.loads(row[16]) if row[16] else {},
        'quests_date': row[17],
        'language': row[18],
        'referrer_id': row[19],
        'referrals': row[20],
        'referral_earnings': row[21],
        'banned': row[22]
    }


def update_balance(user_id, delta):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id))
    conn.commit()
    conn.close()


def update_crystals(user_id, delta):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET crystals = crystals + ? WHERE user_id=?", (delta, user_id))
    conn.commit()
    conn.close()


def add_transaction(user_id, amount, currency, method, status='pending', ext_id=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (user_id, amount, currency, method, status, ext_id, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, amount, currency, method, status, ext_id, int(time.time()))
    )
    tx_id = cur.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def complete_transaction(tx_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE transactions SET status='completed' WHERE id=?", (tx_id,))
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

    # Реферальный процент (с проигрыша)
    if win == 0:
        cur.execute("SELECT referrer_id FROM users WHERE user_id=?", (user_id,))
        r = cur.fetchone()
        if r and r[0]:
            from config import REFERRAL_PERCENT
            bonus = int(bet * REFERRAL_PERCENT)
            if bonus > 0:
                cur.execute("UPDATE users SET balance=balance+?, referral_earnings=referral_earnings+? WHERE user_id=?",
                            (bonus, bonus, r[0]))

    conn.commit()
    conn.close()


def set_language(user_id, lang):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()


def register_referral(new_user_id, referrer_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT referrer_id FROM users WHERE user_id=?", (new_user_id,))
    row = cur.fetchone()
    if row and row[0] == 0 and referrer_id != new_user_id:
        cur.execute("UPDATE users SET referrer_id=? WHERE user_id=?", (referrer_id, new_user_id))
        cur.execute("UPDATE users SET referrals=referrals+1 WHERE user_id=?", (referrer_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


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
                "WHERE banned=0 ORDER BY balance DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ============================================================
# АДМИН
# ============================================================
def admin_stats():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(balance), SUM(crystals) FROM users WHERE banned=0")
    users_count, total_balance, total_crystals = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM transactions WHERE status='completed'")
    tx_count = cur.fetchone()[0]

    cur.execute("SELECT SUM(amount) FROM transactions WHERE status='completed' AND currency='RUB'")
    total_rub = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(amount) FROM transactions WHERE status='completed' AND currency='STARS'")
    total_stars = cur.fetchone()[0] or 0

    conn.close()
    return {
        'users': users_count or 0,
        'total_balance': total_balance or 0,
        'total_crystals': total_crystals or 0,
        'transactions': tx_count,
        'revenue_rub': total_rub,
        'revenue_stars': total_stars
    }


def admin_give(user_id, amount):
    update_balance(user_id, amount)


def admin_ban(user_id, banned=1):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET banned=? WHERE user_id=?", (banned, user_id))
    conn.commit()
    conn.close()


def admin_broadcast_users():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE banned=0")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def make_promo(code, amount, uses=100):
    """Создать промокод (сохраняется в таблицу промокодов)"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            amount INTEGER,
            uses INTEGER,
            used INTEGER DEFAULT 0
        )
    """)
    cur.execute("INSERT OR REPLACE INTO promos (code, amount, uses) VALUES (?, ?, ?)",
                (code.upper(), amount, uses))
    conn.commit()
    conn.close()


def use_promo(user_id, code):
    """Активировать промокод. Возвращает сумму или None"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promo_uses (
            user_id INTEGER,
            code TEXT,
            PRIMARY KEY (user_id, code)
        )
    """)
    cur.execute("SELECT amount, uses, used FROM promos WHERE code=?", (code.upper(),))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    amount, uses, used = row
    if used >= uses:
        conn.close()
        return None
    cur.execute("SELECT 1 FROM promo_uses WHERE user_id=? AND code=?", (user_id, code.upper()))
    if cur.fetchone():
        conn.close()
        return None
    cur.execute("INSERT INTO promo_uses (user_id, code) VALUES (?, ?)", (user_id, code.upper()))
    cur.execute("UPDATE promos SET used=used+1 WHERE code=?", (code.upper(),))
    update_balance(user_id, amount)
    conn.commit()
    conn.close()
    return amount
