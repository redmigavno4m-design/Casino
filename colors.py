# -*- coding: utf-8 -*-
"""ANSI-цвета и утилиты вывода"""

import os


class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_MAGENTA = '\033[45m'


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def fmt(n):
    return f"{int(n):,}".replace(",", " ") + "$"


def wait_enter():
    input(f"\n  {C.DIM}Enter — продолжить...{C.RESET}")


def ask_bet(balance, minimum=50):
    while True:
        try:
            raw = input(f"  {C.WHITE}💰 Ставка (Enter=100, 0=выход): {C.RESET}").strip()
            bet = 100 if raw == "" else int(raw)
            if bet == 0:
                return 0
            if bet < minimum:
                print(f"  {C.RED}Минимум: {minimum}${C.RESET}")
                continue
            if bet > balance:
                print(f"  {C.RED}Недостаточно! Баланс: {fmt(balance)}{C.RESET}")
                continue
            return bet
        except ValueError:
            print(f"  {C.RED}Введи число!{C.RESET}")


def header(title, balance):
    print(f"{C.CYAN}{C.BOLD}═══ {title} ═══{C.RESET}\n")
    print(f"  {C.YELLOW}Баланс: {C.GREEN}{fmt(balance)}{C.RESET}\n")


def show_win(text, amount):
    print(f"\n  {C.BG_GREEN}{C.WHITE}{C.BOLD} {text} +{fmt(amount)} {C.RESET}")


def show_lose(text, amount):
    print(f"\n  {C.RED}{text} -{fmt(amount)}{C.RESET}")


def banner():
    clear()
    print(f"{C.YELLOW}{C.BOLD}")
    print("=" * 50)
    print("         🎰  CASINO ROYALE  🎰")
    print("=" * 50)
    print(f"{C.RESET}")
