import asyncio


async def roll_dice(bot, chat_id, emoji):
    msg = await bot.send_dice(chat_id=chat_id, emoji=emoji)
    await asyncio.sleep(4)
    return msg.dice.value


async def play_darts(bot, chat_id, bet, bet_on):
    v = await roll_dice(bot, chat_id, "🎯")
    if bet_on == 'center':
        mult = 5.0 if v == 6 else 0
    elif bet_on == 'middle':
        mult = 2.0 if v >= 4 else 0
    else:
        mult = 1.5 if v >= 3 else 0
    return {'value': v, 'win': int(bet * mult), 'mult': mult,
            'result_text': {1:"😢 Промах!", 2:"😢 Мимо!", 3:"🎯 В мишень!",
                            4:"🎯 Хороший!", 5:"🎯 Отличный!", 6:"🎯🎯 В ЯБЛОЧКО!"}.get(v, "")}


async def play_football(bot, chat_id, bet, bet_on):
    v = await roll_dice(bot, chat_id, "⚽")
    if bet_on == 'topcorner':
        mult = 4.0 if v == 5 else 0
    else:
        mult = 4.0 if v == 5 else (1.9 if v >= 3 else 0)
    return {'value': v, 'win': int(bet * mult), 'mult': mult,
            'result_text': {1:"❌ Вратарь!", 2:"❌ Перекладина!", 3:"⚽ Гол!",
                            4:"⚽ Красивый!", 5:"⚽ В ДЕВЯТКУ!"}.get(v, "")}


async def play_basketball(bot, chat_id, bet, bet_on):
    v = await roll_dice(bot, chat_id, "🏀")
    if bet_on == 'three':
        mult = 4.5 if v == 5 else 0
    else:
        mult = 4.5 if v == 5 else (1.9 if v >= 3 else 0)
    return {'value': v, 'win': int(bet * mult), 'mult': mult,
            'result_text': {1:"❌ Промах!", 2:"❌ Мимо!", 3:"🏀 Попал!",
                            4:"🏀 Чистый!", 5:"🏀 ТРЁХОЧКОВЫЙ!"}.get(v, "")}


async def play_bowling(bot, chat_id, bet, bet_on):
    v = await roll_dice(bot, chat_id, "🎳")
    if bet_on == 'strike':
        mult = 5.0 if v == 6 else 0
    else:
        mult = {1:0, 2:0.5, 3:1.2, 4:1.9, 5:2.8, 6:5.0}.get(v, 0)
    return {'value': v, 'win': int(bet * mult), 'mult': mult,
            'result_text': {1:"😢 Промах!", 2:"😐 1 кегля", 3:"🙂 3 кегли",
                            4:"😊 5 кеглей", 5:"😃 8 кеглей", 6:"🎳🎳 СТРАЙК!"}.get(v, "")}


async def play_slot_dice(bot, chat_id, bet):
    v = await roll_dice(bot, chat_id, "🎰")
    if v >= 64:
        mult, text = 50.0, "🎰🎰🎰 ДЖЕКПОТ x50!"
    elif v >= 61:
        mult, text = 10.0, "🎰 x10!"
    elif v >= 49:
        mult, text = 3.0, "🎰 x3!"
    elif v >= 33:
        mult, text = 1.5, "🎰 x1.5"
    else:
        mult, text = 0, "😢 Мимо"
    return {'value': v, 'win': int(bet * mult), 'mult': mult, 'result_text': text}
