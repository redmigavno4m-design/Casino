# -*- coding: utf-8 -*-
"""🎡 Рулетка"""

import random
import time
from colors import C, clear, fmt, banner, ask_bet, wait_enter, show_win, show_lose, header
from config import RED_NUMBERS, MIN_BET
from storage import save


def _animate(result):
    for _ in range(15):
        n = random.randint(0, 36)
        print(f"\r   🎡  {n:2d}  ", end='', flush=True)
        time.sleep(0.08)
    print(f"\r   🎡  {result:2d}  ")


def play(balance, stats):
    while True:
        clear()
        banner()
        header("🎡 РУЛЕТКА", balance)
        print("  [1] 🔴 Красное x2")
        print("  [2] ⚫ Чёрное x2")
        print("  [3] 🟢 Зеро x36\n")

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

        print(f"\n  {C.DIM}Колесо крутится...{C.RESET}\n")
        result = random.randint(0, 36)
        _animate(result)
        time.sleep(0.5)

        is_red = result in RED_NUMBERS
        is_zero = result == 0
        color = '🟢 Зеро' if is_zero else ('🔴 Красное' if is_red else '⚫ Чёрное')

        win = 0
        if choice == 1 and is_red:
            win = bet * 2
        elif choice == 2 and not is_red and not is_zero:
            win = bet * 2
        elif choice == 3 and is_zero:
            win = bet * 36

        if win > 0:
            show_win(f"🎉 {color} {result}!", win)
            balance += win
            stats["wins"] += 1
            stats["total_won"] += win
            if win > stats["biggest_win"]:
                stats["biggest_win"] = win
        else:
            show_lose(f"😢 {color} {result}.", bet)
            stats["total_lost"] += bet

        print(f"\n  {C.YELLOW}Баланс: {C.GREEN}{fmt(balance)}{C.RESET}")
        save(balance, stats)
        wait_enter()

        if balance < MIN_BET:
            return balance, stats
