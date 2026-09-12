# -*- coding: utf-8 -*-
"""
🎰 CASINO ROYALE 8.0 — Полная версия
"""
import asyncio
import time
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    PreCheckoutQuery, BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ============ ИМПОРТЫ ИЗ НАШИХ МОДУЛЕЙ ============
from config import (
    BOT_TOKEN, DAILY_BONUS, WHEEL_PRIZES, WHEEL_COOLDOWN,
    ADMIN_IDS, REFERRAL_BONUS_NEW, REFERRAL_BONUS_INVITER,
    TOURNAMENT_ENTRY, CRYSTAL_TO_MONEY, MONEY_TO_CRYSTAL,
    CRYSTAL_PACKS, SUPPORTED_LANGS, MANUAL_CRYSTAL_PACKS
)
from database import (
    init_db, get_user, update_balance, record_game, update_daily_bonus,
    update_wheel_time, unlock_achievement, set_quests, top_players,
    set_language, register_referral, admin_stats, admin_give,
    admin_broadcast_users, make_promo, use_promo, update_crystals,
    list_withdrawals, get_withdrawal, update_withdrawal,
    user_withdrawals, total_withdrawn, pending_withdrawals_count,
    get_user as get_user_db
)
from games import (
    play_slots, play_roulette, play_dice, play_coin,
    mines_new_game, mines_multiplier, spin_wheel,
    ACHIEVEMENTS, check_achievements, get_level, generate_quests
)
from games2 import (
    vslot_spin, american_roulette, mini_roulette,
    craps_check_pass, sickbo_roll, hilo_dice,
    keno_play, crash_generate, scratch_card
)
from sport import (
    play_darts, play_football, play_basketball, play_bowling, play_slot_dice
)
from dice_anim import animate_slots
from graph import make_balance_graph
from promo import activate as promo_activate
from payments import send_stars_invoice
from payments2 import create_crypto_invoice, check_crypto_invoice, manual_payment_text
from wallet import buy_crystals, exchange_crystals
from social import (
    get_referral_link, referral_stats, get_active_tournament,
    join_tournament, is_in_tournament, tournament_top
)
from lang import lang_name
from help_text import (
    get_help, get_faq, search_games,
    HELP_CATEGORIES, FAQ_CATEGORIES
)
from admin_panel import (
    get_house_stats, get_top_by_profit, get_inactive_users
)
from dynamic_odds import apply_dynamic_odds
from vip_system import get_vip_level, give_cashback, get_vip_progress
from marketing import get_random_promo, get_inactive_reminder
from middlewares import AntiSpamMiddleware
from withdraw import (
    calc_payout, validate_withdraw, request_withdraw,
    withdraw_info_text, status_emoji, status_name
)
from keyboards import (
    main_menu, back_menu, bet_menu, mines_grid_buttons,
    sport_choice, sport_bet_menu, help_menu, lang_menu,
    withdraw_methods_menu, withdraw_amount_menu, admin_withdrawals_menu
)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============ ИГРЫ В ПАМЯТИ ============
bj_games = {}
mines_games = {}
craps_games = {}
keno_picks = {}
crash_games = {}


# ============ FSM ============
class SportBet(StatesGroup):
    waiting_amount = State()
    game_type = State()
    bet_type = State()


class HelpStates(StatesGroup):
    waiting_search = State()


class WithdrawState(StatesGroup):
    waiting_amount = State()
    waiting_wallet = State()


# ============ УТИЛИТЫ ============
def fmt(amount):
    return f"{int(amount):,}".replace(",", " ") + "$"


def header(u):
    return f"👤 <b>{u['first_name'] or 'Игрок'}</b>\n💰 Баланс: <b>{fmt(u['balance'])}</b>\n"


async def edit(call, text, kb=None):
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        try:
            await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass


async def notify_achievements(message, user_id):
    u = get_user(user_id)
    new_ach = check_achievements(u)
    for aid in new_ach:
        if unlock_achievement(user_id, aid):
            icon, name, _ = ACHIEVEMENTS[aid]
            try:
                await message.answer(f"🏆 <b>ДОСТИЖЕНИЕ!</b>\n{icon} <b>{name}</b>", parse_mode="HTML")
            except Exception:
                pass


# ============================================================
# СТАРТ
# ============================================================
@dp.message(CommandStart())
async def start(m: Message, command: CommandObject = None):
    # Реферальная ссылка
    if command and command.args and command.args.startswith("ref_"):
        try:
            ref_id = int(command.args[4:])
            if register_referral(m.from_user.id, ref_id):
                update_balance(m.from_user.id, REFERRAL_BONUS_NEW)
                update_balance(ref_id, REFERRAL_BONUS_INVITER)
                try:
                    await bot.send_message(
                        ref_id,
                        f"🎁 <b>Новый реферал!</b>\n+{fmt(REFERRAL_BONUS_INVITER)}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    u = get_user(m.from_user.id, m.from_user.username, m.from_user.first_name)
    if u.get('banned'):
        await m.answer("🚫 Ты заблокирован.")
        return

    lvl_i, lvl_name, _, _ = get_level(u['xp'])

    # Проверка возврата
    now = int(time.time())
    days_inactive = (now - u['last_bonus']) // 86400 if u['last_bonus'] else 0

    if days_inactive >= 7 and u['games'] > 0:
        bonus = 500
        update_balance(m.from_user.id, bonus)
        await m.answer(
            f"🎉 <b>С ВОЗВРАЩЕНИЕМ!</b>\n\n"
            f"Тебя не было {days_inactive} дней.\n"
            f"🎁 Бонус: <b>+{fmt(bonus)}</b>!\n\n"
            f"Уровень: <b>{lvl_name}</b>",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
        return

    text = (
        f"🎰 <b>CASINO ROYALE 8.0</b>\n\n"
        f"{header(u)}"
        f"🏅 Уровень: <b>{lvl_name}</b>\n"
        f"💎 Кристаллы: <b>{u['crystals']}</b>\n"
        f"🎮 Игр: <b>{u['games']}</b> | 🏆 Побед: <b>{u['wins']}</b>\n\n"
        f"Выбирай игру!"
    )
    await m.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@dp.message(Command("balance"))
async def cmd_balance(m: Message):
    u = get_user(m.from_user.id)
    await m.answer(
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n"
        f"💎 Кристаллы: <b>{u['crystals']}</b>",
        parse_mode="HTML"
    )


@dp.message(Command("promo"))
async def cmd_promo(m: Message):
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("📝 /promo КОД")
        return
    code = parts[1]

    # Сначала БД промокодов
    amount = use_promo(m.from_user.id, code)
    if amount:
        u = get_user(m.from_user.id)
        await m.answer(
            f"🎁 Промокод активирован! +{fmt(amount)}\n\n"
            f"💼 Баланс: <b>{fmt(u['balance'])}</b>",
            parse_mode="HTML"
        )
        return

    # Статичные промокоды
    ok, amount, msg = promo_activate(m.from_user.id, code)
    if ok:
        update_balance(m.from_user.id, amount)
        u = get_user(m.from_user.id)
        await m.answer(
            f"🎁 {msg}\n\n💼 Баланс: <b>{fmt(u['balance'])}</b>",
            parse_mode="HTML"
        )
    else:
        await m.answer(msg)


@dp.message(Command("ref"))
async def cmd_ref(m: Message):
    me = await bot.get_me()
    link = get_referral_link(me.username, m.from_user.id)
    count, earnings = referral_stats(m.from_user.id)
    text = (
        f"🎁 <b>РЕФЕРАЛЫ</b>\n\n"
        f"За друга: <b>+{fmt(REFERRAL_BONUS_INVITER)}</b>\n"
        f"Ты получаешь <b>5%</b> с его проигрышей\n\n"
        f"<code>{link}</code>\n\n"
        f"👥 Приглашено: <b>{count}</b>\n"
        f"💰 Заработано: <b>{fmt(earnings)}</b>"
    )
    await m.answer(text, parse_mode="HTML")


@dp.message(Command("vip"))
async def cmd_vip(m: Message):
    lvl, name, cb = get_vip_level(m.from_user.id)
    curr, cn, nn, prog = get_vip_progress(m.from_user.id)
    u = get_user(m.from_user.id)
    bar_len = 10
    filled = int(prog / 100 * bar_len) if prog else 0
    bar = "▰" * filled + "▱" * (bar_len - filled)
    text = (
        f"👑 <b>VIP-СТАТУС</b>\n\n"
        f"Уровень: <b>{name}</b>\n"
        f"💰 Проиграно: <b>{fmt(u['total_lost'])}</b>\n"
        f"💵 Кэшбэк: <b>{cb}%</b>\n\n"
    )
    if nn:
        text += f"До <b>{nn}</b>: {prog:.1f}%\n{bar}\n"
    await m.answer(text, parse_mode="HTML")


@dp.message(Command("cashback"))
async def cmd_cashback(m: Message):
    amount = give_cashback(m.from_user.id)
    if amount > 0:
        u = get_user(m.from_user.id)
        await m.answer(
            f"💵 <b>КЭШБЭК</b>\n\nНачислено: <b>+{fmt(amount)}</b>\n\n"
            f"💼 Баланс: <b>{fmt(u['balance'])}</b>",
            parse_mode="HTML"
        )
    else:
        await m.answer("💵 Кэшбэк пока 0$")


@dp.message(Command("lang"))
async def cmd_lang(m: Message):
    await m.answer("🌍 Выбери язык:", reply_markup=lang_menu())


@dp.message(Command("help"))
async def cmd_help(m: Message):
    parts = m.text.split(maxsplit=1)
    if len(parts) > 1:
        query = parts[1].strip()
        results = search_games(query)
        if not results:
            await m.answer(f"🔍 Ничего не найдено: {query}")
            return
        if len(results) == 1:
            key = results[0][0]
            text, preview, gif = get_help(key)
            if text:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎮 Играть", callback_data=key)],
                    [InlineKeyboardButton(text="⬅️ К списку", callback_data="help")],
                ])
                await m.answer(text, reply_markup=kb, parse_mode="HTML")
            return
        await m.answer(f"🔍 Найдено: {len(results)}", reply_markup=help_menu(query), parse_mode="HTML")
        return

    text = "📚 <b>ПОМОЩЬ</b>\n\n🎮 Выбери игру:"
    await m.answer(text, reply_markup=help_menu(), parse_mode="HTML")


