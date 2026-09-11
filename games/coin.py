# -*- coding: utf-8 -*-
"""🪙 Монетка"""

import random
import time
from colors import C, clear, fmt, banner, ask_bet, wait_enter, show_win, show_lose, header
from config import COIN_MULT, MIN_BET
from storage import save


def play(balance, stats):
    while True:
        clear()
        banner()
        header("🪙 МОНЕТКА", balance)
        print(f"  [1] 🦅 Орёл x{COIN_MULT}")
        print(f"  [2] 🪙 Решка x{COIN_MULT}\n")

        try:
            choice = input(f"  {C.WHITE}Выбор (0=выход): {C.RESET}").strip()
            if choice == "0":
                return balance, stats
            choice = int(choice)
            if choice not in (1, 2):
                continue
            bet = ask_bet(balance, MIN_BET)
            if bet == 0:
                continue
        except ValueError:
            continue

        balance -= bet
        stats["games"] += 1

        print(f"\n  {C.DIM}Монетка в воздухе...{C.RESET}\n")
        for i in range(12):
            s = '🦅' if i % 2 == 0 else '🪙'
            print(f"\r   Монета: {s}  ", end='', flush=True)
            time.sleep(0.1)

        result = random.choice(['eagle', 'tail'])
        symbol = '🦅' if result == 'eagle' else '🪙'
        print(f"\r   Монета: {symbol}  ")
        time.sleep(0.3)

        pick = 'eagle' if choice == 1 else 'tail'
        result_str = '🦅 Орёл' if result == 'eagle' else '🪙 Решка'

        if pick == result:
            win = int(bet * COIN_MULT)
            show_win(f"🎉 {result_str}!", win)
            balance += win
            stats["wins"] += 1
            stats["total_won"] += win
            if win > stats["biggest_win"]:
                stats["biggest_win"] = win
        else:
            show_lose(f"😢 {result_str}.", bet)
            stats["total_lost"] += bet

        print(f"\n  {C.YELLOW}Баланс: {C.GREEN}{fmt(balance)}{C.RESET}")
        save(balance, stats)
        wait_enter()

        if balance < MIN_BET:
            return balance, stats
