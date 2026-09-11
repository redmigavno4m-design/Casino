# -*- coding: utf-8 -*-
"""
🎰 CASINO ROYALE 5.0 — Полный Telegram-бот
С реалистичными анимациями, покером, дуэлями, чатом и графиком
"""
import asyncio
import time
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import (
    BOT_TOKEN, DAILY_BONUS, WHEEL_PRIZES, WHEEL_COOLDOWN,
    POKER_RAKE, PROMOCODES
)
from database import (
    init_db, get_user, update_balance, record_game,
    update_daily_bonus, update_wheel_time, unlock_achievement,
    set_quests, top_players
)
from games import (
    play_slots, play_roulette, play_dice, play_coin,
    mines_new_game, mines_multiplier, spin_wheel,
    ACHIEVEMENTS, check_achievements, get_level, generate_quests
)
from poker import (
    new_game as poker_new_game, best_hand, compare,
    advance_phase, dealer_action, hand_str, card_str
)
from duel import create_duel, attack as duel_attack, defend as duel_defend, active_duels
from dice_anim import roll_real_dice, animate_slots, animate_roulette, animate_coin
from graph import make_balance_graph
from promo import activate as promo_activate
from keyboards import (
    main_menu, back_menu, bet_menu, bj_menu, mines_grid_buttons
)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилища активных игр в памяти
bj_games = {}
mines_games = {}
poker_games = {}


# ============================================================
# УТИЛИТЫ
# ============================================================
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
# START
# ============================================================
@dp.message(CommandStart())
async def start(m: Message):
    u = get_user(m.from_user.id, m.from_user.username, m.from_user.first_name)
    lvl_i, lvl_name, _, _ = get_level(u['xp'])
    text = (
        f"🎰 <b>CASINO ROYALE 5.0</b>\n\n"
        f"{header(u)}"
        f"🏅 Уровень: <b>{lvl_name}</b>\n"
        f"⚡ Опыт: <b>{u['xp']}</b>\n"
        f"🎮 Игр: <b>{u['games']}</b> | 🏆 Побед: <b>{u['wins']}</b>\n\n"
        f"Выбирай игру!"
    )
    await m.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@dp.message(Command("promo"))
async def cmd_promo(m: Message):
    """Использование: /promo CODE"""
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("📝 Используй: <code>/promo КОД</code>", parse_mode="HTML")
        return
    code = parts[1]
    ok, amount, msg = promo_activate(m.from_user.id, code)
    if ok:
        update_balance(m.from_user.id, amount)
        u = get_user(m.from_user.id)
        await m.answer(
            f"🎁 <b>Промокод активирован!</b>\n\n"
            f"💰 {msg}\n"
            f"💼 Баланс: <b>{fmt(u['balance'])}</b>",
            parse_mode="HTML"
        )
    else:
        await m.answer(msg)


@dp.message(Command("balance"))
async def cmd_balance(m: Message):
    u = get_user(m.from_user.id)
    await m.answer(f"💰 Баланс: <b>{fmt(u['balance'])}</b>", parse_mode="HTML")


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================
@dp.callback_query(F.data == "main_menu")
async def cb_main(c: CallbackQuery):
    u = get_user(c.from_user.id)
    lvl_i, lvl_name, _, _ = get_level(u['xp'])
    text = (
        f"🎰 <b>CASINO ROYALE 5.0</b>\n\n"
        f"{header(u)}"
        f"🏅 <b>{lvl_name}</b> | ⚡ {u['xp']} XP\n\n"
        f"Выбирай игру:"
    )
    await edit(c, text, main_menu())
    await c.answer()


@dp.callback_query(F.data == "noop")
async def cb_noop(c: CallbackQuery):
    await c.answer("Возьми бонус 🎁", show_alert=True)


