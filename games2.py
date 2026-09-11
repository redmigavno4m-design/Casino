import random
from config import (
    VSLOT_SYMBOLS, VSLOT_WEIGHTS, VSLOT_PAY3, VSLOT_PAY4, VSLOT_PAY5, VSLOT_DIVISOR,
    AMERICAN_RED, AMERICAN_GREEN_MULT, MINI_RED, MINI_ZERO_MULT,
    CRAPS_FIELD_WINS, CRAPS_FIELD_PAY, SICKBO_PAYOUTS, HILO_MULT,
    KENO_MAX, KENO_PAYOUTS, CRASH_HOUSE_EDGE, CRASH_MAX_MULT
)


def _wchoice(symbols, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for s, w in zip(symbols, weights):
        upto += w
        if r <= upto:
            return s
    return symbols[0]


def vslot_spin(bet):
    grid = [[_wchoice(VSLOT_SYMBOLS, VSLOT_WEIGHTS) for _ in range(3)] for _ in range(5)]
    line = [grid[c][1] for c in range(5)]
    first = line[0]
    count = 1
    for i in range(1, 5):
        if line[i] == first:
            count += 1
        else:
            break
    win = 0
    desc = "😢 Мимо..."
    if count >= 3:
        mult = VSLOT_PAY5[first] if count == 5 else (VSLOT_PAY4[first] if count == 4 else VSLOT_PAY3[first])
        win = int(bet * mult / VSLOT_DIVISOR)
        desc = f"🎉 {count}× {first}! x{mult}"
    scatters = sum(1 for c in range(5) for r in range(3) if grid[c][r] == '⭐')
    freespins = 0
    if scatters >= 3:
        freespins = 8 if scatters == 3 else 12 if scatters == 4 else 15
        desc += f"\n🎁 +{freespins} фриспинов!"
    return win, grid, freespins, desc


def american_roulette(bet, pick):
    result = random.choice(['0', '00'] + [str(i) for i in range(1, 37)])
    if result in ('0', '00'):
        color = "🟢 Зелёное"
        win = bet * AMERICAN_GREEN_MULT if pick == 'green' else 0
    else:
        n = int(result)
        is_red = n in AMERICAN_RED
        color = "🔴 Красное" if is_red else "⚫ Чёрное"
        win = bet * 2 if (pick == 'red' and is_red) or (pick == 'black' and not is_red) else 0
    return win, result, color


def mini_roulette(bet, pick):
    result = random.randint(0, 12)
    is_zero = result == 0
    is_red = result in MINI_RED
    if is_zero:
        color = "🟢 Зеро"
        win = bet * MINI_ZERO_MULT if pick == 'zero' else 0
    elif is_red:
        color = "🔴 Красное"
        win = bet * 2 if pick == 'red' else 0
    else:
        color = "⚫ Чёрное"
        win = bet * 2 if pick == 'black' else 0
    return win, result, color


def craps_check_pass(bet, phase, point, sum_val):
    if phase == 'comeout':
        if sum_val in (7, 11):
            return bet * 2, 'comeout', 0, "🎉 Natural! PASS выиграл!"
        elif sum_val in (2, 3, 12):
            return 0, 'comeout', 0, "😢 Craps! PASS проиграл."
        else:
            return 0, 'point', sum_val, f"🎯 Точка: {sum_val}"
    else:
        if sum_val == point:
            return bet * 2, 'comeout', 0, f"🎉 Точка {sum_val} выбита!"
        elif sum_val == 7:
            return 0, 'comeout', 0, "😢 Seven-out!"
        else:
            return 0, 'point', point, f"🎯 Точка {point}"


def sickbo_roll(bet, guess_sum):
    d1, d2, d3 = random.randint(1,6), random.randint(1,6), random.randint(1,6)
    total = d1 + d2 + d3
    if total == guess_sum:
        return int(bet * SICKBO_PAYOUTS.get(total, 1.0)), d1, d2, d3, total
    return 0, d1, d2, d3, total


def hilo_dice(bet, pick):
    value = random.randint(1, 6)
    win = 0
    if pick == 'high' and value > 3:
        win = int(bet * HILO_MULT)
    elif pick == 'low' and value < 4:
        win = int(bet * HILO_MULT)
    return win, value


def keno_play(bet, picks):
    drawn = random.sample(range(1, KENO_MAX + 1), 20)
    matches = len(set(picks) & set(drawn))
    mult = KENO_PAYOUTS.get((matches, len(picks)), 0)
    return int(bet * mult), drawn, matches


def crash_generate():
    r = random.random()
    if r < CRASH_HOUSE_EDGE:
        return 1.0
    return min(round((1 - CRASH_HOUSE_EDGE) / (1 - r), 2), CRASH_MAX_MULT)


SCRATCH_SYMBOLS = ['💎', '💰', '⭐', '🍒', '7️⃣', '💎']
SCRATCH_WEIGHTS = [30, 25, 20, 15, 7, 3]


def scratch_card(bet):
    grid = [[_wchoice(SCRATCH_SYMBOLS, SCRATCH_WEIGHTS) for _ in range(3)] for _ in range(3)]
    win = 0
    desc = "😢 Ничего..."
    for row in grid:
        if row[0] == row[1] == row[2]:
            m = _scratch_mult(row[0])
            if m > 0 and int(bet * m) > win:
                win, desc = int(bet * m), f"🎉 3× {row[0]} в ряд!"
    for col in range(3):
        if grid[0][col] == grid[1][col] == grid[2][col]:
            m = _scratch_mult(grid[0][col])
            if m > 0 and int(bet * m) > win:
                win, desc = int(bet * m), f"🎉 3× {grid[0][col]} в столбец!"
    if grid[0][0] == grid[1][1] == grid[2][2]:
        m = _scratch_mult(grid[0][0])
        if m > 0 and int(bet * m) > win:
            win, desc = int(bet * m), f"🎉 Диагональ!"
    if grid[0][2] == grid[1][1] == grid[2][0]:
        m = _scratch_mult(grid[0][2])
        if m > 0 and int(bet * m) > win:
            win, desc = int(bet * m), f"🎉 Диагональ!"
    return win, grid, desc


def _scratch_mult(s):
    return {'🍒':1.5, '⭐':3.0, '💰':5.0, '💎':20.0, '7️⃣':100.0}.get(s, 0)
