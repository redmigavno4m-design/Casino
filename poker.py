"""🃏 Техасский Холдем 1-на-1"""
import random

SUITS = [('♠', False), ('♥', True), ('♦', True), ('♣', False)]
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


def new_deck():
    deck = [{'rank': r, 'suit': s, 'red': red} for s, red in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def card_str(c):
    return f"{c['rank']}{c['suit']}"


def hand_str(h, hidden=False):
    if hidden:
        return "🎴 🎴"
    return " ".join(card_str(c) for c in h)


def evaluate_5(cards):
    """Оценка 5 карт. Возвращает (rank, name, kickers)"""
    vals = []
    for c in cards:
        r = c['rank']
        if r == 'A': vals.append(14)
        elif r == 'K': vals.append(13)
        elif r == 'Q': vals.append(12)
        elif r == 'J': vals.append(11)
        else: vals.append(int(r))
    vals.sort(reverse=True)
    suits = [c['suit'] for c in cards]

    is_flush = len(set(suits)) == 1
    is_straight = all(vals[i] - vals[i+1] == 1 for i in range(4))
    # Wheel (A-2-3-4-5)
    if vals == [14, 5, 4, 3, 2]:
        is_straight = True

    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    sorted_c = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))
    groups = [c for _, c in sorted_c]

    if is_flush and is_straight:
        return 8, "Стрит-флеш", vals
    if groups[0] == 4:
        return 7, "Каре", vals
    if groups[0] == 3 and len(groups) > 1 and groups[1] == 2:
        return 6, "Фулл-хаус", vals
    if is_flush:
        return 5, "Флеш", vals
    if is_straight:
        return 4, "Стрит", vals
    if groups[0] == 3:
        return 3, "Сет", vals
    if groups[0] == 2 and len(groups) > 1 and groups[1] == 2:
        return 2, "Две пары", vals
    if groups[0] == 2:
        return 1, "Пара", vals
    return 0, "Старшая карта", vals


def best_hand(cards):
    """Из 5-7 карт выбирает лучшую комбинацию."""
    if len(cards) < 5:
        return evaluate_5(cards)
    best = None
    for i in range(len(cards) - 4):
        for j in range(i + 1, len(cards) - 3):
            for k in range(j + 1, len(cards) - 2):
                for l in range(k + 1, len(cards) - 1):
                    for m in range(l + 1, len(cards)):
                        combo = [cards[i], cards[j], cards[k], cards[l], cards[m]]
                        ev = evaluate_5(combo)
                        if best is None or ev[0] > best[0] or (ev[0] == best[0] and ev[2] > best[2]):
                            best = ev
    return best


def compare(a, b):
    """-1 = a < b, 0 = равно, 1 = a > b"""
    if a[0] != b[0]:
        return 1 if a[0] > b[0] else -1
    if a[2] > b[2]:
        return 1
    if a[2] < b[2]:
        return -1
    return 0


def new_game(blind):
    deck = new_deck()
    return {
        'deck': deck,
        'player': [deck.pop(), deck.pop()],
        'dealer': [deck.pop(), deck.pop()],
        'community': [],
        'pot': blind * 2,
        'player_bet': blind,
        'dealer_bet': blind,
        'player_chips': 1000 - blind,
        'dealer_chips': 1000 - blind,
        'blind': blind,
        'phase': 'preflop',
        'last_raise': blind,
        'active': True,
    }


def dealer_action(game):
    """Простой ИИ дилера: чек/колл/рейз/фолд"""
    dh = best_hand(game['dealer'] + game['community'])
    rank = dh[0]

    need = game['player_bet'] - game['dealer_bet']

    # Мусор — иногда фолд
    if rank == 0 and random.random() < 0.35:
        return 'fold'
    # Хорошая рука — рейз
    if rank >= 3 and game['dealer_chips'] > need + 100:
        return 'raise'
    # Средняя — блеф
    if rank >= 1 and random.random() < 0.25 and game['dealer_chips'] > need + 100:
        return 'raise'
    # Иначе — колл или чек
    if need > 0:
        if game['dealer_chips'] >= need:
            return 'call'
        return 'check'
    return 'check'


def advance_phase(game):
    """Переход к следующей улице."""
    order = ['preflop', 'flop', 'turn', 'river', 'showdown']
    idx = order.index(game['phase'])
    if idx >= len(order) - 1:
        return 'showdown'
    game['phase'] = order[idx + 1]
    if game['phase'] == 'flop':
        for _ in range(3):
            game['community'].append(game['deck'].pop())
    elif game['phase'] in ('turn', 'river'):
        game['community'].append(game['deck'].pop())
    game['player_bet'] = 0
    game['dealer_bet'] = 0
    return game['phase']
