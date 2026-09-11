import asyncio
import random


async def animate_slots(bot, chat_id, message_id, final_reels, delay=0.15, rounds=12):
    symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣']
    for _ in range(rounds):
        current = [random.choice(symbols) for _ in range(3)]
        bar = " | ".join(current)
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                text=f"🎰 <b>Крутим...</b>\n\n<code>{bar}</code>", parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(delay)
    bar = " | ".join(final_reels)
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
            text=f"🎰 <b>Стоп</b>\n\n<code>{bar}</code>", parse_mode="HTML")
    except Exception:
        pass
