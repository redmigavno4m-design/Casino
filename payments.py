"""
💰 Платежи: Telegram Stars + ЮKassa
"""
import aiohttp
import uuid
import base64
from config import (
    YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY,
    CRYSTAL_PACKS, STARS_TO_RUB
)


# ============================================================
# TELEGRAM STARS
# ============================================================

async def send_stars_invoice(bot, chat_id, pack_index):
    """
    Отправляет счёт на оплату Stars.
    Возвращает ID инвойса.
    """
    if pack_index < 0 or pack_index >= len(CRYSTAL_PACKS):
        return None

    crystals, stars_price, rub_price, bonus = CRYSTAL_PACKS[pack_index]
    total_crystals = crystals + int(crystals * bonus / 100)

    from aiogram.types import LabeledPrice
    prices = [LabeledPrice(label=f"{total_crystals}💎", amount=stars_price)]

    msg = await bot.send_invoice(
        chat_id=chat_id,
        title=f"💎 {total_crystals} кристаллов",
        description=f"Покупка {total_crystals} кристаллов в Casino Royale"
                    + (f" (+{bonus}% бонус)" if bonus else ""),
        payload=f"stars_{pack_index}_{total_crystals}",
        provider_token="",  # для Stars пустой
        currency="XTR",     # XTR = Telegram Stars
        prices=prices,
        start_parameter="casino_stars"
    )
    return msg


# ============================================================
# ЮKASSA
# ============================================================

YOOKASSA_API = "https://api.yookassa.ru/v3/payments"


def _auth_header():
    """Basic Auth для ЮKassa"""
    credentials = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def create_yookassa_payment(user_id, pack_index, return_url):
    """
    Создаёт платёж в ЮKassa.
    Возвращает (payment_id, confirmation_url) или (None, None).
    """
    if pack_index < 0 or pack_index >= len(CRYSTAL_PACKS):
        return None, None

    crystals, stars_price, rub_price, bonus = CRYSTAL_PACKS[pack_index]
    total_crystals = crystals + int(crystals * bonus / 100)

    idempotency_key = str(uuid.uuid4())

    payload = {
        "amount": {
            "value": f"{rub_price}.00",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "description": f"💎 {total_crystals} кристаллов Casino Royale",
        "metadata": {
            "user_id": user_id,
            "pack_index": pack_index,
            "crystals": total_crystals
        }
    }

    headers = {
        "Authorization": _auth_header(),
        "Idempotence-Key": idempotency_key,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(YOOKASSA_API, json=payload, headers=headers) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                print(f"YooKassa error: {resp.status} {text}")
                return None, None
            data = await resp.json()

    payment_id = data.get('id')
    confirm_url = data.get('confirmation', {}).get('confirmation_url')
    return payment_id, confirm_url


async def check_yookassa_payment(payment_id):
    """
    Проверяет статус платежа.
    Возвращает 'succeeded' / 'pending' / 'canceled' / None.
    """
    headers = {"Authorization": _auth_header()}

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{YOOKASSA_API}/{payment_id}", headers=headers) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get('status')


# ============================================================
# ФОРМАТИРОВАНИЕ
# ============================================================

def format_pack(idx):
    """Красивое описание пакета"""
    crystals, stars, rub, bonus = CRYSTAL_PACKS[idx]
    total = crystals + int(crystals * bonus / 100)
    bonus_str = f" +{bonus}% бонус" if bonus else ""
    return f"💎 {total} кристаллов{bonus_str}"


def format_price_stars(idx):
    return f"{CRYSTAL_PACKS[idx][1]} ⭐"


def format_price_rub(idx):
    return f"{CRYSTAL_PACKS[idx][2]} ₽"