@dp.message(Command("tutorial"))
async def cmd_tutorial(m: Message):
    text = (
        "🎓 <b>ОБУЧЕНИЕ</b>\n\n"
        "🎰 Выбирай игру из меню\n"
        "💰 Ставь сумму\n"
        "🎲 Смотри результат\n\n"
        "🎁 Получи <b>+500$</b> за прохождение!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Получить 500$", callback_data="tutorial_freespins")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")],
    ])
    await m.answer(text, reply_markup=kb, parse_mode="HTML")


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================
@dp.callback_query(F.data == "main_menu")
async def cb_main(c: CallbackQuery):
    u = get_user(c.from_user.id)
    lvl_i, lvl_name, _, _ = get_level(u['xp'])
    text = (
        f"🎰 <b>CASINO ROYALE 8.0</b>\n\n"
        f"{header(u)}"
        f"🏅 <b>{lvl_name}</b> | ⚡ {u['xp']} XP\n"
        f"💎 Кристаллы: <b>{u['crystals']}</b>\n\n"
        f"Выбирай игру:"
    )
    await edit(c, text, main_menu())
    await c.answer()


@dp.callback_query(F.data == "noop")
async def cb_noop(c: CallbackQuery):
    await c.answer("🎁 Возьми бонус", show_alert=True)


@dp.callback_query(F.data == "tutorial_freespins")
async def cb_tutorial(c: CallbackQuery):
    u = get_user(c.from_user.id)
    if 'tutorial' in u['achievements']:
        await c.answer("🎁 Уже получил!", show_alert=True)
        return
    update_balance(c.from_user.id, 500)
    unlock_achievement(c.from_user.id, 'tutorial')
    u2 = get_user(c.from_user.id)
    await c.answer("🎉 +500$!", show_alert=True)
    await edit(c,
        f"🎁 <b>+500$!</b>\n\n💼 Баланс: <b>{fmt(u2['balance'])}</b>",
        back_menu())


# ============================================================
# ПРОФИЛЬ / ТОП / АЧИВКИ / БОНУС / КВЕСТЫ
# ============================================================
@dp.callback_query(F.data == "profile")
async def cb_profile(c: CallbackQuery):
    u = get_user(c.from_user.id)
    wr = (u['wins'] / u['games'] * 100) if u['games'] else 0
    lvl_i, lvl_name, _, _ = get_level(u['xp'])
    vip_i, vip_name, vip_cb = get_vip_level(c.from_user.id)
    total_wd = total_withdrawn(c.from_user.id)
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n"
        f"💎 Кристаллы: <b>{u['crystals']}</b>\n"
        f"🏅 Уровень: <b>{lvl_name}</b>\n"
        f"👑 VIP: <b>{vip_name}</b>\n"
        f"⚡ XP: <b>{u['xp']}</b>\n"
        f"🎮 Игр: <b>{u['games']}</b>\n"
        f"🏆 Побед: <b>{u['wins']}</b>\n"
        f"📊 Винрейт: <b>{wr:.1f}%</b>\n"
        f"🔥 Серия: <b>{u['max_streak']}</b>\n"
        f"💎 Рекорд: <b>{fmt(u['biggest_win'])}</b>\n"
        f"📈 Всего выиграно: <b>{fmt(u['total_won'])}</b>\n"
        f"📉 Проиграно: <b>{fmt(u['total_lost'])}</b>\n"
        f"💸 Выведено: <b>{total_wd}💎</b>\n"
        f"🏆 Ачивок: <b>{len(u['achievements'])}/{len(ACHIEVEMENTS)}</b>"
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
        q = generate_quests()
        set_quests(c.from_user.id, q)
        u = get_user(c.from_user.id)
    text = "🎯 <b>КВЕСТЫ</b>\n\n"
    for qid, q in u['daily_quests'].items():
        mark = "✅" if q['done'] else "▶️"
        text += f"{mark} <b>{q['text']}</b>\n{q['progress']}/{q['target']} | 🎁 {q['reward']}$\n\n"
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
        text = f"🎡 Через <b>{w//3600}ч {(w%3600)//60}м</b>"
        await edit(c, text, back_menu())
        await c.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎡 КРУТИТЬ!", callback_data="wheel_spin")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")],
    ])
    await edit(c, f"🎡 <b>КОЛЕСО ФОРТУНЫ</b>\n\nПризы: {WHEEL_PRIZES}", kb)
    await c.answer()


@dp.callback_query(F.data == "wheel_spin")
async def cb_wheel_spin(c: CallbackQuery):
    u = get_user(c.from_user.id)
    if int(time.time()) - u['last_wheel'] < WHEEL_COOLDOWN:
        await c.answer("⏳ Уже крутил!")
        return
    idx, prize = spin_wheel(WHEEL_PRIZES)
    for i in range(5):
        try:
            await c.message.edit_text(f"🎡 Крутится... {'🎁' * (i+1)}", parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.3)
    update_balance(c.from_user.id, prize)
    update_wheel_time(c.from_user.id)
    u = get_user(c.from_user.id)
    await edit(c, f"🎉 <b>+{fmt(prize)}</b>!\n\n{header(u)}", back_menu())
    await c.answer(f"+{prize}$", show_alert=True)


