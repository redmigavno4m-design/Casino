import random

PROMO_TEXTS = [
    "🎰 <b>Новые игроки получают 1000$!</b>\n\n{link}",
    "🎁 <b>Ежедневный бонус +50$!</b>\n\n{link}",
    "🏆 <b>Турнир с призом 10000$!</b>\n\n{link}",
    "💰 <b>20+ игр, честные коэффициенты!</b>\n\n{link}",
    "🎡 <b>Колесо фортуны — до 1000$!</b>\n\n{link}",
]


def get_random_promo(link):
    return random.choice(PROMO_TEXTS).format(link=link)


def get_inactive_reminder(name):
    return (
        f"👋 <b>Привет, {name}!</b>\n\n"
        f"🎁 Ежедневный бонус +50$!\n"
        f"🎡 Колесо доступно!\n\n"
        f"Заходи 👇"
    )