# ============================================================
# ПРОФИЛЬ / ТОП / АЧИВКИ / БОНУС / КВЕСТЫ
# ============================================================
@dp.callback_query(F.data == "profile")
async def cb_profile(c: CallbackQuery):
    u = get_user(c.from_user.id)
    wr = (u['wins'] / u['games'] * 100) if u['games'] else 0
    lvl_i, lvl_name, xp_next, _ = get_level(u['xp'])
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n"
        f"🏅 Уровень: <b>{lvl_name}</b>\n"
        f"⚡ Опыт: <b>{u['xp']}</b>\n"
        f"🎮 Игр: <b>{u['games']}</b>\n"
        f"🏆 Побед: <b>{u['wins']}</b>\n"
        f"📊 Винрейт: <b>{wr:.1f}%</b>\n"
        f"🔥 Макс. серия: <b>{u['max_streak']}</b>\n"
        f"💎 Рекорд: <b>{fmt(u['biggest_win'])}</b>\n"
        f"📈 Выиграно: <b>{fmt(u['total_won'])}</b>\n"
        f"📉 Проиграно: <b>{fmt(u['total_lost'])}</b>\n"
        f"🏆 Ачивки: <b>{len(u['achievements'])}/{len(ACHIEVEMENTS)}</b>"
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
        text += f"{mark} <b>{q['text']}</b>\n"
        text += f"   {q['progress']}/{q['target']} | 🎁 {q['reward']}$\n\n"
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
        text = f"🎡 <b>Колесо фортуны</b>\n\n⏳ Через <b>{w//3600}ч {(w%3600)//60}м</b>"
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

    # Анимация "рулетки" через редактирование
    for i in range(6):
        marker = "◀️"
        bar = "🎁 " * (i % 3) + marker + " " + "🎁 " * (2 - i % 3)
        try:
            await c.message.edit_text(
                f"🎡 <b>Крутится...</b>\n\n{bar}",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await asyncio.sleep(0.3)

    update_balance(c.from_user.id, prize)
    update_wheel_time(c.from_user.id)
    u = get_user(c.from_user.id)

    text = f"🎉 <b>ВЫПАЛО: {prize}$!</b>\n\n{header(u)}"
    await edit(c, text, back_menu())
    await c.answer(f"🎉 +{prize}$", show_alert=True)
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🎰 СЛОТЫ (с анимацией)
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

    # Анимация через редактирование
    msg = await c.message.edit_text("🎰 <b>Крутим барабаны...</b>", parse_mode="HTML")
    await animate_slots(bot, c.message.chat.id, msg.message_id, reels)

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
    await c.message.edit_text(text, reply_markup=bet_menu("slots", u['balance']), parse_mode="HTML")
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🎡 РУЛЕТКА (с анимацией)
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

    # Анимация колеса
    msg = await c.message.edit_text("🎡 <b>Крутится колесо...</b>", parse_mode="HTML")
    await animate_roulette(bot, c.message.chat.id, msg.message_id, n)

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
# 🎲 КОСТИ (настоящий Telegram Dice!)
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

    # 🎲 НАСТОЯЩИЙ Telegram Dice — крутится у всех в чате!
    await c.answer()
    await c.message.answer("🎲 Бросаем кость...")
    value = await roll_real_dice(bot, c.message.chat.id, emoji="🎲")

    # Логика
    win = 0
    if pick == 'high' and value > 3:
        win = int(bet * 1.9)
    elif pick == 'low' and value < 4:
        win = int(bet * 1.9)
    elif pick == 'six' and value == 6:
        win = int(bet * 4.5)

    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)

    u = get_user(c.from_user.id)
    faces = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣"}
    result = '+' if win > 0 else '-'
    amount = win if win > 0 else bet
    text = (
        f"🎲 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Выпало: {faces[value]} <b>{value}</b>\n\n"
        f"💰 Итог: <b>{result}{fmt(amount)}</b>\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await c.message.answer(text, reply_markup=back_menu(), parse_mode="HTML")
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🪙 МОНЕТКА (с анимацией)
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

    # Анимация монетки
    msg = await c.message.edit_text("🪙 <b>Подбрасываем...</b>", parse_mode="HTML")
    await animate_coin(bot, c.message.chat.id, msg.message_id, result)

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

    from games import new_deck, hand_value
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
    from games import hand_value
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
    from games import hand_value
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
        f"Сетка 5×5, 3 мины. Открывай клетки —\n"
        f"множитель растёт. Забери выигрыш или взорвёшься!\n\n"
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
        f"💎 Множитель: <b>x1.00</b>"
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
        f"💵 Забрать: <b>{fmt(potential)}</b>"
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
# 🃏 ПОКЕР
# ============================================================
@dp.callback_query(F.data == "poker")
async def cb_poker(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🃏 <b>ТЕХАССКИЙ ХОЛДЕМ</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n\n"
        f"1-на-1 против дилера. Рейк казино: 5%.\n\n"
        f"Выбери ставку (блайнд):"
    )
    await edit(c, text, bet_menu("poker", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_poker_"))
async def poker_start(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return
    update_balance(c.from_user.id, -bet)

    game = poker_new_game(bet)
    poker_games[c.from_user.id] = game

    text = (
        f"🃏 <b>ПОКЕР</b>\n\n"
        f"🤖 Дилер: 🎴 🎴\n"
        f"👤 Ты: {hand_str(game['player'])}\n\n"
        f"💰 Банк: <b>{fmt(game['pot'])}</b>\n"
        f"📋 Фаза: <b>Префлоп</b>\n\n"
        f"Ход:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Чек", callback_data="poker_check"),
         InlineKeyboardButton(text="📞 Колл", callback_data="poker_call")],
        [InlineKeyboardButton(text="💰 Рейз", callback_data="poker_raise"),
         InlineKeyboardButton(text="🚪 Фолд", callback_data="poker_fold")],
    ])
    await edit(c, text, kb)
    await c.answer()


def poker_render(game, my_cards_hidden=False, dealer_hidden=True):
    phase_names = {'preflop': 'Префлоп', 'flop': 'Флоп',
                   'turn': 'Тёрн', 'river': 'Ривер', 'showdown': 'Шоудаун'}
    community = " ".join(card_str(c) for c in game['community']) or "—"
    dealer_cards = hand_str(game['dealer'], hidden=dealer_hidden)
    my_cards = hand_str(game['player'])
    text = (
        f"🃏 <b>ПОКЕР</b>\n\n"
        f"🤖 Дилер: {dealer_cards}\n"
        f"👤 Ты: {my_cards}\n\n"
        f"🎴 Общие: {community}\n\n"
        f"💰 Банк: <b>{fmt(game['pot'])}</b>\n"
        f"📋 Фаза: <b>{phase_names.get(game['phase'], game['phase'])}</b>\n"
    )
    return text


def poker_actions_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Чек", callback_data="poker_check"),
         InlineKeyboardButton(text="📞 Колл", callback_data="poker_call")],
        [InlineKeyboardButton(text="💰 Рейз", callback_data="poker_raise"),
         InlineKeyboardButton(text="🚪 Фолд", callback_data="poker_fold")],
    ])