# ============================================================
# 🎰 СЛОТЫ
# ============================================================
@dp.callback_query(F.data == "slots")
async def cb_slots(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🎰 <b>СЛОТЫ</b>\n\n"
        f"💰 {fmt(u['balance'])}\n\n"
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
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    bar = " | ".join(reels)
    s = '+' if win > 0 else '-'
    amt = win if win > 0 else bet
    text = (
        f"🎰 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"<code>{bar}</code>\n\n"
        f"{desc}\n"
        f"💰 Итог: <b>{s}{fmt(amt)}</b>\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, bet_menu("slots", u['balance']))
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🎰 ВИДЕО-СЛОТЫ
# ============================================================
@dp.callback_query(F.data == "vslot")
async def cb_vslot(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🎰 <b>ВИДЕО-СЛОТЫ 5×3</b>\n\n"
        f"💰 {fmt(u['balance'])}\n\n"
        f"5 барабанов. Выигрыш по центру. 3+ ⭐ → фриспины!\n\n"
        f"Выбери ставку:"
    )
    await edit(c, text, bet_menu("vslot", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_vslot_"))
async def vslot_play(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    win, grid, fs, desc = vslot_spin(bet)
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    g = ""
    for r in range(3):
        row = " ".join(grid[c][r] for c in range(5))
        g += f"<code>{row}</code>{' ⬅️' if r == 1 else ''}\n"
    s = '+' if win > 0 else '-'
    text = (
        f"🎰 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"{g}\n"
        f"{desc}\n"
        f"💰 Итог: <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, bet_menu("vslot", u['balance']))
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🎡 РУЛЕТКИ
# ============================================================
@dp.callback_query(F.data.in_({"roulette", "aroulette", "mroulette"}))
async def cb_roulette(c: CallbackQuery):
    u = get_user(c.from_user.id)
    game = c.data
    names = {'roulette': 'РУЛЕТКА', 'aroulette': 'АМЕРИКАНСКАЯ РУЛЕТКА', 'mroulette': 'МИНИ-РУЛЕТКА'}
    await edit(c, f"🎡 <b>{names[game]}</b>\n\n💰 {fmt(u['balance'])}", bet_menu(game, u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_roulette_"))
@dp.callback_query(F.data.startswith("bet_aroulette_"))
@dp.callback_query(F.data.startswith("bet_mroulette_"))
async def roulette_bet(c: CallbackQuery):
    parts = c.data.split("_")
    if parts[1] == "roulette":
        game, bet = "roulette", int(parts[2])
    elif parts[1] == "aroulette":
        game, bet = "aroulette", int(parts[2])
    else:
        game, bet = "mroulette", int(parts[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    pre = {'roulette': 'rs', 'aroulette': 'ar', 'mroulette': 'mr'}[game]

    if game == 'aroulette':
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Красное x2", callback_data=f"{pre}_{bet}_red"),
             InlineKeyboardButton(text="⚫ Чёрное x2", callback_data=f"{pre}_{bet}_black")],
            [InlineKeyboardButton(text="🟢 Зелёное x17", callback_data=f"{pre}_{bet}_green")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=game)],
        ])
    elif game == 'mroulette':
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Красное x2", callback_data=f"{pre}_{bet}_red"),
             InlineKeyboardButton(text="⚫ Чёрное x2", callback_data=f"{pre}_{bet}_black")],
            [InlineKeyboardButton(text="🟢 Зеро x13", callback_data=f"{pre}_{bet}_zero")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=game)],
        ])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔴 Красное x2", callback_data=f"{pre}_{bet}_red"),
             InlineKeyboardButton(text="⚫ Чёрное x2", callback_data=f"{pre}_{bet}_black")],
            [InlineKeyboardButton(text="🟢 Зеро x36", callback_data=f"{pre}_{bet}_zero")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=game)],
        ])
    await edit(c, f"🎡 Ставка {fmt(bet)}", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("rs_"))
@dp.callback_query(F.data.startswith("ar_"))
@dp.callback_query(F.data.startswith("mr_"))
async def roulette_spin(c: CallbackQuery):
    parts = c.data.split("_")
    pre = parts[0]
    bet = int(parts[1])
    pick = parts[2]
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)

    if pre == 'rs':
        win, n, color = play_roulette(bet, pick)
    elif pre == 'ar':
        win, n, color = american_roulette(bet, pick)
    else:
        win, n, color = mini_roulette(bet, pick)

    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    text = (
        f"🎡 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Выпало: <b>{n}</b> ({color})\n"
        f"💰 Итог: <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🎲 КОСТИ
# ============================================================
@dp.callback_query(F.data == "dice")
async def cb_dice(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🎲 <b>КОСТИ</b>\n\n"
        f"💰 {fmt(u['balance'])}\n\n"
        f"⬆️ Больше 3 → x1.9\n"
        f"⬇️ Меньше 4 → x1.9\n"
        f"🎯 Ровно 6 → x4.5\n\n"
        f"Выбери ставку:"
    )
    await edit(c, text, bet_menu("dice", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_dice_"))
async def dice_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Больше 3", callback_data=f"ds_{bet}_high"),
         InlineKeyboardButton(text="⬇️ Меньше 4", callback_data=f"ds_{bet}_low")],
        [InlineKeyboardButton(text="🎯 Ровно 6 (x4.5)", callback_data=f"ds_{bet}_six")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="dice")],
    ])
    await edit(c, f"🎲 Ставка {fmt(bet)}\n\nТвой прогноз?", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("ds_"))
async def dice_roll(c: CallbackQuery):
    parts = c.data.split("_")
    bet = int(parts[1])
    pick = parts[2]
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return    update_balance(c.from_user.id, -bet)
    await c.answer()
    await c.message.answer("🎲 Бросаем...")

    msg = await bot.send_dice(c.message.chat.id, emoji="🎲")
    await asyncio.sleep(4)
    v = msg.dice.value

    win = 0
    if pick == 'high' and v > 3:
        win = int(bet * 1.9)
    elif pick == 'low' and v < 4:
        win = int(bet * 1.9)
    elif pick == 'six' and v == 6:
        win = int(bet * 4.5)

    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    await c.message.answer(
        f"🎲 Выпало <b>{v}</b>\n"
        f"💰 Итог: <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>",
        reply_markup=back_menu(), parse_mode="HTML"
    )


# ============================================================
# 🪙 МОНЕТКА
# ============================================================
@dp.callback_query(F.data == "coin")
async def cb_coin(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🪙 <b>МОНЕТКА</b>\n\n💰 {fmt(u['balance'])}\n\nВыбери ставку:"
    await edit(c, text, bet_menu("coin", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_coin_"))
async def coin_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Орёл (x1.9)", callback_data=f"cs_{bet}_eagle"),
         InlineKeyboardButton(text="🪙 Решка (x1.9)", callback_data=f"cs_{bet}_tail")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="coin")],
    ])
    await edit(c, f"🪙 Ставка {fmt(bet)}", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("cs_"))
