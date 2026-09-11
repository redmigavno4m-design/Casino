"""
Реалистичные анимации для Telegram.
Использует настоящий send_dice и редактирование сообщений.
"""
import asyncio
import random


async def roll_real_dice(bot, chat_id, emoji="🎲"):
    """
    Отправляет настоящий Telegram Dice.
    Возвращает значение 1-6 (или 1-5 для баскетбола/дартса).
    """
    msg = await bot.send_dice(chat_id=chat_id, emoji=emoji)
    # Ждём завершения анимации (у кубика ~4 секунды)
    await asyncio.sleep(4)
    return msg.dice.value


async def animate_slots(bot, chat_id, message_id, final_reels, delay=0.15, rounds=12):
    """
    Анимация слотов через редактирование сообщения.
    Показывает крутящиеся барабаны.
    """
    symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣']
    for i in range(rounds):
        # На последних итерациях показываем финальные символы
        if i >= rounds - 3:
            current = final_reels[:i - (rounds - 3) + 1] + [
                random.choice(symbols) for _ in range(rounds - i - 1 + 3 - (i - (rounds - 3) + 1))
            ]
            current = current[:3]
        else:
            current = [random.choice(symbols) for _ in range(3)]

        bar = " | ".join(current)
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"🎰 <b>Крутим...</b>\n\n<code>{bar}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await asyncio.sleep(delay)

    # Финальный кадр
    final_bar = " | ".join(final_reels)
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"🎰 <b>Барабаны остановились</b>\n\n<code>{final_bar}</code>",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def animate_roulette(bot, chat_id, message_id, final_number, delay=0.08, rounds=20):
    """Анимация рулетки — числа прокручиваются."""
    for _ in range(rounds):
        n = random.randint(0, 36)
        if n == 0:
            icon = "🟢"
        elif n in {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}:
            icon = "🔴"
        else:
            icon = "⚫"
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"🎡 <b>Крутится колесо...</b>\n\n{icon} <b>{n}</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await asyncio.sleep(delay)

    if final_number == 0:
        icon = "🟢"
    elif final_number in {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}:
        icon = "🔴"
    else:
        icon = "⚫"

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"🎡 <b>Выпало:</b>\n\n{icon} <b>{final_number}</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def animate_coin(bot, chat_id, message_id, final_side):
    """Анимация монетки — крутится орёл/решка."""
    sides = ['🦅', '🪙']
    for i in range(10):
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"🪙 <b>Монетка в воздухе...</b>\n\n{sides[i % 2]}",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await asyncio.sleep(0.15)

    final = '🦅 Орёл' if final_side == 'eagle' else '🪙 Решка'
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"🪙 <b>Упала!</b>\n\n<b>{final}</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