@dp.callback_query(F.data == "poker_check")
async def poker_check(c: CallbackQuery):
    game = poker_games.get(c.from_user.id)
    if not game or not game['active']:
        await c.answer("Нет активной игры", show_alert=True)
        return

    # Действие дилера
    action = dealer_action(game)
    if action == 'fold':
        # Дилер сбрасывает — победа
        rake = int(game['pot'] * POKER_RAKE)
        win = game['pot'] - rake
        update_balance(c.from_user.id, win)
        record_game(c.from_user.id, game['blind'], win)
        game['active'] = False
        text = (
            f"🎉 <b>Дилер сбросил!</b>\n\n"
            f"💰 Выигрыш: <b>+{fmt(win)}</b>\n"
            f"💸 Рейк: <b>-{fmt(rake)}</b>\n\n"
            f"💼 Баланс: <b>{fmt(get_user(c.from_user.id)['balance'])}</b>"
        )
        await edit(c, text, back_menu())
        await c.answer()
        del poker_games[c.from_user.id]
        return

    # Дилер коллит или чек
    need = game['player_bet'] - game['dealer_bet']
    if need > 0:
        game['dealer_chips'] -= need
        game['dealer_bet'] += need
        game['pot'] += need
    elif action == 'raise' and game['dealer_chips'] >= 100:
        game['dealer_chips'] -= 100
        game['dealer_bet'] += 100
        game['pot'] += 100

    # Следующая улица
    phase = advance_phase(game)

    if phase == 'showdown':
        await poker_showdown(c)
        return

    text = poker_render(game) + f"\nХод: <b>Твой</b>"
    await edit(c, text, poker_actions_kb())
    await c.answer()


