import aiohttp
from config import CRYPTOBOT_TOKEN, CRYPTOBOT_ASSET, MANUAL_CRYSTAL_PACKS, MANUAL_PAYMENT_CONTACT

CRYPTO_API = "https://pay.crypt.bot/api"


def _headers():
    return {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}


async def create_crypto_invoice(user_id, pack_index, crystals, rub_price):
    if not CRYPTOBOT_TOKEN:
        return None, None
    usdt = round(rub_price / 95, 2)
    payload = {"asset": CRYPTOBOT_ASSET, "amount": str(usdt),
               "description": f"💎 {crystals} кристаллов",
               "payload": f"crypto_{user_id}_{pack_index}_{crystals}"}
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{CRYPTO_API}/createInvoice", json=payload, headers=_headers()) as r:
            if r.status != 200:
                return None, None
            data = await r.json()
            if not data.get('ok'):
                return None, None
            inv = data['result']
            return inv['invoice_id'], inv['bot_invoice_url']


async def check_crypto_invoice(invoice_id):
    if not CRYPTOBOT_TOKEN:
        return None
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{CRYPTO_API}/getInvoices",
                         params={"invoice_ids": str(invoice_id)},
                         headers=_headers()) as r:
            if r.status != 200:
                return None
            data = await r.json()
            if not data.get('ok'):
                return None
            items = data['result'].get('items', [])
            return items[0].get('status') if items else None


def manual_payment_text():
    text = f"💵 <b>РУЧНАЯ ОПЛАТА</b>\n\nНапиши админу: <b>{MANUAL_PAYMENT_CONTACT}</b>\n\n<b>Пакеты:</b>\n"
    for c, r in MANUAL_CRYSTAL_PACKS:
        text += f"💎 {c} — {r}₽\n"
    return text
