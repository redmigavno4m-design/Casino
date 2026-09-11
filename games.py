import random

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


def play_coin(bet, pick):
    r = random.choice(['eagle', 'tail'])
    win = int(bet * 1.9) if pick == r else 0
    return win, r