@dp.callback_query(F.data == "poker_call")
async def poker_call(c: CallbackQuery):
    game = poker_games.get(c.from_user.id)
    if not game or not game['active']:
        await c.answer("Нет активной игры", show_alert=True)
        return

    need = game['dealer_bet'] - game['player_bet']
    if need > 0 and game['player_chips'] >= need:
        game['player_chips'] -= need
        game['player_bet'] += need
        game['pot'] += need

    # Дилер действует
    action = dealer_action(game)
    if action == 'fold':
        rake = int(game['pot'] * POKER_RAKE)
        win = game['pot'] - rake
        update_balance(c.from_user.id, win)
        record_game(c.from_user.id, game['blind'], win)
        game['active'] = False
        text = (
            f"🎉 <b>Дилер сбросил!</b>\n\n"
            f"💰 Выигрыш: <b>+{fmt(win)}</b>\n"
            f"💸 Рейк: <b>-{fmt(rake)}</b>"
        )
        await edit(c, text, back_menu())
        await c.answer()
        del poker_games[c.from_user.id]
        return

    need2 = game['player_bet'] - game['dealer_bet']
    if need2 > 0 and game['dealer_chips'] >= need2:
        game['dealer_chips'] -= need2
        game['dealer_bet'] += need2
        game['pot'] += need2

    phase = advance_phase(game)
    if phase == 'showdown':
        await poker_showdown(c)
        return

    text = poker_render(game) + f"\nХод: <b>Твой</b>"
    await edit(c, text, poker_actions_kb())
    await c.answer()


@dp.callback_query(F.data == "poker_raise")
async def poker_raise(c: CallbackQuery):
    game = poker_games.get(c.from_user.id)
    if not game or not game['active']:
        await c.answer("Нет активной игры", show_alert=True)
        return

    raise_amt = max(game['last_raise'] * 2, 100)
    need = game['dealer_bet'] + raise_amt - game['player_bet']

    if game['player_chips'] < need:
        await c.answer("❌ Недостаточно фишек!", show_alert=True)
        return

    game['player_chips'] -= need
    game['player_bet'] += need
    game['pot'] += need
    game['last_raise'] = raise_amt

    # Дилер отвечает
    action = dealer_action(game)
    if action == 'fold':
        rake = int(game['pot'] * POKER_RAKE)
        win = game['pot'] - rake
        update_balance(c.from_user.id, win)
        record_game(c.from_user.id, game['blind'], win)
        game['active'] = False
        text = (
            f"🎉 <b>Дилер сбросил на рейз!</b>\n\n"
            f"💰 Выигрыш: <b>+{fmt(win)}</b>\n"
            f"💸 Рейк: <b>-{fmt(rake)}</b>"
        )
        await edit(c, text, back_menu())
        await c.answer()
        del poker_games[c.from_user.id]
        return

    need2 = game['player_bet'] - game['dealer_bet']
    if need2 > 0 and game['dealer_chips'] >= need2:
        game['dealer_chips'] -= need2
        game['dealer_bet'] += need2
        game['pot'] += need2

    phase = advance_phase(game)
    if phase == 'showdown':
        await poker_showdown(c)
        return

    text = poker_render(game) + f"\nХод: <b>Твой</b>"
    await edit(c, text, poker_actions_kb())
    await c.answer()


