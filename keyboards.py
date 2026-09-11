from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        # Классика
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="slots"),
         InlineKeyboardButton(text="🎡 Рулетка", callback_data="roulette")],
        [InlineKeyboardButton(text="🎲 Кости", callback_data="dice"),
         InlineKeyboardButton(text="🪙 Монетка", callback_data="coin")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="mines"),
         InlineKeyboardButton(text="🎡 Колесо", callback_data="wheel")],

        # 🆕 Спортивные
        [InlineKeyboardButton(text="🎯 Дартс", callback_data="darts"),
         InlineKeyboardButton(text="⚽ Футбол", callback_data="football")],
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="basket"),
         InlineKeyboardButton(text="🎳 Боулинг", callback_data="bowling")],
        [InlineKeyboardButton(text="🎰 Слот-машина", callback_data="slot_dice")],

        # Информация
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="🎯 Квесты", callback_data="quests"),
         InlineKeyboardButton(text="🏅 Ачивки", callback_data="achievements")],
        [InlineKeyboardButton(text="💎 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="🎁 Бонус", callback_data="daily")],
    ])


def sport_choice(game):
    """Меню выбора для спортивных игр"""
    choices = {
        'darts': [
            ("🎯 В яблочко (x5)", f"sport_darts_center"),
            ("🎯 Внутренний круг (x2)", f"sport_darts_middle"),
            ("🎯 В мишень (x1.5)", f"sport_darts_any"),
        ],
        'football': [
            ("⚽ Гол (x1.9-4)", f"sport_football_goal"),
            ("⚽ В девятку (x4)", f"sport_football_topcorner"),
        ],
        'basket': [
            ("🏀 Бросок (x1.9-4.5)", f"sport_basket_shot"),
            ("🏀 Трёхочковый (x4.5)", f"sport_basket_three"),
        ],
        'bowling': [
            ("🎳 Страйк (x5)", f"sport_bowling_strike"),
            ("🎳 Любое попадание", f"sport_bowling_any"),
        ],
    }
    rows = []
    for text, cb in choices.get(game, []):
        rows.append([InlineKeyboardButton(text=text, callback_data=cb)])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]
    ])


def bet_menu(game, balance):
    bets = [b for b in [50, 100, 250, 500, 1000] if b <= balance]
    rows = []
    row = []
    for b in bets:
        row.append(InlineKeyboardButton(text=f"💰{b}", callback_data=f"bet_{game}_{b}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if not bets:
        rows.append([InlineKeyboardButton(text="Нет средств", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bj_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Взять", callback_data="bj_hit"),
         InlineKeyboardButton(text="✋ Стоп", callback_data="bj_stand")],
    ])


def mines_grid_buttons(game_id, opened, mines_positions, grid_size=5):
    """Создаёт сетку кнопок для мин."""
    rows = []
    row = []
    for i in range(grid_size * grid_size):
        if i in opened:
            symbol = "💎"
        elif i in mines_positions and game_id.get('finished'):
            symbol = "💣"
        else:
            symbol = "⬜"
        row.append(InlineKeyboardButton(text=symbol, callback_data=f"mines_open_{i}"))
        if len(row) == grid_size:
            rows.append(row)
            row = []
    rows.append([InlineKeyboardButton(text="💰 Забрать", callback_data="mines_cashout")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
