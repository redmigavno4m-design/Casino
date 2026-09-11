import asyncio
import time
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, DAILY_BONUS, WHEEL_PRIZES, WHEEL_COOLDOWN
from database import (
    init_db, get_user, update_balance, record_game,
    update_daily_bonus, update_wheel_time, unlock_achievement,
    set_quests, top_players
)
from games import (
    play_slots, play_roulette, play_dice, play_coin,
    new_deck, hand_value, card_str, hand_str,
    mines_new_game, mines_multiplier,
    spin_wheel, ACHIEVEMENTS, check_achievements,
    get_level, generate_quests, LEVELS
)
from keyboards import (
    main_menu, back_menu, bet_menu, bj_menu, mines_grid_buttons
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Активные игры в памяти
bj_games = {}
mines_games = {}


def fmt(amount):
    return f"{int(amount):,}".replace(",", " ") + "$"


def header(u):
    return f"👤 <b>{u['first_name'] or 'Игрок'}</b>\n💰 Баланс: <b>{fmt(u['balance'])}</b>\n"


async def edit(call, text, kb=None):
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")


async def notify_achievements(message, user_id):
    u = get_user(user_id)
    new_ach = check_achievements(u)
    for aid in new_ach:
        if unlock_achievement(user_id, aid):
            icon, name, _ = ACHIEVEMENTS[aid]
            await message.answer(
                f"🏆 <b>ДОСТИЖЕНИЕ!</b>\n{icon} <b>{name}</b>",
                parse_mode="HTML"
            )


# ============================================================
# СТАРТ
# ============================================================
@dp.message(CommandStart())
async def start(m: Message):
    u = get_user(m.from_user.id, m.from_user.username, m.from_user.first_name)
    lvl_i, lvl_name, xp_to_next, _ = get_level(u['xp'])
    text = (
        f"🎰 <b>CASINO ROYALE</b>\n\n"
        f"{header(u)}"
        f"🏅 Уровень: <b>{lvl_name}</b>\n"
        f"⚡ Опыт: <b>{u['xp']}</b>\n"
        f"🎮 Игр: <b>{u['games']}</b> | 🏆 Побед: <b>{u['wins']}</b>\n\n"
        f"Выбирай игру!"
    )
    await m.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@dp.callback_query(F.data == "main_menu")
async def cb_main(c: CallbackQuery):
    u = get_user(c.from_user.id)
    lvl_i, lvl_name, xp_to_next, _ = get_level(u['xp'])
    text = (
        f"🎰 <b>CASINO ROYALE</b>\n\n"
        f"{header(u)}"
        f"🏅 <b>{lvl_name}</b> | ⚡ {u['xp']} XP\n\n"
        f"Выбирай игру:"
    )
    await edit(c, text, main_menu())
    await c.answer()


@dp.callback_query(F.data == "noop")
async def cb_noop(c: CallbackQuery):
    await c.answer("Возьми бонус 🎁", show_alert=True)


@dp.callback_query(F.data == "profile")
async def cb_profile(c: CallbackQuery):
    u = get_user(c.from_user.id)
    wr = (u['wins'] / u['games'] * 100) if u['games'] else 0
    lvl_i, lvl_name, xp_to_next, next_name = get_level(u['xp'])
    ach_count = len(u['achievements'])
    ach_total = len(ACHIEVEMENTS)
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n"
        f"🏅 Уровень: <b>{lvl_name}</b>\n"
        f"⚡ Опыт: <b>{u['xp']}</b>"
        + (f" (до следующего: {xp_to_next})\n" if next_name else "\n") +
        f"🎮 Игр: <b>{u['games']}</b>\n"
        f"🏆 Побед: <b>{u['wins']}</b>\n"
        f"📊 Винрейт: <b>{wr:.1f}%</b>\n"
        f"🔥 Макс. серия: <b>{u['max_streak']}</b>\n"
        f"💎 Рекорд: <b>{fmt(u['biggest_win'])}</b>\n"
        f"📈 Выиграно: <b>{fmt(u['total_won'])}</b>\n"
        f"📉 Проиграно: <b>{fmt(u['total_lost'])}</b>\n"
        f"🏆 Ачивки: <b>{ach_count}/{ach_total}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()


@dp.callback_query(F.data == "top")
async def cb_top(c: CallbackQuery):
    rows = top_players(10)
    text = "🏆 <b>ТОП-10</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (fn, un, bal) in enumerate(rows):
        m = medals[i] if i < 3 else f"{i+1}."
        name = fn or un or "Аноним"
        text += f"{m} <b>{name}</b> — {fmt(bal)}\n"
    await edit(c, text, back_menu())
    await c.answer()


@dp.callback_query(F.data == "achievements")
async def cb_ach(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = "🏅 <b>ДОСТИЖЕНИЯ</b>\n\n"
    unlocked = 0
    for aid, (icon, name, desc) in ACHIEVEMENTS.items():
        if aid in u['achievements']:
            unlocked += 1
            text += f"✅ {icon} <b>{name}</b>\n<i>{desc}</i>\n\n"
        else:
            text += f"🔒 {icon} <b>{name}</b>\n<i>{desc}</i>\n\n"
    text += f"\n📊 Открыто: <b>{unlocked}/{len(ACHIEVEMENTS)}</b>"
    await edit(c, text, back_menu())
    await c.answer()


@dp.callback_query(F.data == "daily")
async def cb_daily(c: CallbackQuery):
    u = get_user(c.from_user.id)
    now = int(time.time())
    if now - u['last_bonus'] >= 86400:
        update_balance(c.from_user.id, DAILY_BONUS)
        update_daily_bonus(c.from_user.id)
        u = get_user(c.from_user.id)
        await c.answer(f"🎁 +{DAILY_BONUS}$", show_alert=True)
        text = f"🎁 <b>Бонус +{DAILY_BONUS}$!</b>\n\n{header(u)}"
    else:
        w = 86400 - (now - u['last_bonus'])
        text = f"⏳ Через <b>{w//3600}ч {(w%3600)//60}м</b>"
    await edit(c, text, back_menu())
    await c.answer()


# ============================================================
# КВЕСТЫ
# ============================================================
@dp.callback_query(F.data == "quests")
async def cb_quests(c: CallbackQuery):
    u = get_user(c.from_user.id)
    today = time.strftime('%Y-%m-%d')

    if u['quests_date'] != today or not u['daily_quests']:
        quests = generate_quests()
        set_quests(c.from_user.id, quests)
        u = get_user(c.from_user.id)

    quests = u['daily_quests']
    text = "🎯 <b>ЕЖЕДНЕВНЫЕ КВЕСТЫ</b>\n\n"
    for qid, q in quests.items():
        mark = "✅" if q['done'] else "▶️"
        progress = f"{q['progress']}/{q['target']}"
        text += f"{mark} <b>{q['text']}</b>\n"
        text += f"   Прогресс: {progress} | Награда: {q['reward']}$\n\n"
    await edit(c, text, back_menu())
    await c.answer()


# ============================================================
# КОЛЕСО ФОРТУНЫ
# ============================================================
@dp.callback_query(F.data == "wheel")
async def cb_wheel(c: CallbackQuery):
    u = get_user(c.from_user.id)
    now = int(time.time())
    if now - u['last_wheel'] < WHEEL_COOLDOWN:
        w = WHEEL_COOLDOWN - (now - u['last_wheel'])
        text = f"🎡 <b>Колесо фортуны</b>\n\n⏳ Следующий спин через <b>{w//3600}ч {(w%3600)//60}м</b>"
        await edit(c, text, back_menu())
        await c.answer()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎡 КРУТИТЬ!", callback_data="wheel_spin")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")],
    ])
    text = (
        f"🎡 <b>КОЛЕСО ФОРТУНЫ</b>\n\n"
        f"Бесплатный спин раз в 24 часа!\n"
        f"Призы: {', '.join(str(p)+'$' for p in WHEEL_PRIZES)}\n\n"
        f"Крути! 🍀"
    )
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data == "wheel_spin")
async def cb_wheel_spin(c: CallbackQuery):
    u = get_user(c.from_user.id)
    now = int(time.time())
    if now - u['last_wheel'] < WHEEL_COOLDOWN:
        await c.answer("⏳ Уже крутил!", show_alert=True)
        return

    idx, prize = spin_wheel(WHEEL_PRIZES)
    update_balance(c.from_user.id, prize)
    update_wheel_time(c.from_user.id)

    # Анимация через редактирование
    for i in range(3):
        await asyncio.sleep(0.4)
        try:
            await c.message.edit_text(
                f"🎡 <b>Крутится...</b>\n\n"
                f"{'◀️' * (i+1)} 🎁 🎁 🎁",
                parse_mode="HTML"
            )
        except Exception:
            pass

    u = get_user(c.from_user.id)
    text = (
        f"🎉 <b>ВЫПАЛО: {prize}$!</b>\n\n"
        f"{header(u)}"
    )
    await edit(c, text, back_menu())
    await c.answer(f"🎉 +{prize}$", show_alert=True)
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# СЛОТЫ
# ============================================================
@dp.callback_query(F.data == "slots")
async def cb_slots(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🎰 <b>СЛОТЫ</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n\n"
        f"7️⃣x40 💎x20 ⭐x12 🍇x8 🍊x5 🍋x4 🍒x3\n"
        f"2 совпадения — x1.7\n\n"
        f"Выбери ставку:"
    )
    await edit(c, text, bet_menu("slots", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_slots_"))
async def slots_play(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    update_balance(c.from_user.id, -bet)
    win, reels, desc = play_slots(bet)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)

    u = get_user(c.from_user.id)
    reel_str = " | ".join(reels)
    result = '+' if win > 0 else '-'
    amount = win if win > 0 else bet
    text = (
        f"🎰 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"<code>{reel_str}</code>\n\n"
        f"{desc}\n"
        f"💰 Итог: <b>{result}{fmt(amount)}</b>\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, bet_menu("slots", u['balance']))
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# РУЛЕТКА
# ============================================================
@dp.callback_query(F.data == "roulette")
async def cb_roulette(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🎡 <b>РУЛЕТКА</b>\n\n💰 Баланс: <b>{fmt(u['balance'])}</b>\n\nВыбери ставку:"
    await edit(c, text, bet_menu("roulette", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_roulette_"))
async def roulette_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное x2", callback_data=f"rs_{bet}_red"),
         InlineKeyboardButton(text="⚫ Чёрное x2", callback_data=f"rs_{bet}_black")],
        [InlineKeyboardButton(text="🟢 Зеро x36", callback_data=f"rs_{bet}_zero")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="roulette")],
    ])
    await edit(c, f"🎡 Ставка: <b>{fmt(bet)}</b>\n\nНа что ставим?", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("rs_"))
async def roulette_spin(c: CallbackQuery):
    parts = c.data.split("_")
    bet = int(parts[1])
    pick = parts[2]
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    update_balance(c.from_user.id, -bet)
    win, n, color = play_roulette(bet, pick)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    result = '+' if win > 0 else '-'
    amount = win if win > 0 else bet
    text = (
        f"🎡 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Выпало: <b>{n}</b> ({color})\n\n"
        f"💰 Итог: <b>{result}{fmt(amount)}</b>\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# КОСТИ
# ============================================================
@dp.callback_query(F.data == "dice")
async def cb_dice(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🎲 <b>КОСТИ</b>\n\n💰 Баланс: <b>{fmt(u['balance'])}</b>\n\nВыбери ставку:"
    await edit(c, text, bet_menu("dice", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_dice_"))
async def dice_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Больше 3 (x1.9)", callback_data=f"ds_{bet}_high"),
         InlineKeyboardButton(text="⬇️ Меньше 4 (x1.9)", callback_data=f"ds_{bet}_low")],
        [InlineKeyboardButton(text="🎯 Ровно 6 (x4.5)", callback_data=f"ds_{bet}_six")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="dice")],
    ])
    await edit(c, f"🎲 Ставка: <b>{fmt(bet)}</b>\n\nТвой прогноз?", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("ds_"))
async def dice_roll(c: CallbackQuery):
    parts = c.data.split("_")
    bet = int(parts[1])
    pick = parts[2]
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    update_balance(c.from_user.id, -bet)
    win, v = play_dice(bet, pick)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    faces = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣"}
    result = '+' if win > 0 else '-'
    amount = win if win > 0 else bet
    text = (
        f"🎲 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Выпало: {faces[v]} <b>{v}</b>\n\n"
        f"💰 Итог: <b>{result}{fmt(amount)}</b>\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# МОНЕТКА
# ============================================================
@dp.callback_query(F.data == "coin")
async def cb_coin(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🪙 <b>МОНЕТКА</b>\n\n💰 Баланс: <b>{fmt(u['balance'])}</b>\n\nВыбери ставку:"
    await edit(c, text, bet_menu("coin", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_coin_"))
async def coin_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Орёл (x1.9)", callback_data=f"cs_{bet}_eagle"),
         InlineKeyboardButton(text="🪙 Решка (x1.9)", callback_data=f"cs_{bet}_tail")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="coin")],
    ])
    await edit(c, f"🪙 Ставка: <b>{fmt(bet)}</b>\n\nЧто выбираешь?", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("cs_"))
async def coin_flip(c: CallbackQuery):
    parts = c.data.split("_")
    bet = int(parts[1])
    pick = parts[2]
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    update_balance(c.from_user.id, -bet)
    win, result = play_coin(bet, pick)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    result_str = "🦅 Орёл" if result == 'eagle' else "🪙 Решка"
    r = '+' if win > 0 else '-'
    amount = win if win > 0 else bet
    text = (
        f"🪙 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Выпало: <b>{result_str}</b>\n\n"
        f"💰 Итог: <b>{r}{fmt(amount)}</b>\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🃏 БЛЭКДЖЕК
# ============================================================
@dp.callback_query(F.data == "bj")
async def cb_bj(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🃏 <b>БЛЭКДЖЕК</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n\n"
        f"Цель — набрать 21 или ближе, чем дилер.\n"
        f"Дилер добирает до 17.\n\n"
        f"Выбери ставку:"
    )
    await edit(c, text, bet_menu("bj", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_bj_"))
async def bj_start(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    update_balance(c.from_user.id, -bet)

    deck = new_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    bj_games[c.from_user.id] = {
        'deck': deck, 'player': player, 'dealer': dealer,
        'bet': bet, 'active': True
    }

    pv = hand_value(player)
    text = (
        f"🃏 <b>БЛЭКДЖЕК</b>\n\n"
        f"🤖 Дилер: <b>{card_str(dealer[0])}</b> 🎴\n"
        f"👤 Ты: {hand_str(player)} — <b>{pv}</b>\n\n"
        f"Что делаешь?"
    )
    await edit(c, text, bj_menu())
    await c.answer()


@dp.callback_query(F.data == "bj_hit")
async def bj_hit(c: CallbackQuery):
    g = bj_games.get(c.from_user.id)
    if not g or not g['active']:
        await c.answer("Игра не активна", show_alert=True)
        return

    g['player'].append(g['deck'].pop())
    pv = hand_value(g['player'])

    if pv > 21:
        g['active'] = False
        record_game(c.from_user.id, g['bet'], 0)
        u = get_user(c.from_user.id)
        text = (
            f"🃏 <b>ПЕРЕБОР!</b>\n\n"
            f"👤 Ты: {hand_str(g['player'])} — <b>{pv}</b>\n\n"
            f"💸 Потеряно: <b>-{fmt(g['bet'])}</b>\n\n"
            f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
        )
        await edit(c, text, back_menu())
        await c.answer()
        del bj_games[c.from_user.id]
        return

    text = (
        f"🃏 <b>БЛЭКДЖЕК</b>\n\n"
        f"🤖 Дилер: <b>{card_str(g['dealer'][0])}</b> 🎴\n"
        f"👤 Ты: {hand_str(g['player'])} — <b>{pv}</b>\n\n"
        f"Что делаешь?"
    )
    await edit(c, text, bj_menu())
    await c.answer()


@dp.callback_query(F.data == "bj_stand")
async def bj_stand(c: CallbackQuery):
    g = bj_games.get(c.from_user.id)
    if not g or not g['active']:
        await c.answer("Игра не активна", show_alert=True)
        return

    while hand_value(g['dealer']) < 17:
        g['dealer'].append(g['deck'].pop())

    g['active'] = False
    pv = hand_value(g['player'])
    dv = hand_value(g['dealer'])

    if dv > 21 or pv > dv:
        win = int(g['bet'] * 2)
        update_balance(c.from_user.id, win)
        record_game(c.from_user.id, g['bet'], win)
        result = f"🎉 <b>ПОБЕДА!</b> +{fmt(win)}"
    elif pv == dv:
        update_balance(c.from_user.id, g['bet'])
        record_game(c.from_user.id, g['bet'], 0)
        result = f"🤝 <b>Ничья.</b> Возврат {fmt(g['bet'])}"
    else:
        record_game(c.from_user.id, g['bet'], 0)
        result = f"😢 <b>Проигрыш.</b> -{fmt(g['bet'])}"

    u = get_user(c.from_user.id)
    text = (
        f"🃏 <b>ИТОГ</b>\n\n"
        f"🤖 Дилер: {hand_str(g['dealer'])} — <b>{dv}</b>\n"
        f"👤 Ты: {hand_str(g['player'])} — <b>{pv}</b>\n\n"
        f"{result}\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    del bj_games[c.from_user.id]
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 💣 МИНЫ
# ============================================================
@dp.callback_query(F.data == "mines")
async def cb_mines(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"💣 <b>МИНЫ</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n\n"
        f"Сетка 5×5, 3 мины. Открывай клетки,\n"
        f"множитель растёт. Забери выигрыш — или взорвёшься!\n\n"
        f"Выбери ставку:"
    )
    await edit(c, text, bet_menu("mines", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_mines_"))
async def mines_start(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    update_balance(c.from_user.id, -bet)

    mines_games[c.from_user.id] = {
        'mines': mines_new_game(),
        'opened': set(),
        'bet': bet,
        'finished': False
    }
    g = mines_games[c.from_user.id]
    text = (
        f"💣 <b>МИНЫ</b>\n\n"
        f"💰 Ставка: <b>{fmt(bet)}</b>\n"
        f"🎯 Открыто: <b>0</b>\n"
        f"💎 Множитель: <b>x1.00</b>\n\n"
        f"Открывай клетки!"
    )
    await edit(c, text, mines_grid_buttons(g, g['opened'], g['mines']))
    await c.answer()


@dp.callback_query(F.data.startswith("mines_open_"))
async def mines_open(c: CallbackQuery):
    g = mines_games.get(c.from_user.id)
    if not g or g['finished']:
        await c.answer("Игра не активна", show_alert=True)
        return

    idx = int(c.data.split("_")[2])

    if idx in g['opened']:
        await c.answer("Уже открыто!")
        return

    if idx in g['mines']:
        # Взорвались
        g['finished'] = True
        record_game(c.from_user.id, g['bet'], 0)
        u = get_user(c.from_user.id)
        text = (
            f"💥 <b>ВЗРЫВ!</b>\n\n"
            f"💰 Потеряно: <b>-{fmt(g['bet'])}</b>\n\n"
            f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
        )
        await edit(c, text, back_menu())
        await c.answer()
        del mines_games[c.from_user.id]
        return

    g['opened'].add(idx)
    mult = mines_multiplier(len(g['opened']), 3)
    potential = int(g['bet'] * mult)

    text = (
        f"💣 <b>МИНЫ</b>\n\n"
        f"💰 Ставка: <b>{fmt(g['bet'])}</b>\n"
        f"🎯 Открыто: <b>{len(g['opened'])}</b>\n"
        f"💎 Множитель: <b>x{mult}</b>\n"
        f"💵 Можешь забрать: <b>{fmt(potential)}</b>\n\n"
        f"Продолжаешь?"
    )
    await edit(c, text, mines_grid_buttons(g, g['opened'], g['mines']))
    await c.answer()


@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(c: CallbackQuery):
    g = mines_games.get(c.from_user.id)
    if not g or g['finished'] or not g['opened']:
        await c.answer("Нечего забирать", show_alert=True)
        return

    mult = mines_multiplier(len(g['opened']), 3)
    win = int(g['bet'] * mult)
    update_balance(c.from_user.id, win)
    record_game(c.from_user.id, g['bet'], win)
    g['finished'] = True

    u = get_user(c.from_user.id)
    text = (
        f"💰 <b>ЗАБРАЛ!</b>\n\n"
        f"🎯 Открыто: <b>{len(g['opened'])}</b>\n"
        f"💎 Множитель: <b>x{mult}</b>\n"
        f"💰 Выигрыш: <b>+{fmt(win)}</b>\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    del mines_games[c.from_user.id]
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# ЗАПУСК
# ============================================================
async def main():
    init_db()
    print("🎰 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