@dp.callback_query(F.data == "poker_fold")
async def poker_fold(c: CallbackQuery):
    game = poker_games.get(c.from_user.id)
    if not game or not game['active']:
        await c.answer("Нет активной игры", show_alert=True)
        return
    game['active'] = False
    record_game(c.from_user.id, game['blind'], 0)
    del poker_games[c.from_user.id]
    u = get_user(c.from_user.id)
    text = (
        f"🚪 <b>Ты сбросил.</b>\n\n"
        f"💸 Потеряно: <b>-{fmt(game['blind'])}</b>\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()


async def poker_showdown(c: CallbackQuery):
    game = poker_games.get(c.from_user.id)
    if not game:
        return
    player_best = best_hand(game['player'] + game['community'])
    dealer_best = best_hand(game['dealer'] + game['community'])
    cmp = compare(player_best, dealer_best)

    community = " ".join(card_str(c) for c in game['community'])
    dealer_cards = hand_str(game['dealer'])
    my_cards = hand_str(game['player'])

    if cmp > 0:
        rake = int(game['pot'] * POKER_RAKE)
        win = game['pot'] - rake
        update_balance(c.from_user.id, win)
        record_game(c.from_user.id, game['blind'], win)
        result = f"🏆 <b>Ты победил!</b> +{fmt(win)}\n💸 Рейк: -{fmt(rake)}"
    elif cmp < 0:
        record_game(c.from_user.id, game['blind'], 0)
        result = f"😢 <b>Дилер победил.</b> -{fmt(game['blind'])}"
    else:
        update_balance(c.from_user.id, game['blind'])
        record_game(c.from_user.id, game['blind'], 0)
        result = f"🤝 <b>Ничья.</b> Возврат {fmt(game['blind'])}"

    game['active'] = False
    u = get_user(c.from_user.id)
    text = (
        f"🃏 <b>ШОУДАУН</b>\n\n"
        f"🤖 Дилер: {dealer_cards} — <b>{dealer_best[1]}</b>\n"
        f"👤 Ты: {my_cards} — <b>{player_best[1]}</b>\n"
        f"🎴 Общие: {community}\n\n"
        f"{result}\n\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    del poker_games[c.from_user.id]
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 📊 ГРАФИК
# ============================================================
@dp.callback_query(F.data == "graph")
async def cb_graph(c: CallbackQuery):
    u = get_user(c.from_user.id)
    # Пример истории — можно заменить на реальную из БД
    # Здесь используем баланс + фейковые точки для демонстрации
    history = [1000, 1200, 900, 1500, 800, u['balance']]
    buf = make_balance_graph(history)
    if buf is None:
        await c.answer("❌ Pillow не установлен. Смотри requirements.txt", show_alert=True)
        return

    photo = BufferedInputFile(buf.read(), filename="graph.png")
    await c.message.answer_photo(
        photo,
        caption=f"📊 <b>График баланса</b>\n\n💰 Текущий: <b>{fmt(u['balance'])}</b>",
        parse_mode="HTML"
    )
    await c.answer()


# ============================================================
# 👥 ДУЭЛИ (PvP)
# ============================================================
@dp.callback_query(F.data == "duel")
async def cb_duel(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"👥 <b>ДУЭЛИ PvP</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n\n"
        f"Пригласи друга в дуэль! Победитель забирает банк.\n"
        f"Рейк казино: 5%\n\n"
        f"Выбери ставку:"
    )
    await edit(c, text, bet_menu("duel", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_duel_"))
async def duel_invite(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌ Недостаточно!", show_alert=True)
        return

    # Кнопка приглашения — отправим в чат
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⚔️ ПРИНЯТЬ ДУЭЛЬ ({fmt(bet)})",
            callback_data=f"duel_accept_{c.from_user.id}_{bet}"
        )],
    ])
    await c.message.answer(
        f"⚔️ <b>{u['first_name'] or 'Игрок'}</b> вызывает на дуэль!\n\n"
        f"💰 Ставка: <b>{fmt(bet)}</b>\n\n"
        f"Кто примет вызов?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await c.answer()


@dp.callback_query(F.data.startswith("duel_accept_"))
async def duel_accept(c: CallbackQuery):
    parts = c.data.split("_")
    challenger_id = int(parts[2])
    bet = int(parts[3])

    if c.from_user.id == challenger_id:
        await c.answer("❌ Нельзя сражаться с собой!", show_alert=True)
        return

    challenger = get_user(challenger_id)
    acceptor = get_user(c.from_user.id)

    if challenger['balance'] < bet:
        await c.answer("❌ У вызывающего недостаточно средств!", show_alert=True)
        return
    if acceptor['balance'] < bet:
        await c.answer("❌ У тебя недостаточно средств!", show_alert=True)
        return

    # Списываем ставки
    update_balance(challenger_id, -bet)
    update_balance(c.from_user.id, -bet)

    # Создаём дуэль
    chat_id = c.message.chat.id
    d = create_duel(chat_id, challenger_id, c.from_user.id, bet)

    text = (
        f"⚔️ <b>ДУЭЛЬ НАЧАЛАСЬ!</b>\n\n"
        f"🥊 <b>{challenger['first_name']}</b> — HP: 100\n"
        f"🥊 <b>{acceptor['first_name']}</b> — HP: 100\n\n"
        f"💰 Банк: <b>{fmt(bet * 2)}</b>\n"
        f"🎯 Ход: <b>{challenger['first_name']}</b>\n\n"
        f"<i>Бой идёт по очереди. Бей или защищайся!</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ АТАКА", callback_data="duel_attack"),
         InlineKeyboardButton(text="🛡️ ЗАЩИТА", callback_data="duel_defend")],
    ])
    await c.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await c.answer()


