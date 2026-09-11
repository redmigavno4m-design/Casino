import asyncio
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, DAILY_BONUS
from database import (
    init_db, get_user, update_balance,
    record_game, update_daily_bonus, top_players
)
from games import play_slots, play_roulette, play_dice, play_coin
from keyboards import main_menu, back_menu, bet_menu

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def fmt(amount):
    return f"{amount:,}".replace(",", " ") + "$"


def header(u):
    return f"👤 <b>{u['first_name'] or 'Игрок'}</b>\n💰 Баланс: <b>{fmt(u['balance'])}</b>\n"


async def edit(call, text, kb=None):
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")


@dp.message(CommandStart())
async def start(m: Message):
    u = get_user(m.from_user.id, m.from_user.username, m.from_user.first_name)
    text = (
        f"🎰 <b>CASINO ROYALE</b>\n\n"
        f"{header(u)}\n"
        f"🎮 Игр: <b>{u['games']}</b> | 🏆 Побед: <b>{u['wins']}</b>\n\n"
        f"Выбирай игру!"
    )
    await m.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@dp.callback_query(F.data == "main_menu")
async def cb_main(c: CallbackQuery):
    u = get_user(c.from_user.id)
    text = f"🎰 <b>CASINO ROYALE</b>\n\n{header(u)}\nВыбирай игру:"
    await edit(c, text, main_menu())
    await c.answer()


@dp.callback_query(F.data == "noop")
async def cb_noop(c: CallbackQuery):
    await c.answer("Возьми бонус 🎁", show_alert=True)


@dp.callback_query(F.data == "profile")
async def cb_profile(c: CallbackQuery):
    u = get_user(c.from_user.id)
    wr = (u['wins'] / u['games'] * 100) if u['games'] else 0
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"💰 Баланс: <b>{fmt(u['balance'])}</b>\n"
        f"🎮 Игр: <b>{u['games']}</b>\n"
        f"🏆 Побед: <b>{u['wins']}</b>\n"
        f"📊 Винрейт: <b>{wr:.1f}%</b>\n"
        f"💎 Рекорд: <b>{fmt(u['biggest_win'])}</b>\n"
        f"📈 Выиграно: <b>{fmt(u['total_won'])}</b>\n"
        f"📉 Проиграно: <b>{fmt(u['total_lost'])}</b>"
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
    else:
        record_game(c.from_user.id, bet, 0)
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
    else:
        record_game(c.from_user.id, bet, 0)
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
    else:
        record_game(c.from_user.id, bet, 0)
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
    else:
        record_game(c.from_user.id, bet, 0)
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


async def main():
    init_db()
    print("🎰 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
