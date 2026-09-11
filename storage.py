# -*- coding: utf-8 -*-
"""Сохранение/загрузка прогресса"""

import json
from pathlib import Path


SAVE_PATH = Path.home() / ".casino_save.json"


def default_stats():
    return {
        "games": 0, "wins": 0, "biggest_win": 0,
        "total_won": 0, "total_lost": 0, "jackpots": 0
    }


def save(balance, stats):
    try:
        SAVE_PATH.write_text(json.dumps({"balance": balance, "stats": stats}))
    except Exception:
        pass


def load():
    if SAVE_PATH.exists():
        try:
            data = json.loads(SAVE_PATH.read_text())
            balance = data.get("balance", 1000)
            stats = data.get("stats", default_stats())
            for k, v in default_stats().items():
                stats.setdefault(k, v)
            return balance, stats
        except Exception:
            pass
    return 1000, default_stats()


def reset():
    if SAVE_PATH.exists():
        SAVE_PATH.unlink()