@dp.callback_query(F.data == "duel_attack")
async def duel_attack_cb(c: CallbackQuery):
    chat_id = c.message.chat.id
    d = active_duels.get(chat_id)
    if not d or not d['active']:
        await c.answer("Нет активной дуэли", show_alert=True)
        return
    if d['turn'] != c.from_user.id:
        await c.answer("⏳ Не твой ход!", show_alert=True)
        return

    result = duel_attack(chat_id, c.from_user.id)

    if 'winner' in result:
        winner = get_user(result['winner'])
        loser = get_user(result['loser'])
        pot = d['bet'] * 2
        rake = int(pot * 0.05)
        prize = pot - rake
        update_balance(result['winner'], prize)
        text = (
            f"🏆 <b>ПОБЕДА!</b>\n\n"
            f"👑 <b>{winner['first_name']}</b> выиграл!\n"
            f"💰 Приз: <b>{fmt(prize)}</b>\n"
            f"💸 Рейк: <b>-{fmt(rake)}</b>"
        )
        await c.message.answer(text, parse_mode="HTML")
        del active_duels[chat_id]
        return

    p1 = get_user(d['p1'])
    p2 = get_user(d['p2'])
    next_id = result['next']
    next_name = get_user(next_id)['first_name']

    text = (
        f"⚔️ <b>ДУЭЛЬ</b>\n\n"
        f"🥊 {p1['first_name']} — HP: <b>{d['hp'][d['p1']]}</b>\n"
        f"🥊 {p2['first_name']} — HP: <b>{d['hp'][d['p2']]}</b>\n\n"
        f"💥 Урон: <b>{result['damage']}</b>\n"
        f"🎯 Ход: <b>{next_name}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ АТАКА", callback_data="duel_attack"),
         InlineKeyboardButton(text="🛡️ ЗАЩИТА", callback_data="duel_defend")],
    ])
    await c.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await c.answer()


@dp.callback_query(F.data == "duel_defend")
async def duel_defend_cb(c: CallbackQuery):
    chat_id = c.message.chat.id
    d = active_duels.get(chat_id)
    if not d or not d['active']:
        await c.answer("Нет активной дуэли", show_alert=True)
        return
    if d['turn'] != c.from_user.id:
        await c.answer("⏳ Не твой ход!", show_alert=True)
        return

    result = duel_defend(chat_id, c.from_user.id)
    p1 = get_user(d['p1'])
    p2 = get_user(d['p2'])
    next_id = result['next']
    next_name = get_user(next_id)['first_name']

    text = (
        f"⚔️ <b>ДУЭЛЬ</b>\n\n"
        f"🥊 {p1['first_name']} — HP: <b>{d['hp'][d['p1']]}</b>\n"
        f"🥊 {p2['first_name']} — HP: <b>{d['hp'][d['p2']]}</b>\n\n"
        f"🛡️ Защита! Урон: <b>{result['damage']}</b>\n"
        f"🎯 Ход: <b>{next_name}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ АТАКА", callback_data="duel_attack"),
         InlineKeyboardButton(text="🛡️ ЗАЩИТА", callback_data="duel_defend")],
    ])
    await c.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await c.answer()

