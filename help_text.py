HELP_CATEGORIES = {
    'slots': '🎰 Слоты', 'vslot': '🎰 Видео-слоты', 'slot_dice': '🎰 Слот-машина',
    'roulette': '🎡 Рулетка', 'aroulette': '🎡 Амер. рулетка', 'mroulette': '🎡 Мини-рулетка',
    'dice': '🎲 Кости', 'craps': '🎯 Крэпс', 'sickbo': '🎲 Сик-Бо', 'hilo': '🎲 Хай-Лоу',
    'coin': '🪙 Монетка', 'mines': '💣 Мины', 'keno': '💎 Кено', 'crash': '💥 Краш',
    'scratch': '🎰 Скретч', 'lottery': '🎟 Лотерея', 'wheel': '🎡 Колесо',
    'darts': '🎯 Дартс', 'football': '⚽ Футбол', 'basket': '🏀 Баскет', 'bowling': '🎳 Боулинг',
}

SEARCH_KEYWORDS = {
    'slots': ['слот', 'барабан'], 'vslot': ['видео'], 'roulette': ['рулет', 'красн'],
    'dice': ['кост', 'кубик'], 'craps': ['крэпс'], 'mines': ['мин'], 'keno': ['кено'],
    'crash': ['краш'], 'darts': ['дартс'], 'football': ['футбол'], 'basket': ['баскет'],
    'bowling': ['боулинг'],
}


def search_games(query):
    q = query.lower().strip()
    if not q:
        return []
    result = []
    for key, name in HELP_CATEGORIES.items():
        if q in name.lower():
            result.append((key, name))
            continue
        for kw in SEARCH_KEYWORDS.get(key, []):
            if q in kw or kw in q:
                result.append((key, name))
                break
    return result


GAME_HELP = {
    'slots': {'text': "🎰 <b>СЛОТЫ</b>\n\n3 барабана. 3 совпадения → x3-x40. 2 → x1.7", 'preview': None, 'gif': None},
    'roulette': {'text': "🎡 <b>РУЛЕТКА</b>\n\n🔴 Красное → x2\n⚫ Чёрное → x2\n🟢 Зеро → x36", 'preview': None, 'gif': None},
    'dice': {'text': "🎲 <b>КОСТИ</b>\n\n⬆️ Больше 3 → x1.9\n⬇️ Меньше 4 → x1.9\n🎯 Ровно 6 → x4.5", 'preview': None, 'gif': None},
    'coin': {'text': "🪙 <b>МОНЕТКА</b>\n\nОрёл/Решка → x1.9", 'preview': None, 'gif': None},
    'mines': {'text': "💣 <b>МИНЫ</b>\n\n5×5, 3 мины", 'preview': None, 'gif': None},
    'crash': {'text': "💥 <b>КРАШ</b>\n\nЗабирай до краха!", 'preview': None, 'gif': None},
    'darts': {'text': "🎯 <b>ДАРТС</b>\n\nЯблочко x5 | Круг x2 | Мишень x1.5", 'preview': None, 'gif': None},
    'football': {'text': "⚽ <b>ФУТБОЛ</b>\n\nГол x1.9 | Девятка x4", 'preview': None, 'gif': None},
    'basket': {'text': "🏀 <b>БАСКЕТ</b>\n\nБросок x1.9 | Трёхочковый x4.5", 'preview': None, 'gif': None},
    'bowling': {'text': "🎳 <b>БОУЛИНГ</b>\n\nСтрайк x5", 'preview': None, 'gif': None},
}


def get_help(key):
    d = GAME_HELP.get(key)
    return (d['text'], d['preview'], d['gif']) if d else (None, None, None)


FAQ_CATEGORIES = {
    'pay': ('💰 Оплата', "Пополнение через Stars, CryptoBot или ручную оплату"),
    'games': ('🎮 Игры', "20+ игр. Правила → /help"),
    'tech': ('⚙️ Технические', "Если бот молчит — /start"),
    'bonus': ('🎁 Бонусы', "Ежедневка, колесо, рефералы, промокоды"),
    'withdraw': ('💎 Вывод', "Вывод кристаллов. Курс: 1💎 = 2.0₽"),
}


def get_faq(cat):
    return FAQ_CATEGORIES.get(cat, (None, None))[1]


def get_categories():
    return HELP_CATEGORIES
