activated = {}

PROMOS = {"WELCOME": 500, "CASINO1000": 1000, "LUCKY777": 777, "BONUS500": 500}


def activate(user_id, code):
    code = code.upper().strip()
    if code not in PROMOS:
        return False, 0, "❌ Промокод не найден"
    if user_id not in activated:
        activated[user_id] = []
    if code in activated[user_id]:
        return False, 0, "⚠️ Уже активировал"
    activated[user_id].append(code)
    return True, PROMOS[code], f"🎉 +{PROMOS[code]}$!"