# ============================================================
# 💰 МАГАЗИН И ПЛАТЕЖИ
# ============================================================
from wallet import buy_crystals, exchange_crystals, format_crystals
from payments import (
    send_stars_invoice, create_yookassa_payment,
    check_yookassa_payment, format_pack,
    format_price_stars, format_price_rub
)
from config import CRYSTAL_PACKS, CRYSTAL_TO_MONEY
from aiogram.types import PreCheckoutQuery, LabeledPrice


@dp.callback_query(F.data == "shop")
async def cb_shop(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"💎 <b>МАГАЗИН КРИСТАЛЛОВ</b>\n\n"
        f"💰 Игровой баланс: <b>{fmt(u['balance'])}</b>\n"
        f"💎 Кристаллов: <b>{u['crystals']}</b>\n\n"
        f"💱 Курс: <b>1💎 = {CRYSTAL_TO_MONEY}$</b>\n\n"
        f"Выбери пакет:"
    )
    rows = []
    for i, (crystals, stars, rub, bonus) in enumerate(CRYSTAL_PACKS):
        total = crystals + int(crystals * bonus / 100)
        bonus_str = f" +{bonus}%" if bonus else ""
        rows.append([
            InlineKeyboardButton(
                text=f"💎 {total}{bonus_str} — {stars}⭐ / {rub}₽",
                callback_data=f"pack_{i}"
            )
        ])
    rows.append([InlineKeyboardButton(text="💱 Обменять кристаллы", callback_data="exchange")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data.startswith("pack_"))
async def cb_pack(c: CallbackQuery):
    idx = int(c.data.split("_")[1])
    u = get_user(c.from_user.id)
    text = (
        f"💎 <b>{format_pack(idx)}</b>\n\n"
        f"⭐ Stars: <b>{format_price_stars(idx)}</b>\n"
        f"💳 Карта: <b>{format_price_rub(idx)}</b>\n\n"
        f"Как оплатить?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ Оплатить Stars ({format_price_stars(idx)})",
                              callback_data=f"pay_stars_{idx}")],
        [InlineKeyboardButton(text=f"💳 Оплатить картой ({format_price_rub(idx)})",
                              callback_data=f"pay_yoo_{idx}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="shop")],
    ])
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data.startswith("pay_stars_"))
async def cb_pay_stars(c: CallbackQuery):
    idx = int(c.data.split("_")[2])
    await c.answer("⭐ Отправляю счёт...")
    try:
        await send_stars_invoice(bot, c.from_user.id, idx)
    except Exception as e:
        await c.message.answer(f"❌ Ошибка: {e}")


