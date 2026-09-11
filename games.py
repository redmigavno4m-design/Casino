import random


# ============================================================
# СЛОТЫ
# ============================================================
SLOT_SYMBOLS = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣']
SLOT_WEIGHTS = [25, 25, 20, 15, 8, 5, 2]
PAYOUTS = {'7️⃣': 40, '💎': 20, '⭐': 12, '🍇': 8, '🍊': 5, '🍋': 4, '🍒': 3}


def wchoice():
    total = sum(SLOT_WEIGHTS)
    r = random.uniform(0, total)
    upto = 0
    for s, w in zip(SLOT_SYMBOLS, SLOT_WEIGHTS):
        upto += w
        if r <= upto:
            return s
    return SLOT_SYMBOLS[0]


def play_slots(bet):
    reels = [wchoice() for _ in range(3)]
    a, b, c = reels
    if a == b == c:
        return bet * PAYOUTS[a], reels, f"🎉 Джекпот x{PAYOUTS[a]}!"
    elif a == b or b == c or a == c:
        return int(bet * 1.7), reels, "✨ Два совпадения!"
    return 0, reels, "😢 Мимо..."


# ============================================================
# РУЛЕТКА
# ============================================================
RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


def play_roulette(bet, pick):
    n = random.randint(0, 36)
    is_red = n in RED
    is_zero = n == 0
    win = 0
    if pick == 'red' and is_red:
        win = bet * 2
    elif pick == 'black' and not is_red and not is_zero:
        win = bet * 2
    elif pick == 'zero' and is_zero:
        win = bet * 36
    color = '🟢 Зеро' if is_zero else ('🔴 Красное' if is_red else '⚫ Чёрное')
    return win, n, color


# ============================================================
# КОСТИ
# ============================================================
def play_dice(bet, pick):
    v = random.randint(1, 6)
    win = 0
    if pick == 'high' and v > 3:
        win = int(bet * 1.9)
    elif pick == 'low' and v < 4:
        win = int(bet * 1.9)
    elif pick == 'six' and v == 6:
        win = int(bet * 4.5)
    return win, v


# ============================================================
# МОНЕТКА
# ============================================================
def play_coin(bet, pick):
    r = random.choice(['eagle', 'tail'])
    win = int(bet * 1.9) if pick == r else 0
    return win, r


# ============================================================
# 🃏 БЛЭКДЖЕК
# ============================================================
SUITS = [('♠', False), ('♥', True), ('♦', True), ('♣', False)]
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


