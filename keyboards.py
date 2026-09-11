from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SPORT_QUICK_BETS, SUPPORTED_LANGS
from help_text import HELP_CATEGORIES


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="slots"),
         InlineKeyboardButton(text="🎰 Видео-слоты", callback_data="vslot")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="roulette"),
         InlineKeyboardButton(text="🎡 Амер. рулетка", callback_data="aroulette")],
        [InlineKeyboardButton(text="🎡 Мини-рулетка", callback_data="mroulette"),
         InlineKeyboardButton(text="🎲 Кости", callback_data="dice")],
        [InlineKeyboardButton(text="🎲 Хай-Лоу", callback_data="hilo"),
         InlineKeyboardButton(text="🎲 Сик-Бо", callback_data="sickbo")],
        [InlineKeyboardButton(text="🎯 Крэпс", callback_data="craps"),
         InlineKeyboardButton(text="🪙 Монетка", callback_data="coin")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="mines"),
         InlineKeyboardButton(text="💎 Кено", callback_data="keno")],
        [InlineKeyboardButton(text="💥 Краш", callback_data="crash"),
         InlineKeyboardButton(text="🎟 Лотерея", callback_data="lottery")],
        [InlineKeyboardButton(text="🎰 Скретч", callback_data="scratch"),
         InlineKeyboardButton(text="🎡 Колесо", callback_data="wheel")],
        [InlineKeyboardButton(text="🎯 Дартс", callback_data="darts"),
         InlineKeyboardButton(text="⚽ Футбол", callback_data="football")],
        [InlineKeyboardButton(text="🏀 Баскет", callback_data="basket"),
         InlineKeyboardButton(text="🎳 Боулинг", callback_data="bowling")],
        [InlineKeyboardButton(text="🎰 Слот-машина", callback_data="slot_dice")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="🎯 Квесты", callback_data="quests"),
         InlineKeyboardButton(text="🏅 Ачивки", callback_data="achievements")],
        [InlineKeyboardButton(text="💎 Магазин", callback_data="shop"),
         InlineKeyboardButton(text="💰 Вывести", callback_data="withdraw")],
        [InlineKeyboardButton(text="👑 VIP", callback_data="vip_info"),
         InlineKeyboardButton(text="🎁 Бонус", callback_data="daily")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
         InlineKeyboardButton(text="🌍 Язык", callback_data="lang_menu")],
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
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mines_grid_buttons(game, opened, mines_positions, grid_size=5):
    rows = []
    row = []
    for i in range(grid_size * grid_size):
        if i in opened:
            s = "💎"
        elif i in mines_positions and game.get('finished'):
            s = "💣"
        else:
            s = "⬜"
        row.append(InlineKeyboardButton(text=s, callback_data=f"mines_open_{i}"))
        if len(row) == grid_size:
            rows.append(row)
            row = []
    rows.append([InlineKeyboardButton(text="💰 Забрать", callback_data="mines_cashout")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sport_choice(game):
    choices = {
        'darts': [("🎯 В яблочко (x5)", "sport_darts_center"),
                  ("🎯 Внутр. круг (x2)", "sport_darts_middle"),
                  ("🎯 В мишень (x1.5)", "sport_darts_any")],
        'football': [("⚽ Гол", "sport_football_goal"),
                     ("⚽ В девятку (x4)", "sport_football_topcorner")],
        'basket': [("🏀 Бросок", "sport_basket_shot"),
                   ("🏀 Трёхочковый (x4.5)", "sport_basket_three")],
        'bowling': [("🎳 Страйк (x5)", "sport_bowling_strike"),
                    ("🎳 Любое", "sport_bowling_any")],
    }
    rows = []
    for t, cb in choices.get(game, []):
        rows.append([InlineKeyboardButton(text=t, callback_data=cb)])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sport_bet_menu(prefix, back_cb="main_menu"):
    rows = []
    row = []
    for b in SPORT_QUICK_BETS:
        row.append(InlineKeyboardButton(text=f"💰{b}", callback_data=f"sbet_{prefix}_{b}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✏️ Своя", callback_data=f"scustom_{prefix}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def help_menu(query=None):
    if query:
        from help_text import search_games
        results = search_games(query)
        rows = []
        if not results:
            rows.append([InlineKeyboardButton(text=f"❌ Ничего: {query}", callback_data="noop")])
        else:
            for key, name in results:
                rows.append([InlineKeyboardButton(text=name, callback_data=f"help_{key}")])
        rows.append([InlineKeyboardButton(text="📖 Все игры", callback_data="help")])
        rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    rows = []
    row = []
    for key, name in HELP_CATEGORIES.items():
        row.append(InlineKeyboardButton(text=name, callback_data=f"help_{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="❓ FAQ", callback_data="help_faq")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lang_menu():
    from lang import lang_name
    rows = []
    for l in SUPPORTED_LANGS:
        rows.append([InlineKeyboardButton(text=lang_name(l), callback_data=f"setlang_{l}")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def withdraw_methods_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 CryptoBot (USDT/TON)", callback_data="wd_method_cryptobot")],
        [InlineKeyboardButton(text="💵 Ручная заявка", callback_data="wd_method_manual")],
        [InlineKeyboardButton(text="📜 История выводов", callback_data="wd_history")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")],
    ])


def withdraw_amount_menu(balance_crystals):
    amounts = [a for a in [50, 100, 250, 500, 1000] if a <= balance_crystals]
    rows = []
    row = []
    for a in amounts:
        row.append(InlineKeyboardButton(text=f"💎{a}", callback_data=f"wd_amount_{a}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✏️ Своя", callback_data="wd_custom")])
    if balance_crystals >= 50:
        rows.append([InlineKeyboardButton(text=f"💎 Всё ({balance_crystals})", callback_data=f"wd_amount_{balance_crystals}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="withdraw")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_withdrawals_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Ожидающие", callback_data="adm_wd_pending")],
        [InlineKeyboardButton(text="✅ Выплаченные", callback_data="adm_wd_approved")],
        [InlineKeyboardButton(text="❌ Отклонённые", callback_data="adm_wd_rejected")],
    ])
