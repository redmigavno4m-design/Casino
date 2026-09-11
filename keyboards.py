from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="slots"),
         InlineKeyboardButton(text="🎡 Рулетка", callback_data="roulette")],
        [InlineKeyboardButton(text="🎲 Кости", callback_data="dice"),
         InlineKeyboardButton(text="🪙 Монетка", callback_data="coin")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="🎁 Бонус", callback_data="daily")],
    ])


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