async def coin_flip(c: CallbackQuery):
    parts = c.data.split("_")
    bet = int(parts[1])
    pick = parts[2]
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    win, result = play_coin(bet, pick)
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    result_str = "🦅 Орёл" if result == 'eagle' else "🪙 Решка"
    s = '+' if win > 0 else '-'
    text = (
        f"🪙 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Выпало: <b>{result_str}</b>\n"
        f"💰 <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 Баланс: <b>{fmt(u['balance'])}</b>"
    )
    await edit(c, text, back_menu())
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 💣 МИНЫ
# ============================================================
@dp.callback_query(F.data == "mines")
async def cb_mines(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"💣 <b>МИНЫ</b>\n\n5×5, 3 мины. Множитель растёт!\n\n💰 {fmt(u['balance'])}"
    await edit(c, text, bet_menu("mines", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_mines_"))
async def mines_start(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    mines_games[c.from_user.id] = {
        'mines': mines_new_game(),
        'opened': set(),
        'bet': bet,
        'finished': False
    }
    g = mines_games[c.from_user.id]
    text = f"💣 <b>МИНЫ</b>\n\n💰 Ставка: {fmt(bet)}\n🎯 Открыто: 0\n💎 x1.00"
    await edit(c, text, mines_grid_buttons(g, g['opened'], g['mines']))
    await c.answer()


@dp.callback_query(F.data.startswith("mines_open_"))
async def mines_open(c: CallbackQuery):
    g = mines_games.get(c.from_user.id)
    if not g or g['finished']:
        await c.answer("Игра не активна")
        return
    idx = int(c.data.split("_")[2])
    if idx in g['opened']:
        await c.answer("Уже открыто")
        return
    if idx in g['mines']:
        g['finished'] = True
        record_game(c.from_user.id, g['bet'], 0)
        u = get_user(c.from_user.id)
        text = f"💥 <b>ВЗРЫВ!</b>\n\n💰 Потеряно: <b>-{fmt(g['bet'])}</b>\n💼 {fmt(u['balance'])}"
        await edit(c, text, back_menu())
        await c.answer()
        del mines_games[c.from_user.id]
        return
    g['opened'].add(idx)
    mult = mines_multiplier(len(g['opened']), 3)
    potential = int(g['bet'] * mult)
    text = (
        f"💣 <b>МИНЫ</b>\n\n"
        f"💰 Ставка: {fmt(g['bet'])}\n"
        f"🎯 Открыто: <b>{len(g['opened'])}</b>\n"
        f"💎 Множитель: <b>x{mult}</b>\n"
        f"💵 Забрать: {fmt(potential)}"
    )
    await edit(c, text, mines_grid_buttons(g, g['opened'], g['mines']))
    await c.answer()


@dp.callback_query(F.data == "mines_cashout")
async def mines_cashout(c: CallbackQuery):
    g = mines_games.get(c.from_user.id)
    if not g or g['finished'] or not g['opened']:
        await c.answer("Нечего забирать")
        return
    mult = mines_multiplier(len(g['opened']), 3)
    win = int(g['bet'] * mult)
    update_balance(c.from_user.id, win)
    record_game(c.from_user.id, g['bet'], win)
    g['finished'] = True
    u = get_user(c.from_user.id)
    text = f"💰 <b>ЗАБРАЛ!</b>\n\n💎 x{mult}\n💰 +{fmt(win)}\n💼 {fmt(u['balance'])}"
    await edit(c, text, back_menu())
    await c.answer()
    del mines_games[c.from_user.id]
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 💎 КЕНО
# ============================================================
@dp.callback_query(F.data == "keno")
async def cb_keno(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"💎 <b>КЕНО</b>\n\nВыбери 1-10 чисел от 1-80.\n\n💰 {fmt(u['balance'])}"
    await edit(c, text, bet_menu("keno", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_keno_"))
async def keno_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    keno_picks[c.from_user.id] = {'bet': bet, 'picks': set()}
    await show_keno_grid(c)
    await c.answer()


async def show_keno_grid(c: CallbackQuery):
    state = keno_picks.get(c.from_user.id)
    if not state:
        return
    picks = state['picks']
    bet = state['bet']
    rows = []
    row = []
    for n in range(1, 81):
        mark = "✅" if n in picks else str(n)
        row.append(InlineKeyboardButton(text=mark, callback_data=f"kp_{n}"))
        if len(row) == 8:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=f"🎰 ИГРАТЬ ({len(picks)} чисел)", callback_data="keno_play")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await c.message.edit_text(
        f"💎 <b>КЕНО</b>\n\n💰 Ставка: {fmt(bet)}\n🎯 Выбрано: <b>{len(picks)}/10</b>",
        reply_markup=kb, parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("kp_"))
async def keno_pick(c: CallbackQuery):
    n = int(c.data.split("_")[1])
    state = keno_picks.get(c.from_user.id)
    if not state:
        await c.answer("Начни заново")
        return
    if n in state['picks']:
        state['picks'].remove(n)
    elif len(state['picks']) < 10:
        state['picks'].add(n)
    else:
        await c.answer("Максимум 10!")
        return
    await show_keno_grid(c)
    await c.answer()


@dp.callback_query(F.data == "keno_play")
async def keno_do_play(c: CallbackQuery):
    state = keno_picks.get(c.from_user.id)
    if not state or not state['picks']:
        await c.answer("Выбери числа!")
        return
    bet = state['bet']
    picks = list(state['picks'])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    win, drawn, matches = keno_play(bet, picks)
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    text = (
        f"💎 <b>КЕНО РЕЗУЛЬТАТ</b>\n\n"
        f"🎯 Твои: <code>{' '.join(map(str, sorted(picks)))}</code>\n"
        f"🎲 Выпало: <code>{' '.join(map(str, sorted(drawn)))}</code>\n"
        f"✅ Совпадений: <b>{matches}</b>\n\n"
        f"💰 <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 {fmt(u['balance'])}"
    )
    await edit(c, text, back_menu())
    await c.answer()
    del keno_picks[c.from_user.id]
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 💥 КРАШ
# ============================================================
@dp.callback_query(F.data == "crash")
async def cb_crash(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"💥 <b>КРАШ</b>\n\nМножитель растёт. Забирай до краха!\n\n💰 {fmt(u['balance'])}"
    await edit(c, text, bet_menu("crash", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_crash_"))
async def crash_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    crash_point = crash_generate()
    crash_games[c.from_user.id] = {
        'bet': bet, 'crash_point': crash_point,
        'mult': 1.0, 'active': True, 'msg_id': None
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 ЗАБРАТЬ", callback_data="crash_cashout")],
    ])
    msg = await c.message.edit_text(
        f"💥 <b>КРАШ</b>\n\n"
        f"💰 Ставка: {fmt(bet)}\n"
        f"📈 x1.00\n"
        f"💵 Забрать: {fmt(bet)}",
        reply_markup=kb, parse_mode="HTML"
    )
    crash_games[c.from_user.id]['msg_id'] = msg.message_id
    asyncio.create_task(crash_loop(c.from_user.id, c.message.chat.id))
    await c.answer()


async def crash_loop(user_id, chat_id):
    g = crash_games.get(user_id)
    if not g:
        return
    while g['active']:
        await asyncio.sleep(0.5)
        g['mult'] = round(g['mult'] + random.uniform(0.05, 0.3), 2)
        if g['mult'] >= g['crash_point']:
            g['active'] = False
            g['mult'] = g['crash_point']
            record_game(user_id, g['bet'], 0)
            u = get_user(user_id)
            try:
                await bot.edit_message_text(
                    chat_id=chat_id, message_id=g['msg_id'],
                    text=f"💥 <b>КРАШ x{g['crash_point']}!</b>\n\n💰 -{fmt(g['bet'])}\n💼 {fmt(u['balance'])}",
                    reply_markup=back_menu(), parse_mode="HTML"
                )
            except Exception:
                pass
            del crash_games[user_id]
            return
        payout = int(g['bet'] * g['mult'])
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💵 ЗАБРАТЬ", callback_data="crash_cashout")],
            ])
            await bot.edit_message_text(
                chat_id=chat_id, message_id=g['msg_id'],
                text=f"💥 <b>КРАШ</b>\n\n💰 {fmt(g['bet'])}\n📈 x{g['mult']}\n💵 Забрать: {fmt(payout)}",
                reply_markup=kb, parse_mode="HTML"
            )
        except Exception:
            pass


@dp.callback_query(F.data == "crash_cashout")
async def crash_cashout(c: CallbackQuery):
    g = crash_games.get(c.from_user.id)
    if not g or not g['active']:
        await c.answer("Игра закончилась")
        return
    g['active'] = False
    win = int(g['bet'] * g['mult'])
    update_balance(c.from_user.id, win)
    record_game(c.from_user.id, g['bet'], win)
    u = get_user(c.from_user.id)
    await c.message.edit_text(
        f"💵 <b>ЗАБРАЛ!</b>\n\n📈 x{g['mult']}\n💰 +{fmt(win)}\n💼 {fmt(u['balance'])}",
        reply_markup=back_menu(), parse_mode="HTML"
    )
    await c.answer()
    del crash_games[c.from_user.id]


# ============================================================
# 🎰 СКРЕТЧ-КАРТА
# ============================================================
@dp.callback_query(F.data == "scratch")
async def cb_scratch(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🎰 <b>СКРЕТЧ-КАРТА</b>\n\n3×3, собери 3 в ряд!\n\n💰 {fmt(u['balance'])}"
    await edit(c, text, bet_menu("scratch", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_scratch_"))
async def scratch_play(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    win, grid, desc = scratch_card(bet)
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    g = ""
    for row in grid:
        g += " ".join(row) + "\n"
    s = '+' if win > 0 else '-'
    text = (
        f"🎰 <b>СКРЕТЧ</b>\n\n"
        f"<code>{g}</code>\n"
        f"{desc}\n"
        f"💰 <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 {fmt(u['balance'])}"
    )
    await edit(c, text, back_menu())
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# 🎯 КРЭПС
# ============================================================
@dp.callback_query(F.data == "craps")
async def cb_craps(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🎯 <b>КРЭПС</b>\n\n"
        f"Правила:\n"
        f"• Pass Line: 7/11 на первом броске — победа\n"
        f"• Затем нужно выбить точку\n\n"
        f"💰 {fmt(u['balance'])}"
    )
    await edit(c, text, bet_menu("craps", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_craps_"))
async def craps_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    craps_games[c.from_user.id] = {'bet': bet, 'phase': 'comeout', 'point': 0}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 БРОСИТЬ", callback_data="craps_roll")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")],
    ])
    await edit(c, f"🎯 <b>КРЭПС</b>\n\n💰 Ставка: {fmt(bet)}\n\nБросай!", kb)
    await c.answer()


@dp.callback_query(F.data == "craps_roll")
async def craps_do_roll(c: CallbackQuery):
    g = craps_games.get(c.from_user.id)
    if not g:
        await c.answer("Нет активной игры")
        return
    await c.answer()
    await c.message.answer("🎲 Бросаем кости...")

    d1_msg = await bot.send_dice(c.message.chat.id, emoji="🎲")
    await asyncio.sleep(4)
    d1 = d1_msg.dice.value

    d2_msg = await bot.send_dice(c.message.chat.id, emoji="🎲")
    await asyncio.sleep(4)
    d2 = d2_msg.dice.value

    total = d1 + d2
    win, phase, point, msg = craps_check_pass(g['bet'], g['phase'], g['point'], total)
    g['phase'] = phase
    g['point'] = point

    if win > 0:
        update_balance(c.from_user.id, win)
        record_game(c.from_user.id, g['bet'], win)
        del craps_games[c.from_user.id]
    elif phase == 'comeout':
        record_game(c.from_user.id, g['bet'], 0)
        del craps_games[c.from_user.id]
    else:
        record_game(c.from_user.id, g['bet'], 0)

    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    text = (
        f"🎲 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Кости: <b>{d1} + {d2} = {total}</b>\n\n"
        f"{msg}\n\n"
        f"💰 <b>{s}{fmt(win if win > 0 else g['bet'])}</b>\n"
        f"💼 {fmt(u['balance'])}"
    )

    if phase == 'point':
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 ЕЩЁ БРОСОК", callback_data="craps_roll")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")],
        ])
        await c.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await c.message.answer(text, reply_markup=back_menu(), parse_mode="HTML")


# ============================================================
# 🎲 ХАЙ-ЛОУ / СИК-БО
# ============================================================
@dp.callback_query(F.data == "hilo")
async def cb_hilo(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🎲 <b>ХАЙ-ЛОУ</b>\n\n⬆️ Больше 3 → x1.9\n⬇️ Меньше 4 → x1.9\n\n💰 {fmt(u['balance'])}"
    await edit(c, text, bet_menu("hilo", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_hilo_"))
async def hilo_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Больше 3", callback_data=f"hl_{bet}_high"),
         InlineKeyboardButton(text="⬇️ Меньше 4", callback_data=f"hl_{bet}_low")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="hilo")],
    ])
    await edit(c, f"🎲 Ставка {fmt(bet)}", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("hl_"))
async def hilo_play(c: CallbackQuery):
    parts = c.data.split("_")
    bet = int(parts[1])
    pick = parts[2]
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    await c.answer()
    await c.message.answer("🎲 Бросаем...")
    msg = await bot.send_dice(c.message.chat.id, emoji="🎲")
    await asyncio.sleep(4)
    v = msg.dice.value
    win = 0
    if pick == 'high' and v > 3:
        win = int(bet * 1.9)
    elif pick == 'low' and v < 4:
        win = int(bet * 1.9)
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    await c.message.answer(
        f"🎲 Выпало <b>{v}</b>\n💰 {s}{fmt(win if win > 0 else bet)}\n💼 {fmt(u['balance'])}",
        reply_markup=back_menu(), parse_mode="HTML"
    )


@dp.callback_query(F.data == "sickbo")
async def cb_sickbo(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🎲 <b>СИК-БО</b>\n\n3 кубика. Угадай сумму 3-18.\n\n💰 {fmt(u['balance'])}"
    await edit(c, text, bet_menu("sickbo", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_sickbo_"))
async def sickbo_bet(c: CallbackQuery):
    bet = int(c.data.split("_")[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    rows = []
    row = []
    for s in range(3, 19):
        row.append(InlineKeyboardButton(text=f"{s}", callback_data=f"sb_{bet}_{s}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="sickbo")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await edit(c, f"🎲 Ставка {fmt(bet)}\n\nУгадай сумму:", kb)
    await c.answer()


@dp.callback_query(F.data.startswith("sb_"))
async def sickbo_play(c: CallbackQuery):
    parts = c.data.split("_")
    bet = int(parts[1])
    guess = int(parts[2])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    await c.answer()
    await c.message.answer(f"🎲 Бросаем 3 кубика (ставка на {guess})...")

    dice_msgs = []
    for _ in range(3):
        msg = await bot.send_dice(c.message.chat.id, emoji="🎲")
        dice_msgs.append(msg)
        await asyncio.sleep(4)

    dice_vals = [m.dice.value for m in dice_msgs]
    total = sum(dice_vals)
    win = 0
    if total == guess:
        from config import SICKBO_PAYOUTS
        mult = SICKBO_PAYOUTS.get(total, 1.0)
        win = int(bet * mult)
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    await c.message.answer(
        f"🎲 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Кубики: {dice_vals[0]}+{dice_vals[1]}+{dice_vals[2]} = <b>{total}</b>\n"
        f"Прогноз: {guess}\n"
        f"💰 <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 {fmt(u['balance'])}",
        reply_markup=back_menu(), parse_mode="HTML"
    )


# ============================================================
# 🎯 СПОРТИВНЫЕ ИГРЫ
# ============================================================
@dp.callback_query(F.data == "darts")
async def cb_darts(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🎯 <b>ДАРТС</b>\n\n"
        f"💰 {fmt(u['balance'])}\n\n"
        f"🎯 Мишень (3-6) → x1.5\n"
        f"🎯 Круг (4-6) → x2\n"
        f"🎯 Яблочко (6) → x5\n\n"
        f"Куда метим?"
    )
    await edit(c, text, sport_choice('darts'))
    await c.answer()


@dp.callback_query(F.data.startswith("sport_darts_"))
async def darts_pick_type(c: CallbackQuery, state: FSMContext):
    bet_type = c.data.split("_")[2]
    await state.update_data(game='darts', bet_type=bet_type)
    await state.set_state(SportBet.waiting_amount)
    u = get_user(c.from_user.id)
    text = f"🎯 <b>ДАРТС</b>\n\n💰 {fmt(u['balance'])}\n🎯 {bet_type}\n\nВыбери ставку:"
    await edit(c, text, sport_bet_menu(f"darts_{bet_type}", "darts"))
    await c.answer()


@dp.callback_query(F.data == "football")
async def cb_football(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"⚽ <b>ФУТБОЛ</b>\n\n💰 {fmt(u['balance'])}\n\n⚽ Гол → x1.9\n⚽ Девятка → x4"
    await edit(c, text, sport_choice('football'))
    await c.answer()


@dp.callback_query(F.data.startswith("sport_football_"))
async def football_pick_type(c: CallbackQuery, state: FSMContext):
    bet_type = c.data.split("_")[2]
    await state.update_data(game='football', bet_type=bet_type)
    await state.set_state(SportBet.waiting_amount)
    u = get_user(c.from_user.id)
    text = f"⚽ <b>ФУТБОЛ</b>\n\n💰 {fmt(u['balance'])}\n\nВыбери ставку:"
    await edit(c, text, sport_bet_menu(f"football_{bet_type}", "football"))
    await c.answer()


@dp.callback_query(F.data == "basket")
async def cb_basket(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🏀 <b>БАСКЕТБОЛ</b>\n\n💰 {fmt(u['balance'])}\n\n🏀 Бросок → x1.9\n🏀 Трёхочковый → x4.5"
    await edit(c, text, sport_choice('basket'))
    await c.answer()


@dp.callback_query(F.data.startswith("sport_basket_"))
async def basket_pick_type(c: CallbackQuery, state: FSMContext):
    bet_type = c.data.split("_")[2]
    await state.update_data(game='basket', bet_type=bet_type)
    await state.set_state(SportBet.waiting_amount)
    u = get_user(c.from_user.id)
    text = f"🏀 <b>БАСКЕТБОЛ</b>\n\n💰 {fmt(u['balance'])}\n\nВыбери ставку:"
    await edit(c, text, sport_bet_menu(f"basket_{bet_type}", "basket"))
    await c.answer()


@dp.callback_query(F.data == "bowling")
async def cb_bowling(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🎳 <b>БОУЛИНГ</b>\n\n💰 {fmt(u['balance'])}\n\n🎳 Страйк → x5\n🎳 Любое → x0.5-2.8"
    await edit(c, text, sport_choice('bowling'))
    await c.answer()


@dp.callback_query(F.data.startswith("sport_bowling_"))
async def bowling_pick_type(c: CallbackQuery, state: FSMContext):
    bet_type = c.data.split("_")[2]
    await state.update_data(game='bowling', bet_type=bet_type)
    await state.set_state(SportBet.waiting_amount)
    u = get_user(c.from_user.id)
    text = f"🎳 <b>БОУЛИНГ</b>\n\n💰 {fmt(u['balance'])}\n\nВыбери ставку:"
    await edit(c, text, sport_bet_menu(f"bowling_{bet_type}", "bowling"))
    await c.answer()


@dp.callback_query(F.data == "slot_dice")
async def cb_slot_dice(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"🎰 <b>СЛОТ-МАШИНА</b>\n\n"
        f"💰 {fmt(u['balance'])}\n\n"
        f"Значения 1-64. 64 → x50!\n\n"
        f"Выбери ставку:"
    )
    await edit(c, text, bet_menu("slot_dice", u['balance']))
    await c.answer()


@dp.callback_query(F.data.startswith("bet_slot_dice_"))
async def slot_dice_play(c: CallbackQuery):
    bet = int(c.data.split("_")[3])
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)
    await c.message.edit_text("🎰 <b>Крутим барабаны...</b>", parse_mode="HTML")
    result = await play_slot_dice(bot, c.message.chat.id, bet)
    win = result['win']
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    text = (
        f"🎰 <b>РЕЗУЛЬТАТ</b>\n\n"
        f"Значение: <b>{result['value']}/64</b>\n"
        f"{result['result_text']}\n\n"
        f"💰 <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 {fmt(u['balance'])}"
    )
    await edit(c, text, back_menu())
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


# ============================================================
# СПОРТ - ОБРАБОТЧИКИ СТАВОК
# ============================================================
@dp.callback_query(F.data.startswith("sbet_"))
async def sport_quick_bet(c: CallbackQuery, state: FSMContext):
    parts = c.data.split("_")
    game = parts[1]
    bet_type = parts[2]
    bet = int(parts[3])
    await state.clear()
    await run_sport_game(c, game, bet_type, bet)


@dp.callback_query(F.data.startswith("scustom_"))
async def sport_custom_bet(c: CallbackQuery, state: FSMContext):
    parts = c.data.split("_")
    game = parts[1]
    bet_type = parts[2]
    await state.update_data(game=game, bet_type=bet_type)
    await state.set_state(SportBet.waiting_amount)
    u = get_user(c.from_user.id)
    await edit(c, f"✏️ Введи сумму:\n\n💰 Баланс: {fmt(u['balance'])}", back_menu())
    await c.answer()


@dp.message(SportBet.waiting_amount)
async def sport_handle_amount(m: Message, state: FSMContext):
    try:
        bet = int(m.text.strip())
        if bet < 50:
            await m.answer("❌ Минимум 50$")
            return
    except ValueError:
        await m.answer("❌ Введи число!")
        return

    data = await state.get_data()
    game = data.get('game')
    bet_type = data.get('bet_type')
    await state.clear()

    if not game or not bet_type:
        await m.answer("❌ Ошибка, начни заново")
        return

    u = get_user(m.from_user.id)
    if bet > u['balance']:
        await m.answer(f"❌ Недостаточно! Баланс: {fmt(u['balance'])}")
        return

    await run_sport_game_msg(m, game, bet_type, bet)


async def run_sport_game(c: CallbackQuery, game, bet_type, bet):
    u = get_user(c.from_user.id)
    if u['balance'] < bet:
        await c.answer("❌")
        return
    update_balance(c.from_user.id, -bet)

    play_map = {
        'darts': ("🎯 Бросаем...", play_darts),
        'football': ("⚽ Пенальти...", play_football),
        'basket': ("🏀 Бросаем...", play_basketball),
        'bowling': ("🎳 Шар катится...", play_bowling),
    }
    if game not in play_map:
        await c.answer("Ошибка")
        return
    text, play_fn = play_map[game]
    await c.message.edit_text(text, parse_mode="HTML")
    result = await play_fn(bot, c.message.chat.id, bet, bet_type)
    win = result['win']
    win = apply_dynamic_odds(c.from_user.id, win)
    if win > 0:
        update_balance(c.from_user.id, win)
    record_game(c.from_user.id, bet, win)
    u = get_user(c.from_user.id)
    s = '+' if win > 0 else '-'
    final = (
        f"{result['result_text']}\n\n"
        f"💰 <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 {fmt(u['balance'])}"
    )
    await c.message.edit_text(final, reply_markup=back_menu(), parse_mode="HTML")
    await c.answer()
    await notify_achievements(c.message, c.from_user.id)


async def run_sport_game_msg(m: Message, game, bet_type, bet):
    update_balance(m.from_user.id, -bet)
    play_map = {
        'darts': ("🎯 Бросаем...", play_darts),
        'football': ("⚽ Пенальти...", play_football),
        'basket': ("🏀 Бросаем...", play_basketball),
        'bowling': ("🎳 Шар катится...", play_bowling),
    }
    if game not in play_map:
        await m.answer("Ошибка")
        return
    text, play_fn = play_map[game]
    msg = await m.answer(text, parse_mode="HTML")
    result = await play_fn(bot, m.chat.id, bet, bet_type)
    win = result['win']
    win = apply_dynamic_odds(m.from_user.id, win)
    if win > 0:
        update_balance(m.from_user.id, win)
    record_game(m.from_user.id, bet, win)
    u = get_user(m.from_user.id)
    s = '+' if win > 0 else '-'
    final = (
        f"{result['result_text']}\n\n"
        f"💰 <b>{s}{fmt(win if win > 0 else bet)}</b>\n"
        f"💼 {fmt(u['balance'])}"
    )
    await msg.edit_text(final, reply_markup=back_menu(), parse_mode="HTML")


# ============================================================
# 📚 ПОМОЩЬ
# ============================================================
@dp.callback_query(F.data == "help")
async def cb_help(c: CallbackQuery):
    text = "📚 <b>ПОМОЩЬ</b>\n\n🎮 Выбери игру:"
    await edit(c, text, help_menu())
    await c.answer()


@dp.callback_query(F.data.startswith("help_"))
async def cb_help_game(c: CallbackQuery):
    key = c.data.replace("help_", "")
    if key == "faq":
        text = "❓ <b>FAQ</b>\n\nВыбери категорию:"
        rows = []
        for k, (name, _) in FAQ_CATEGORIES.items():
            rows.append([InlineKeyboardButton(text=name, callback_data=f"faq_{k}")])
        rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="help")])
        await edit(c, text, InlineKeyboardMarkup(inline_keyboard=rows))
        await c.answer()
        return

    if key not in HELP_CATEGORIES:
        await c.answer("❌ Не найдено")
        return

    text, preview, gif = get_help(key)
    if not text:
        await c.answer("❌ Не найдено")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data=key)],
        [InlineKeyboardButton(text="⬅️ К списку", callback_data="help")],
    ])
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data.startswith("faq_"))
async def cb_faq(c: CallbackQuery):
    cat = c.data.replace("faq_", "")
    text = get_faq(cat)
    if not text:
        await c.answer("❌")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К FAQ", callback_data="help_faq")],
    ])
    await edit(c, text, kb)
    await c.answer()


# ============================================================
# 🌍 ЯЗЫКИ
# ============================================================
@dp.callback_query(F.data == "lang_menu")
async def cb_lang_menu(c: CallbackQuery):
    await edit(c, "🌍 Выбери язык:", lang_menu())
    await c.answer()


@dp.callback_query(F.data.startswith("setlang_"))
async def cb_setlang(c: CallbackQuery):
    l = c.data.split("_")[1]
    if l not in SUPPORTED_LANGS:
        await c.answer("❌")
        return
    set_language(c.from_user.id, l)
    await c.answer(f"✅ {lang_name(l)}", show_alert=True)
    await edit(c, f"✅ Язык: <b>{lang_name(l)}</b>", back_menu())


# ============================================================
# 👑 VIP
# ============================================================
@dp.callback_query(F.data == "vip_info")
async def cb_vip(c: CallbackQuery):
    u = get_user(c.from_user.id)
    lvl, name, cb = get_vip_level(c.from_user.id)
    curr, cn, nn, prog = get_vip_progress(c.from_user.id)
    bar_len = 10
    filled = int(prog / 100 * bar_len) if prog else 0
    bar = "▰" * filled + "▱" * (bar_len - filled)
    text = (
        f"👑 <b>VIP</b>\n\n"
        f"Уровень: <b>{name}</b>\n"
        f"💰 Проиграно: {fmt(u['total_lost'])}\n"
        f"💵 Кэшбэк: <b>{cb}%</b>\n\n"
    )
    if nn:
        text += f"До <b>{nn}</b>: {prog:.1f}%\n{bar}\n\n"
    text += "🥉 Бронза 2% | 🥈 Серебро 3% | 🥇 Золото 5%\n💎 Платина 7% | 💠 Бриллиант 10% | 👑 Император 15%"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Забрать кэшбэк", callback_data="claim_cashback")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")],
    ])
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data == "claim_cashback")
async def cb_claim_cashback(c: CallbackQuery):
    amount = give_cashback(c.from_user.id)
    if amount > 0:
        u = get_user(c.from_user.id)
        await c.answer(f"💵 +{fmt(amount)}", show_alert=True)
        await edit(c, f"✅ Кэшбэк: <b>+{fmt(amount)}</b>\n\n💼 {fmt(u['balance'])}", back_menu())
    else:
        await c.answer("💵 Пока 0$", show_alert=True)