def new_deck():
    deck = [{'rank': r, 'suit': s, 'red': red} for s, red in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def hand_value(hand):
    total = 0
    aces = 0
    for c in hand:
        if c['rank'] == 'A':
            aces += 1
            total += 11
        elif c['rank'] in ('J', 'Q', 'K'):
            total += 10
        else:
            total += int(c['rank'])
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def card_str(c):
    return f"{c['rank']}{c['suit']}"


def hand_str(h):
    return " ".join(card_str(c) for c in h)


# ============================================================
# 💣 МИНЫ
# ============================================================
def mines_new_game(grid_size=5, mines_count=3):
    """Создаёт сетку с минами. Возвращает set с индексами мин."""
    total = grid_size * grid_size
    positions = random.sample(range(total), mines_count)
    return set(positions)


def mines_multiplier(opened, mines_count, grid_size=5):
    """Множитель за открытые клетки."""
    total = grid_size * grid_size
    safe = total - mines_count
    if opened == 0:
        return 1.0
    # Простая формула: множитель растёт экспоненциально
    mult = 1.0
    for i in range(opened):
        remaining_safe = safe - i
        remaining_total = total - i
        mult *= remaining_total / remaining_safe
    return round(mult * 0.9, 2)  # 0.9 = house edge


# ============================================================
# 🎡 КОЛЕСО ФОРТУНЫ
# ============================================================
def spin_wheel(prizes):
    """Возвращает индекс и приз."""
    idx = random.randint(0, len(prizes) - 1)
    return idx, prizes[idx]


# ============================================================
# 🏆 ДОСТИЖЕНИЯ
# ============================================================
ACHIEVEMENTS = {
    'first_win': ('🥇', 'Первая победа', 'Выиграй в первый раз'),
    'streak3': ('🔥', 'Серия x3', 'Выиграй 3 раза подряд'),
    'streak5': ('⚡', 'Серия x5', 'Выиграй 5 раз подряд'),
    'streak10': ('💫', 'Серия x10', 'Выиграй 10 раз подряд'),
    'bigwin': ('💎', 'Большой куш', 'Выиграй 1000$ за раз'),
    'megawin': ('👑', 'Мега-куш', 'Выиграй 5000$ за раз'),
    'rich': ('💰', 'Миллионер', 'Накопи 10000$'),
    'games50': ('🎮', 'Заядлый игрок', 'Сыграй 50 игр'),
    'games200': ('🕹', 'Ветеран', 'Сыграй 200 игр'),
    'bj_win': ('🃏', 'Блэкджек-мастер', 'Выиграй в блэкджек'),
    'mines_win': ('💣', 'Сапёр', 'Выиграй в мины'),
}


def check_achievements(u):
    """Возвращает список новых достижений."""
    unlocked = []
    checks = {
        'first_win': u['total_won'] > 0,
        'streak3': u['max_streak'] >= 3,
        'streak5': u['max_streak'] >= 5,
        'streak10': u['max_streak'] >= 10,
        'bigwin': u['biggest_win'] >= 1000,
        'megawin': u['biggest_win'] >= 5000,
        'rich': u['balance'] >= 10000,
        'games50': u['games'] >= 50,
        'games200': u['games'] >= 200,
    }
    for aid, condition in checks.items():
        if condition and aid not in u['achievements']:
            unlocked.append(aid)
    return unlocked


# ============================================================
# 📊 УРОВНИ
# ============================================================
LEVELS = [
    (0, "🥉 Новичок", 0),
    (100, "🥈 Игрок", 100),
    (500, "🥇 Опытный", 300),
    (1500, "💎 Профи", 500),
    (5000, "👑 Мастер", 1000),
    (15000, "🏆 Легенда", 5000),
    (50000, "🌟 Король", 10000),
]


def get_level(xp):
    """Возвращает (level_index, name, xp_to_next_level, next_name)."""
    for i in range(len(LEVELS) - 1, -1, -1):
        if xp >= LEVELS[i][0]:
            current = LEVELS[i]
            if i + 1 < len(LEVELS):
                next_lvl = LEVELS[i + 1]
                return i, current[1], next_lvl[0] - xp, next_lvl[1]
            return i, current[1], 0, None
    return 0, LEVELS[0][1], LEVELS[1][0], LEVELS[1][1]


# ============================================================
# 📅 ЕЖЕДНЕВНЫЕ КВЕСТЫ
# ============================================================
QUEST_TEMPLATES = [
    {'id': 'play5', 'text': 'Сыграй 5 игр', 'target': 5, 'reward': 100},
    {'id': 'win3', 'text': 'Выиграй 3 раза', 'target': 3, 'reward': 150},
    {'id': 'slots3', 'text': 'Сыграй в слоты 3 раза', 'target': 3, 'reward': 100},
    {'id': 'bet500', 'text': 'Поставь 500$ всего', 'target': 500, 'reward': 200},
    {'id': 'win100', 'text': 'Выиграй 100$ суммарно', 'target': 100, 'reward': 100},
]


def generate_quests():
    """Генерирует 3 случайных квеста."""
    import time
    selected = random.sample(QUEST_TEMPLATES, 3)
    return {
        q['id']: {'text': q['text'], 'target': q['target'],
                  'reward': q['reward'], 'progress': 0, 'done': False}
        for q in selected
    }
