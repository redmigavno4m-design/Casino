"""
🎯 Спортивные игры с настоящими Telegram Dice
"""
import asyncio
from config import (
    DARTS_SECTORS, FOOTBALL_RESULT, BASKETBALL_RESULT,
    BOWLING_RESULT, SLOT_DICE_THRESHOLDS
)


async def roll_dice(bot, chat_id, emoji):
    """
    Бросает настоящий Telegram Dice.
    Возвращает значение (int).
    """
    msg = await bot.send_dice(chat_id=chat_id, emoji=emoji)
    # Ждём завершения анимации
    await asyncio.sleep(4)
    return msg.dice.value


# ============================================================
# 🎯 ДАРТС
# ============================================================
async def play_darts(bot, chat_id, bet, bet_on):
    """
    bet_on: 'center' (максимум), 'middle', 'any'
    Сектора: 1-6 (в эмодзи 🎯)
    """
    value = await roll_dice(bot, chat_id, "🎯")

    if bet_on == 'center':
        # Только 6 (яблочко) → x5
        mult = 5.0 if value == 6 else 0
        target = "в яблочко 🎯"
    elif bet_on == 'middle':
        # 4-6 (внутренний круг) → x2
        mult = 2.0 if value >= 4 else 0
        target = "внутренний круг 🎯"
    else:  # any
        # 3-6 (в мишень) → x1.5
        mult = 1.5 if value >= 3 else 0
        target = "в мишень"

    win = int(bet * mult)
    return {
        'value': value,
        'win': win,
        'mult': mult,
        'target': target,
        'result_text': {
            1: "😢 Промах — мимо мишени!",
            2: "😢 Промах!",
            3: "🎯 Попал в край мишени!",
            4: "🎯 Хороший бросок!",
            5: "🎯 Отличный бросок!",
            6: "🎯🎯 В ЯБЛОЧКО!",
        }.get(value, "")
    }


# ============================================================
# ⚽ ФУТБОЛ (пенальти)
# ============================================================
async def play_football(bot, chat_id, bet, bet_on):
    """
    bet_on: 'goal' (гол), 'topcorner' (в девятку)
    """
    value = await roll_dice(bot, chat_id, "⚽")

    if bet_on == 'topcorner':
        # 5 = в девятку → x4
        mult = 4.0 if value == 5 else 0
        target = "в девятку 🥅"
    else:  # goal
        # 3-5 = гол → x2, 5 = x2.5
        if value == 5:
            mult = 4.0
        elif value >= 3:
            mult = 1.9
        else:
            mult = 0
        target = "гол ⚽"

    win = int(bet * mult)
    return {
        'value': value,
        'win': win,
        'mult': mult,
        'target': target,
        'result_text': {
            1: "❌ Вратарь поймал!",
            2: "❌ Мяч в перекладину!",
            3: "⚽ Гол!",
            4: "⚽ Красивый гол!",
            5: "⚽ В ДЕВЯТКУ! Гол!",
        }.get(value, "")
    }


# ============================================================
# 🏀 БАСКЕТБОЛ
# ============================================================
async def play_basketball(bot, chat_id, bet, bet_on):
    """
    bet_on: 'shot' (обычный), 'three' (трёхочковый)
    """
    value = await roll_dice(bot, chat_id, "🏀")

    if bet_on == 'three':
        # 5 = трёхочковый → x4.5
        mult = 4.5 if value == 5 else 0
        target = "трёхочковый 🏀"
    else:
        if value == 5:
            mult = 4.5
        elif value >= 3:
            mult = 1.9
        else:
            mult = 0
        target = "бросок 🏀"

    win = int(bet * mult)
    return {
        'value': value,
        'win': win,
        'mult': mult,
        'target': target,
        'result_text': {
            1: "❌ Промах!",
            2: "❌ Мяч в кольцо не попал!",
            3: "🏀 Попал!",
            4: "🏀 Чистый бросок!",
            5: "🏀 ТРЁХОЧКОВЫЙ!",
        }.get(value, "")
    }


# ============================================================
# 🎳 БОУЛИНГ
# ============================================================
async def play_bowling(bot, chat_id, bet, bet_on):
    """
    bet_on: 'strike' (страйк), 'any'
    """
    value = await roll_dice(bot, chat_id, "🎳")

    if bet_on == 'strike':
        # 6 = все кегли → x5
        mult = 5.0 if value == 6 else 0
        target = "СТРАЙК 🎳"
    else:
        if value == 6:
            mult = 5.0
        elif value == 5:
            mult = 2.8
        elif value == 4:
            mult = 1.9
        elif value == 3:
            mult = 1.2
        elif value == 2:
            mult = 0.5
        else:
            mult = 0
        target = "попадание 🎳"

    win = int(bet * mult)
    return {
        'value': value,
        'win': win,
        'mult': mult,
        'target': target,
        'result_text': {
            1: "😢 Промах!",
            2: "😐 1 кегля.",
            3: "🙂 3 кегли.",
            4: "😊 5 кеглей!",
            5: "😃 8 кеглей!",
            6: "🎳🎳 СТРАЙК!",
        }.get(value, "")
    }


# ============================================================
# 🎰 СЛОТ-МАШИНА (Telegram Dice 🎰)
# ============================================================
async def play_slot_dice(bot, chat_id, bet):
    """
    Настоящий Telegram-слот. Значения 1-64.
    """
    value = await roll_dice(bot, chat_id, "🎰")

    if value >= 64:
        mult = 50.0
        text = "🎰🎰🎰 ДЖЕКПОТ x50!"
    elif value >= 61:
        mult = 10.0
        text = "🎰 x10!"
    elif value >= 49:
        mult = 3.0
        text = "🎰 x3!"
    elif value >= 33:
        mult = 1.5
        text = "🎰 x1.5"
    else:
        mult = 0
        text = "😢 Мимо"

    win = int(bet * mult)
    return {
        'value': value,
        'win': win,
        'mult': mult,
        'result_text': text
    }