# ============================================================
# 💎 МАГАЗИН / ПЛАТЕЖИ
# ============================================================
@dp.callback_query(F.data == "shop")
async def cb_shop(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"💎 <b>МАГАЗИН</b>\n\n"
        f"💰 Баланс: {fmt(u['balance'])}\n"
        f"💎 Кристаллов: <b>{u['crystals']}</b>\n\n"
        f"💱 Курс: 1💎 = {CRYSTAL_TO_MONEY}$\n"
        f"Обратно: {MONEY_TO_CRYSTAL}$ = 1💎\n\n"
        f"Выбери пакет:"
    )
    rows = []
    for i, (crystals, stars, rub, bonus) in enumerate(CRYSTAL_PACKS):
        total = crystals + int(crystals * bonus / 100)
        bonus_str = f" +{bonus}%" if bonus else ""
        rows.append([InlineKeyboardButton(
            text=f"💎 {total}{bonus_str} — {stars}⭐ / {rub}₽",
            callback_data=f"pack_{i}"
        )])
    rows.append([InlineKeyboardButton(text="💳 Ручная оплата", callback_data="manual_pay")])
    rows.append([InlineKeyboardButton(text="💱 Обменять 💎→$", callback_data="exchange")])
    rows.append([InlineKeyboardButton(text="💱 Обменять $→💎", callback_data="reverse_exchange")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")])
    await edit(c, text, InlineKeyboardMarkup(inline_keyboard=rows))
    await c.answer()


@dp.callback_query(F.data.startswith("pack_"))
async def cb_pack(c: CallbackQuery):
    idx = int(c.data.split("_")[1])
    crystals, stars, rub, bonus = CRYSTAL_PACKS[idx]
    total = crystals + int(crystals * bonus / 100)
    text = (
        f"💎 <b>{total} кристаллов</b>\n\n"
        f"⭐ Stars: <b>{stars}⭐</b>\n"
        f"💎 CryptoBot: ≈{round(rub/95, 2)} USDT\n"
        f"💵 Ручная: {rub}₽\n\n"
        f"Как оплатить?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ Stars ({stars}⭐)", callback_data=f"pay_stars_{idx}")],
        [InlineKeyboardButton(text="💎 CryptoBot", callback_data=f"pay_crypto_{idx}")],
        [InlineKeyboardButton(text="💵 Ручная", callback_data="manual_pay")],
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
        await c.message.answer(f"❌ {e}")


@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def on_payment(m: Message):
    payload = m.successful_payment.invoice_payload
    parts = payload.split("_")
    crystals = int(parts[2])
    buy_crystals(m.from_user.id, crystals, 'stars', m.successful_payment.telegram_payment_charge_id)
    u = get_user(m.from_user.id)
    await m.answer(
        f"🎉 <b>Оплата прошла!</b>\n\n"
        f"💎 +{crystals}\n"
        f"💼 Всего: <b>{u['crystals']}</b>",
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("pay_crypto_"))
async def cb_pay_crypto(c: CallbackQuery):
    idx = int(c.data.split("_")[2])
    crystals, stars, rub, bonus = CRYSTAL_PACKS[idx]
    total = crystals + int(crystals * bonus / 100)
    await c.answer("💎 Создаю счёт...")
    inv_id, url = await create_crypto_invoice(c.from_user.id, idx, total, rub)
    if not inv_id:
        await c.message.answer("❌ CryptoBot не настроен.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Оплатить", url=url)],
        [InlineKeyboardButton(text="✅ Проверить", callback_data=f"check_crypto_{inv_id}_{total}")],
    ])
    await c.message.edit_text(
        f"💎 <b>Оплата CryptoBot</b>\n\nКристаллов: <b>{total}</b>\nСумма: ≈<b>{round(rub/95, 2)} USDT</b>",
        reply_markup=kb, parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("check_crypto_"))
