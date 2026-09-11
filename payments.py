from config import CRYSTAL_PACKS
from aiogram.types import LabeledPrice


async def send_stars_invoice(bot, chat_id, pack_index):
    if not (0 <= pack_index < len(CRYSTAL_PACKS)):
        return None
    crystals, stars_price, rub_price, bonus = CRYSTAL_PACKS[pack_index]
    total = crystals + int(crystals * bonus / 100)
    prices = [LabeledPrice(label=f"{total}💎", amount=stars_price)]
    return await bot.send_invoice(
        chat_id=chat_id,
        title=f"💎 {total} кристаллов",
        description=f"Покупка {total} кристаллов",
        payload=f"stars_{pack_index}_{total}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="casino_stars"
    )


def format_pack(idx):
    crystals, stars, rub, bonus = CRYSTAL_PACKS[idx]
    total = crystals + int(crystals * bonus / 100)
    return f"💎 {total}{f' +{bonus}%' if bonus else ''}"


def format_price_stars(idx):
    return f"{CRYSTAL_PACKS[idx][1]} ⭐"
