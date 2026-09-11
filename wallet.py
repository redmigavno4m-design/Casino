from config import CRYSTAL_TO_MONEY, MONEY_TO_CRYSTAL
from database import get_user, update_crystals, update_balance, add_transaction


def buy_crystals(user_id, amount, method, ext_id=None):
    update_crystals(user_id, amount)
    add_transaction(user_id, amount, method.upper(), method, 'completed', ext_id)


def exchange_crystals(user_id, crystal_amount):
    """Кристаллы → игровые $"""
    if crystal_amount < 1:
        return False, 0
    u = get_user(user_id)
    if u['crystals'] < crystal_amount:
        return False, 0
    money = crystal_amount * CRYSTAL_TO_MONEY
    update_crystals(user_id, -crystal_amount)
    update_balance(user_id, money)
    add_transaction(user_id, -crystal_amount, 'CRYSTAL', 'exchange', 'completed')
    return True, money


def money_to_crystals(user_id, money_amount):
    """
    Игровые $ → кристаллы (обратный обмен, курс ХУЖЕ для игрока)
    Защита от минуса!
    """
    if money_amount < MONEY_TO_CRYSTAL:
        return False, 0, f"Минимум {MONEY_TO_CRYSTAL}$"
    u = get_user(user_id)
    if u['balance'] < money_amount:
        return False, 0, "Недостаточно $"
    crystals = money_amount // MONEY_TO_CRYSTAL
    if crystals < 1:
        return False, 0, "Мало $"
    update_balance(user_id, -money_amount)
    update_crystals(user_id, crystals)
    add_transaction(user_id, crystals, 'CRYSTAL', 'reverse_exchange', 'completed')
    return True, crystals, ""
