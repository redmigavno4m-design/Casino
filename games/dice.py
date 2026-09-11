# -*- coding: utf-8 -*-
"""🎲 Кости"""

import random
import time
from colors import C, clear, fmt, banner, ask_bet, wait_enter, show_win, show_lose, header
from config import DICE_HIGH_MULT, DICE_LOW_MULT, DICE_SIX_MULT, MIN_BET
from storage import save


def play(balance, stats):
    while True:
        clear()
        banner()
        header("🎲 КОСТИ", balance)
        print(f"  [1] ⬆️ Больше 3 — x{DICE_HIGH_MULT}")
        print(f"  [2] ⬇️ Меньше 4 — x{DICE_LOW_MULT}")
        print(f"  [3] 🎯 Ровно 6 — x{DICE_SIX_MULT}\n")

        try:
            choice = input(f"  {C.WHITE}Выбор (0=выход): {C.RESET}").strip()
            if choice == "0":
                return balance, stats
            choice = int(choice)
            if choice not in (1, 2, 3):
                continue
            bet = ask_bet(balance, MIN_BET)
            if bet == 0:
                continue
        except ValueError:
            continue

        balance -= bet
        stats["games"] += 1

        print(f"\n  {C.DIM}Бросок...{C.RESET}\n")
        for _ in range(8):
            v = random.randint(1, 6)
            print(f"\r   🎲 Кубик: {v}  ", end='', flush=True)
            time.sleep(0.1)
        value = random.randint(1, 6)
        print(f"\r   🎲 Кубик: {value}  ")
        time.sleep(0.3)

        win = 0
        if choice == 1 and value > 3:
            win = int(bet * DICE_HIGH_MULT)
        elif choice == 2 and value < 4:
            win = int(bet * DICE_LOW_MULT)
        elif choice == 3 and value == 6:
            win = int(bet * DICE_SIX_MULT)

        if win > 0:
            show_win(f"🎉 Выпало {value}!", win)
            balance += win
            stats["wins"] += 1
            stats["total_won"] += win
            if win > stats["biggest_win"]:
                stats["biggest_win"] = win
        else:
            show_lose(f"😢 Выпало {value}.", bet)
            stats["total_lost"] += bet

        print(f"\n  {C.YELLOW}Баланс: {C.GREEN}{fmt(balance)}{C.RESET}")
        save(balance, stats)
        wait_enter()

        if balance < MIN_BET:
            return balance, stats
