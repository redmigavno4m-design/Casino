"""🎁 Промокоды"""
import time

# Активированные промокоды: {user_id: [code1, code2]}
activated = {}

PROMOS = {
    "WELCOME": 500,
    "CASINO1000": 1000,
    "LUCKY777": 777,
    "BONUS500": 500,
}


def activate(user_id, code):
    """
    Возвращает (успех, сумма, сообщение).
    """
    code = code.upper().strip()

    if code not in PROMOS:
        return False, 0, "❌ Промокод не найден"

    if user_id not in activated:
        activated[user_id] = []

    if code in activated[user_id]:
        return False, 0, "⚠️ Ты уже активировал этот промокод"

    activated[user_id].append(code)
    amount = PROMOS[code]
    return True, amount, f"🎉 +{amount}$!"