@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    """Подтверждение оплаты Stars"""
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def on_successful_payment(m: Message):
    """Успешная оплата — начисляем кристаллы"""
    payload = m.successful_payment.invoice_payload  # stars_0_10
    parts = payload.split("_")
    total_crystals = int(parts[2])
    amount_stars = m.successful_payment.total_amount

    buy_crystals(m.from_user.id, total_crystals, 'stars', m.successful_payment.telegram_payment_charge_id)
    u = get_user(m.from_user.id)

    await m.answer(
        f"🎉 <b>Оплата прошла!</b>\n\n"
        f"💎 Получено: <b>+{total_crystals} кристаллов</b>\n"
        f"⭐ Списано: <b>{amount_stars} Stars</b>\n\n"
        f"💼 Всего кристаллов: <b>{u['crystals']}</b>",
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("pay_yoo_"))
async def cb_pay_yoo(c: CallbackQuery):
    idx = int(c.data.split("_")[2])
    await c.answer("💳 Создаю платёж...")

    return_url = f"https://t.me/{(await bot.get_me()).username}"
    payment_id, url = await create_yookassa_payment(c.from_user.id, idx, return_url)

    if not payment_id:
        await c.message.answer(
            "❌ ЮKassa не настроена.\n\n"
            "Проверь SHOP_ID и SECRET_KEY в config.py."
        )
        return

    crystals, stars, rub, bonus = CRYSTAL_PACKS[idx]
    total = crystals + int(crystals * bonus / 100)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Перейти к оплате", url=url)],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_yoo_{payment_id}_{total}")],
    ])
    await c.message.edit_text(
        f"💳 <b>Оплата картой</b>\n\n"
        f"💎 {total} кристаллов\n"
        f"💰 Сумма: <b>{rub}₽</b>\n\n"
        f"После оплаты нажми «Проверить оплату».",
        reply_markup=kb,
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("check_yoo_"))
async def cb_check_yoo(c: CallbackQuery):
    parts = c.data.split("_")
    payment_id = parts[2]
    crystals = int(parts[3])

    status = await check_yookassa_payment(payment_id)

    if status == 'succeeded':
        # Проверим, не начисляли ли уже
        # (упрощённо — просто начисляем)
        buy_crystals(c.from_user.id, crystals, 'yookassa', payment_id)
        u = get_user(c.from_user.id)
        await c.answer(f"✅ +{crystals}💎!", show_alert=True)
        await c.message.edit_text(
            f"🎉 <b>Оплата прошла!</b>\n\n"
            f"💎 Получено: <b>+{crystals} кристаллов</b>\n\n"
            f"💼 Всего: <b>{u['crystals']}</b>",
            reply_markup=back_menu(),
            parse_mode="HTML"
        )
    elif status == 'pending':
        await c.answer("⏳ Платёж ещё не завершён", show_alert=True)
    else:
        await c.answer(f"❌ Статус: {status}", show_alert=True)


@dp.callback_query(F.data == "exchange")
async def cb_exchange(c: CallbackQuery):
    u = get_user(c.from_user.id)
    if u['crystals'] < 1:
        await c.answer("❌ У тебя нет кристаллов", show_alert=True)
        return
    text = (
        f"💱 <b>ОБМЕН КРИСТАЛЛОВ</b>\n\n"
        f"💎 У тебя: <b>{u['crystals']}</b>\n"
        f"💱 Курс: <b>1💎 = {CRYSTAL_TO_MONEY}$</b>\n"
        f"💰 Можно получить: <b>{u['crystals'] * CRYSTAL_TO_MONEY}$</b>\n\n"
        f"Обменять все?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💱 Обменять все ({u['crystals']}💎)",
                              callback_data="exchange_all")],
        [InlineKeyboardButton(text="⬅️ В магазин", callback_data="shop")],
    ])
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data == "exchange_all")
async def cb_exchange_all(c: CallbackQuery):
    u = get_user(c.from_user.id)
    if u['crystals'] < 1:
        await c.answer("❌ Нет кристаллов", show_alert=True)
        return
    ok, money = exchange_crystals(c.from_user.id, u['crystals'])
    if ok:
        u2 = get_user(c.from_user.id)
        await c.answer(f"💱 +{fmt(money)}!", show_alert=True)
        await edit(c,
                   f"✅ <b>Обмен выполнен!</b>\n\n"
                   f"💎 Обменяно: <b>{u['crystals']}</b>\n"
                   f"💰 Получено: <b>+{fmt(money)}</b>\n\n"
                   f"💼 Баланс: <b>{fmt(u2['balance'])}</b>",
                   back_menu())
    else:
        await c.answer("❌ Ошибка", show_alert=True)

# ============================================================
# ЗАПУСК
# ============================================================
async def main():
    init_db()
    print("🎰 CASINO ROYALE 5.0 запущен!")
    print("✅ Анимации: слоты, рулетка, кости (Telegram Dice), монетка")
    print("✅ Игры: слоты, рулетка, кости, монетка, блэкджек, мины, покер")
    print("✅ Фичи: достижения, квесты, колесо, дуэли, промокоды, график")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
