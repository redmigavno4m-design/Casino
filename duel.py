"""👥 Дуэли между игроками (PvP)"""
import random

# Активные дуэли: chat_id -> {players: [uid1, uid2], state: {...}}
active_duels = {}


def create_duel(chat_id, uid1, uid2, bet):
    active_duels[chat_id] = {
        'p1': uid1,
        'p2': uid2,
        'bet': bet,
        'hp': {uid1: 100, uid2: 100},
        'turn': uid1,
        'log': [],
        'active': True,
    }
    return active_duels[chat_id]


def attack(chat_id, attacker_id):
    d = active_duels.get(chat_id)
    if not d or not d['active']:
        return None
    if d['turn'] != attacker_id:
        return None

    opponent = d['p2'] if attacker_id == d['p1'] else d['p1']
    dmg = random.randint(10, 30)
    d['hp'][opponent] = max(0, d['hp'][opponent] - dmg)
    d['log'].append(f"⚔️ {attacker_id} → {dmg} урона")
    d['turn'] = opponent

    if d['hp'][opponent] <= 0:
        d['active'] = False
        return {'winner': attacker_id, 'loser': opponent, 'damage': dmg}
    return {'damage': dmg, 'next': opponent}


def defend(chat_id, defender_id):
    d = active_duels.get(chat_id)
    if not d or not d['active']:
        return None
    if d['turn'] != defender_id:
        return None

    opponent = d['p2'] if defender_id == d['p1'] else d['p1']
    # Защита уменьшает следующий урон в 2 раза
    dmg = random.randint(5, 15)
    d['hp'][defender_id] = max(0, d['hp'][defender_id] - dmg)
    d['log'].append(f"🛡️ {defender_id} защищается, получил {dmg}")
    d['turn'] = opponent
    return {'damage': dmg, 'next': opponent}
