# -*- coding: utf-8 -*-
"""🎰 Слоты"""

import random
import time
from colors import C, clear, fmt, banner, ask_bet, wait_enter, show_win, show_lose, header
from config import (
    SLOT_SYMBOLS, SLOT_WEIGHTS, SLOT_PAYOUTS,
    SLOT_TWO_MATCH_MULT, MIN_BET
)
from storage import save


def _spin():
    total = sum(SLOT_WEIGHTS)
    r = random.uniform(0, total)
    upto = 0
    for s, w in zip(SLOT_SYMBOLS, SLOT_WEIGHTS):
        upto += w
        if r <= upto:
            return s
    return SLOT_SYMBOLS[0]


def _animate(final):
    for _ in range(10):
        row = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        print(f"\r   [ {row[0]} | {row[1]} | {row[2]} ]", end='', flush=True)
        time.sleep(0.1)
    print(f"\r   [ {final[0]} | {final[1]} | {final[2]} ]")


def play(balance, stats):
    while True:
        clear()
        banner()
        header("🎰 СЛОТЫ", balance)
        print("  7x40  💎x20  ⭐x12  🍇x8  🍊x5  🍋x4  🍒x3")
        print(f"  2 совпадения — x{SLOT_TWO_MATCH_MULT}\n")

        bet = ask_bet(balance, MIN_BET)
        if bet == 0:
            return balance, stats

        balance -= bet
        stats["games"] += 1

        print(f"\n  {C.DIM}Барабаны крутятся...{C.RESET}\n")
        final = [_spin() for _ in range(3)]
        _animate(final)
        time.sleep(0.5)

        a, b, c = final
        win = 0

        if a == b == c:
            mult = SLOT_PAYOUTS[a]
            win = int(bet * mult)
            show_win(f"🎉 ДЖЕКПОТ x{mult}!", win)
            stats["jackpots"] += 1
        elif a == b or b == c or a == c:
            win = int(bet * SLOT_TWO_MATCH_MULT)
            show_win("✨ Два совпадения!", win)
        else:
            show_lose("😢 Мимо...", bet)

        if win > 0:
            balance += win
            stats["wins"] += 1
            stats["total_won"] += win
            if win > stats["biggest_win"]:
                stats["biggest_win"] = win
        else:
            stats["total_lost"] += bet

        print(f"\n  {C.YELLOW}Баланс: {C.GREEN}{fmt(balance)}{C.RESET}")
        save(balance, stats)
        wait_enter()

        if balance < MIN_BET:
            return balance, stats
