# -*- coding: utf-8 -*-
"""🎰 CASINO ROYALE — точка входа"""

import sys
from colors import C, clear, banner, fmt, wait_enter
from storage import load, save, reset, default_stats
from games import slots, roulette, dice, coin


def show_stats(balance, stats):
    clear()
    banner()
    wr = (stats["wins"] / stats["games"] * 100) if stats["games"] else 0
    print(f"{C.CYAN}{C.BOLD}═══ 📊 ПРОФИЛЬ ═══{C.RESET}\n")
    print(f"  💰 Баланс:         {C.GREEN}{fmt(balance)}{C.RESET}")
    print(f"  🎮 Игр сыграно:    {C.YELLOW}{stats['games']}{C.RESET}")
    print(f"  🏆 Побед:          {C.YELLOW}{stats['wins']}{C.RESET}")
    print(f"  📊 Винрейт:        {C.YELLOW}{wr:.1f}%{C.RESET}")
    print(f"  💎 Максимум:       {C.YELLOW}{fmt(stats['biggest_win'])}{C.RESET}")
    print(f"  🎰 Джекпотов:      {C.YELLOW}{stats['jackpots']}{C.RESET}")
    print(f"  📈 Всего выиграно: {C.GREEN}{fmt(stats['total_won'])}{C.RESET}")
    print(f"  📉 Всего слито:    {C.RED}{fmt(stats['total_lost'])}{C.RESET}")
    wait_enter()


def main_menu(balance, stats):
    while True:
        clear()
        banner()
        print(f"  {C.YELLOW}💰 Баланс: {C.GREEN}{C.BOLD}{fmt(balance)}{C.RESET}")
        print(f"  {C.DIM}🎮 Игр: {stats['games']} | 🏆 Побед: {stats['wins']}{C.RESET}\n")
        print(f"  {C.WHITE}{C.BOLD}ВЫБЕРИ ИГРУ:{C.RESET}\n")
        print(f"    {C.CYAN}[1]{C.RESET} 🎰 Слоты")
        print(f"    {C.CYAN}[2]{C.RESET} 🎡 Рулетка")
        print(f"    {C.CYAN}[3]{C.RESET} 🎲 Кости")
        print(f"    {C.CYAN}[4]{C.RESET} 🪙 Монетка")
        print(f"    {C.MAGENTA}[5]{C.RESET} 📊 Профиль")
        print(f"    {C.MAGENTA}[6]{C.RESET} 🗑️  Сбросить прогресс")
        print(f"    {C.RED}[0]{C.RESET} 🚪 Выход\n")

        try:
            choice = input(f"  {C.WHITE}➤ Твой выбор: {C.RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            choice = "0"

        if choice == "1":
            balance, stats = slots.play(balance, stats)
        elif choice == "2":
            balance, stats = roulette.play(balance, stats)
        elif choice == "3":
            balance, stats = dice.play(balance, stats)
        elif choice == "4":
            balance, stats = coin.play(balance, stats)
        elif choice == "5":
            show_stats(balance, stats)
        elif choice == "6":
            c = input(f"  {C.RED}Точно сбросить? (y/n): {C.RESET}").strip().lower()
            if c == "y":
                reset()
                balance = 1000
                stats = default_stats()
                save(balance, stats)
                print(f"  {C.GREEN}Прогресс сброшен!{C.RESET}")
                wait_enter()
        elif choice == "0":
            save(balance, stats)
            clear()
            print(f"\n  {C.YELLOW}👋 До встречи! Баланс: {C.GREEN}{fmt(balance)}{C.RESET}\n")
            sys.exit(0)


def main():
    balance, stats = load()
    try:
        main_menu(balance, stats)
    except KeyboardInterrupt:
        save(balance, stats)
        print(f"\n\n  {C.YELLOW}👋 Сохранено. Пока!{C.RESET}\n")


if __name__ == "__main__":
    main()
