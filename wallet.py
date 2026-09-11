"""
💎 Кошелёк: кристаллы, обмен на игровые $
"""
from config import CRYSTAL_TO_MONEY
from database import get_user, update_crystals, update_balance, add_transaction


def buy_crystals(user_id, amount, method, ext_id=None):
    """
    Начисляет кристаллы после успешной оплаты.
    amount: количество кристаллов
    method: 'stars', 'yookassa', 'crypto'
    """
    update_crystals(user_id, amount)
    add_transaction(user_id, amount, method.upper(), method, 'completed', ext_id)


def exchange_crystals(user_id, crystal_amount):
    """
    Обмен кристаллов на игровые $.
    Возвращает (success, money) или (False, 0)
    """
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


def format_crystals(amount):
    return f"💎 {amount}"
