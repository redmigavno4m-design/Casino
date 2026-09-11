from database import get_user


def get_multiplier(user_id):
    u = get_user(user_id)
    total = u['total_won'] + u['total_lost']
    if total < 5000:
        return 1.0
    ratio = u['total_won'] / total if total > 0 else 0.5
    if ratio < 0.40: return 1.15
    if ratio < 0.50: return 1.05
    if ratio < 0.55: return 1.0
    if ratio < 0.65: return 0.90
    return 0.75


def apply_dynamic_odds(user_id, win):
    if win <= 0:
        return win
    return int(win * get_multiplier(user_id))
