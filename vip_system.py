from database import get_user, update_balance

VIP_LEVELS = [
    (0, 'Новичок', 0), (5000, 'Бронза', 2), (20000, 'Серебро', 3),
    (50000, 'Золото', 5), (150000, 'Платина', 7),
    (500000, 'Бриллиант', 10), (1000000, 'Император', 15),
]


def get_vip_level(user_id):
    u = get_user(user_id)
    total = u['total_lost']
    for i in range(len(VIP_LEVELS) - 1, -1, -1):
        if total >= VIP_LEVELS[i][0]:
            return i, VIP_LEVELS[i][1], VIP_LEVELS[i][2]
    return 0, 'Новичок', 0def give_cashback(user_id):
    u = get_user(user_id)
    _, _, pct = get_vip_level(user_id)
    week = u['total_lost'] // 10
    cb = int(week * pct / 100)
    if cb > 0:
        update_balance(user_id, cb)
        return cb
    return 0


def get_vip_progress(user_id):
    u = get_user(user_id)
    total = u['total_lost']
    current, next_level = 0, 1
    for i in range(len(VIP_LEVELS) - 1, -1, -1):
        if total >= VIP_LEVELS[i][0]:
            current = i
            next_level = i + 1
            break
    if next_level >= len(VIP_LEVELS):
        return current, VIP_LEVELS[current][1], None, 0
    nt = VIP_LEVELS[next_level][0]
    p = (total - VIP_LEVELS[current][0]) / (nt - VIP_LEVELS[current][0]) * 100
    return current, VIP_LEVELS[current][1], VIP_LEVELS[next_level][1], p