async def cb_check_crypto(c: CallbackQuery):
    parts = c.data.split("_")
    inv_id = parts[2]
    crystals = int(parts[3])
    status = await check_crypto_invoice(inv_id)
    if status == 'paid':
        buy_crystals(c.from_user.id, crystals, 'crypto', inv_id)
        u = get_user(c.from_user.id)
        await c.answer(f"✅ +{crystals}💎!", show_alert=True)
        await edit(c, f"🎉 +{crystals}💎\n💼 {u['crystals']}", back_menu())
    elif status == 'active':
        await c.answer("⏳ Не завершён", show_alert=True)
    else:
        await c.answer(f"❌ {status}", show_alert=True)


@dp.callback_query(F.data == "manual_pay")
async def cb_manual_pay(c: CallbackQuery):
    await edit(c, manual_payment_text(), back_menu())
    await c.answer()


@dp.callback_query(F.data == "exchange")
async def cb_exchange(c: CallbackQuery):
    u = get_user(c.from_user.id)
    if u['crystals'] < 1:
        await c.answer("❌ Нет кристаллов")
        return
    text = f"💱 <b>Обмен 💎→$</b>\n\n💎 {u['crystals']} → {u['crystals'] * CRYSTAL_TO_MONEY}$"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💱 Обменять всё", callback_data="exchange_all")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="shop")],
    ])
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data == "exchange_all")
async def cb_exchange_all(c: CallbackQuery):
    u = get_user(c.from_user.id)
    if u['crystals'] < 1:
        await c.answer("❌")
        return
    ok, money = exchange_crystals(c.from_user.id, u['crystals'])
    if ok:
        u2 = get_user(c.from_user.id)
        await c.answer(f"💱 +{fmt(money)}!", show_alert=True)
        await edit(c, f"✅ Обмен!\n\n💎 {u['crystals']} → +{fmt(money)}\n💼 {fmt(u2['balance'])}", back_menu())


