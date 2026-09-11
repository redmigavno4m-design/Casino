from database import (
    get_user, update_crystals, create_withdrawal,
    pending_withdrawals_count
)
from config import (
    SELL_RATE_RUB, SELL_RATE_USDT,
    MIN_WITHDRAW_CRYSTALS, MAX_WITHDRAW_CRYSTALS,
    WITHDRAW_DELAY_HOURS, WITHDRAW_METHODS,
    MANUAL_WITHDRAW_CONTACT
)


def calc_payout(crystals):
    return round(crystals * SELL_RATE_RUB, 2), round(crystals * SELL_RATE_USDT, 4)


def validate_withdraw(user_id, crystals):
    if crystals < MIN_WITHDRAW_CRYSTALS:
        return False, f"❌ Минимум: {MIN_WITHDRAW_CRYSTALS}💎"
    if crystals > MAX_WITHDRAW_CRYSTALS:
        return False, f"❌ Максимум: {MAX_WITHDRAW_CRYSTALS}💎"
    u = get_user(user_id)
    if u['crystals'] < crystals:
        return False, f"❌ У тебя {u['crystals']}💎"
    if pending_withdrawals_count(user_id) >= 2:
        return False, "⏳ Уже 2 заявки. Дождись обработки."
    return True, ""


def request_withdraw(user_id, crystals, method, wallet):
    ok, err = validate_withdraw(user_id, crystals)
    if not ok:
        return False, None, err

    rub, usdt = calc_payout(crystals)
    update_crystals(user_id, -crystals)
    wid = create_withdrawal(user_id, crystals, rub, usdt, method, wallet)
    return True, wid, f"✅ Заявка #{wid} создана!"


def withdraw_info_text():
    return (
        f"💎 <b>ВЫВОД СРЕДСТВ</b>\n\n"
        f"<b>Курс вывода:</b>\n"
        f"• 1💎 = {SELL_RATE_RUB}₽\n"
        f"• 1💎 = {SELL_RATE_USDT} USDT\n\n"
        f"<b>Лимиты:</b>\n"
        f"• Минимум: {MIN_WITHDRAW_CRYSTALS}💎\n"
        f"• Максимум: {MAX_WITHDRAW_CRYSTALS}💎\n\n"
        f"<b>Время:</b> до {WITHDRAW_DELAY_HOURS}ч\n\n"
        f"💵 Ручной: {MANUAL_WITHDRAW_CONTACT}"
    )


def status_emoji(s):
    return {'pending':'⏳', 'approved':'✅', 'rejected':'❌', 'processing':'🔄'}.get(s, '❓')


def status_name(s):
    return {'pending':'Ожидает', 'approved':'Выплачено',
            'rejected':'Отклонено', 'processing':'Обрабатывается'}.get(s, s)