@dp.callback_query(F.data == "reverse_exchange")
async def cb_reverse_exchange(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = (
        f"💱 <b>Обмен $→💎</b>\n\n"
        f"Курс: <b>{MONEY_TO_CRYSTAL}$ = 1💎</b>\n"
        f"💰 Баланс: {fmt(u['balance'])}\n"
        f"💎 Получишь: {u['balance'] // MONEY_TO_CRYSTAL}💎\n\n"
        f"⚠️ Курс хуже, чем покупка!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💱 Обменять всё ({u['balance'] // MONEY_TO_CRYSTAL}💎)", callback_data="reverse_all")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="shop")],
    ])
    await edit(c, text, kb)
    await c.answer()


@dp.callback_query(F.data == "reverse_all")
async def cb_reverse_all(c: CallbackQuery):
    from wallet import money_to_crystals
    u = get_user(c.from_user.id)
    money = u['balance'] // MONEY_TO_CRYSTAL * MONEY_TO_CRYSTAL
    ok, crystals, err = money_to_crystals(c.from_user.id, money)
    if ok:
        u2 = get_user(c.from_user.id)
        await c.answer(f"💱 +{crystals}💎!", show_alert=True)
        await edit(c, f"✅ Обмен!\n\n💰 -{fmt(money)}\n💎 +{crystals}\n💼 {fmt(u2['balance'])}", back_menu())
    else:
        await c.answer(f"❌ {err}", show_alert=True)


# ============================================================
# 💰 ВЫВОД
# ============================================================
@dp.callback_query(F.data == "withdraw")
async def cb_withdraw(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = withdraw_info_text() + f"\n\n💎 Твой: <b>{u['crystals']}</b>"
    await edit(c, text, withdraw_methods_menu())
    await c.answer()


@dp.callback_query(F.data == "wd_history")
async def cb_wd_history(c: CallbackQuery):
    rows = user_withdrawals(c.from_user.id, 10)
    if not rows:
        text = "📜 Пока пусто"
    else:
        text = "📜 <b>ИСТОРИЯ</b>\n\n"
        for wid, crystals, rub, usdt, method, status, ts in rows:
            emoji = status_emoji(status)
            date = time.strftime('%d.%m %H:%M', time.localtime(ts))
            text += f"{emoji} #{wid} — {crystals}💎 / {rub}₽\n<i>{date} | {status_name(status)}</i>\n\n"
    total = total_withdrawn(c.from_user.id)
    text += f"\n💰 Всего выведено: <b>{total}💎</b>"
    await edit(c, text, back_menu())
    await c.answer()


@dp.callback_query(F.data.startswith("wd_method_"))
async def cb_wd_method(c: CallbackQuery, state: FSMContext):
    method = c.data.replace("wd_method_", "")
    u = get_user(c.from_user.id)
    from config import MIN_WITHDRAW_CRYSTALS
    if u['crystals'] < MIN_WITHDRAW_CRYSTALS:
        await c.answer(f"❌ Минимум {MIN_WITHDRAW_CRYSTALS}💎")
        return
    await state.update_data(method=method)
    await state.set_state(WithdrawState.waiting_amount)
    text = f"💎 <b>ВЫВОД</b>\n\nМетод: <b>{method}</b>\nБаланс: <b>{u['crystals']}💎</b>\n\nВыбери сумму:"
    await edit(c, text, withdraw_amount_menu(u['crystals']))
    await c.answer()


@dp.callback_query(F.data.startswith("wd_amount_"))
async def cb_wd_amount(c: CallbackQuery, state: FSMContext):
    amount = int(c.data.split("_")[2])
    await state.update_data(crystals=amount)
    await ask_wallet(c, state)


@dp.callback_query(F.data == "wd_custom")
async def cb_wd_custom(c: CallbackQuery, state: FSMContext):
    await state.set_state(WithdrawState.waiting_amount)
    u = get_user(c.from_user.id)
    from config import MIN_WITHDRAW_CRYSTALS, MAX_WITHDRAW_CRYSTALS
    await edit(c,
        f"✏️ Введи количество:\n\n💰 {u['crystals']}💎\n📉 Мин: {MIN_WITHDRAW_CRYSTALS} | Макс: {MAX_WITHDRAW_CRYSTALS}",
        back_menu())
    await c.answer()


async def ask_wallet(c_or_m, state):
    data = await state.get_data()
    method = data.get('method', 'manual')
    if method == 'cryptobot':
        text = "📝 Отправь <b>USDT/TON</b> адрес:"
    else:
        text = "📝 Напиши свой контакт:"
    if hasattr(c_or_m, 'message'):
        await c_or_m.message.edit_text(text, reply_markup=back_menu(), parse_mode="HTML")
    else:
        await c_or_m.answer(text, parse_mode="HTML")
    await state.set_state(WithdrawState.waiting_wallet)


@dp.message(WithdrawState.waiting_amount)
async def wd_handle_amount(m: Message, state: FSMContext):
    try:
        amount = int(m.text.strip())
    except ValueError:
        await m.answer("❌ Введи число!")
        return
    ok, err = validate_withdraw(m.from_user.id, amount)
    if not ok:
        await m.answer(err)
        return
    await state.update_data(crystals=amount)
    await ask_wallet(m, state)


@dp.message(WithdrawState.waiting_wallet)
async def wd_handle_wallet(m: Message, state: FSMContext):
    wallet = m.text.strip()
    if len(wallet) < 3:
        await m.answer("❌ Слишком короткий")
        return
    data = await state.get_data()
    crystals = data.get('crystals')
    method = data.get('method', 'manual')
    ok, wid, msg = request_withdraw(m.from_user.id, crystals, method, wallet)
    if not ok:
        await m.answer(msg)
        await state.clear()
        return
    await state.clear()
    rub, usdt = calc_payout(crystals)
    u = get_user(m.from_user.id)
    text = (
        f"{msg}\n\n"
        f"💎 {crystals}\n"
        f"💰 {rub}₽ ({usdt} USDT)\n"
        f"💳 <code>{wallet}</code>\n\n"
        f"⏱ До 24ч\n"
        f"💼 Кристаллы: {u['crystals']}💎"
    )
    await m.answer(text, reply_markup=back_menu(), parse_mode="HTML")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🔔 <b>ВЫВОД #{wid}</b>\n\n"
                f"👤 {u['first_name']} (ID: {u['user_id']})\n"
                f"💎 {crystals} = {rub}₽\n"
                f"Метод: {method}\n"
                f"Кошелёк: <code>{wallet}</code>\n\n"
                f"/approve {wid} | /reject {wid}",
                parse_mode="HTML"
            )
        except Exception:
            pass


@dp.message(Command("withdrawals"))
async def cmd_withdrawals(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    pending = list_withdrawals('pending', 20)
    await m.answer(
        f"⏳ <b>Заявок:</b> {len(pending)}\n\n"
        + "\n".join(f"#{r[0]} — {r[2]}💎 = {r[3]}₽ (ID: {r[1]})" for r in pending[:10]),
        parse_mode="HTML"
    )


@dp.message(Command("approve"))
async def cmd_approve(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("/approve ID")
        return
    try:
        wid = int(parts[1])
    except ValueError:
        await m.answer("❌")
        return
    w = get_withdrawal(wid)
    if not w:
        await m.answer("❌ Не найдено")
        return
    update_withdrawal(wid, 'approved', admin_id=m.from_user.id)
    try:
        await bot.send_message(w['user_id'],
            f"✅ <b>ВЫВОД #{wid} ОДОБРЕН!</b>\n\n💎 {w['crystals']} = {w['payout_rub']}₽",
            parse_mode="HTML")
    except Exception:
        pass
    await m.answer(f"✅ #{wid} одобрено")


@dp.message(Command("reject"))
async def cmd_reject(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    parts = m.text.split(maxsplit=2)
    if len(parts) < 2:
        await m.answer("/reject ID [причина]")
        return
    try:
        wid = int(parts[1])
    except ValueError:
        await m.answer("❌")
        return
    reason = parts[2] if len(parts) > 2 else "Отклонено"
    w = get_withdrawal(wid)
    if not w:
        await m.answer("❌")
        return
    update_crystals(w['user_id'], w['crystals'])
    update_withdrawal(wid, 'rejected', admin_id=m.from_user.id, comment=reason)
    try:
        await bot.send_message(w['user_id'],
            f"❌ <b>ВЫВОД #{wid} ОТКЛОНЁН</b>\n\nКристаллы возвращены\nПричина: {reason}",
            parse_mode="HTML")
    except Exception:
        pass
    await m.answer(f"❌ #{wid} отклонено")


# ============================================================
# 📊 ГРАФИК
# ============================================================
@dp.callback_query(F.data == "graph")
async def cb_graph(c: CallbackQuery):
    u = get_user(c.from_user.id)
    history = [1000, 1200, 900, 1500, 800, u['balance']]
    buf = make_balance_graph(history)
    if buf is None:
        await c.answer("❌ Pillow не установлен")
        return
    photo = BufferedInputFile(buf.read(), filename="graph.png")
    await c.message.answer_photo(photo,
        caption=f"📊 <b>График</b>\n\n💰 {fmt(u['balance'])}",
        parse_mode="HTML")
    await c.answer()


# ============================================================
# 👨‍💼 АДМИНКА
# ============================================================
def is_admin(uid):
    return uid in ADMIN_IDS


@dp.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        return
    await m.answer("👨‍💼 <b>АДМИН</b>\n\n/dash /dashstats /dashtop /withdrawals /remind",
                   parse_mode="HTML")


@dp.message(Command("dash"))
async def cmd_dash(m: Message):
    if not is_admin(m.from_user.id):
        return
    h = get_house_stats()
    text = (
        f"📊 <b>ДАШБОРД</b>\n\n"
        f"👥 Игроков: <b>{h['players']}</b>\n"
        f"💰 Выиграно: {fmt(h['total_won'])}\n"
        f"💸 Проиграно: {fmt(h['total_lost'])}\n"
        f"📈 <b>Доход: {fmt(h['profit'])}</b>\n"
        f"🎯 House edge: <b>{h['house_edge']:.2f}%</b>"
    )
    await m.answer(text, parse_mode="HTML")


@dp.message(Command("dashtop"))
async def cmd_dashtop(m: Message):
    if not is_admin(m.from_user.id):
        return
    rows = get_top_by_profit(10)
    text = "💰 <b>ТОП</b>\n\n"
    for i, (name, un, lost, won, profit) in enumerate(rows):
        text += f"{i+1}. {name or 'Аноним'} — <b>+{fmt(profit)}</b>\n"
    await m.answer(text, parse_mode="HTML")


@dp.message(Command("remind"))
async def cmd_remind(m: Message):
    if not is_admin(m.from_user.id):
        return
    users = get_inactive_users(3)
    sent = 0
    for uid, name in users:
        try:
            await bot.send_message(uid, get_inactive_reminder(name or "игрок"), parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass
    await m.answer(f"📢 Отправлено {sent}")


@dp.message(Command("autopost"))
async def cmd_autopost(m: Message):
    if not is_admin(m.from_user.id):
        return
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("/autopost @канал")
        return
    channel = parts[1].strip()
    me = await bot.get_me()
    link = f"https://t.me/{me.username}"
    await m.answer(f"📢 Запущено в {channel}")

    async def poster():
        while True:
            try:
                text = get_random_promo(link)
                await bot.send_message(channel, text, parse_mode="HTML")
                await asyncio.sleep(3600)
            except Exception as e:
                print(f"Autopost error: {e}")
                await asyncio.sleep(600)

    asyncio.create_task(poster())


# ============================================================
# УНИВЕРСАЛЬНЫЙ ПЕРЕХВАТ
# ============================================================
@dp.message(F.text & ~F.text.startswith("/"))
async def catch_all(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    current = await state.get_state()
    if current is None:
        return
    text = m.text.strip()
    if " " in text:
        code, amount = text.split(" ", 1)
        try:
            amount = int(amount)
            make_promo(code, amount, 100)
            await m.answer(f"✅ Промокод {code.upper()} на {amount}$", parse_mode="HTML")
        except ValueError:
            users = admin_broadcast_users()
            sent = 0
            for uid in users:
                try:
                    await bot.send_message(uid, text, parse_mode="HTML")
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
            await m.answer(f"📢 Отправлено: {sent}")
    else:
        await m.answer("❌ Формат: КОД СУММА")
    await state.clear()


# ============================================================
# ЗАПУСК
# ============================================================
async def main():
    init_db()
    dp.callback_query.middleware(AntiSpamMiddleware())
    print("🎰 CASINO ROYALE 8.0 запущен!")
    print("✅ Игры: 20+")
    print("✅ Платежи: Stars, CryptoBot, ручная")
    print("✅ Вывод: 1💎 = 2₽")
    print("✅ Фичи: VIP, кэшбэк, рефералы, турниры")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
