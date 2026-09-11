BOT_TOKEN = "8815985502:AAEAhmVxCqvQCDkudv5UnuIXmeFoLNri8Ro"
START_BALANCE = 1000
DAILY_BONUS = 50
MIN_BET = 50

# Покер
POKER_RAKE = 0.05  # 5% казино забирает от банка

# Дуэли
DUEL_RAKE = 0.05
DUEL_HP = 100

# Промокоды: код -> сумма
PROMOCODES = {
    "WELCOME": 500,
    "CASINO1000": 1000,
    "LUCKY777": 777,
    "BONUS500": 500,
}

# Колесо
WHEEL_PRIZES = [0, 50, 100, 200, 500, 1000, 250, 100]
WHEEL_COOLDOWN = 24 * 60 * 60

# Уровни
LEVELS = [
    (0, "🥉 Новичок", 0),
    (100, "🥈 Игрок", 100),
    (500, "🥇 Опытный", 300),
    (1500, "💎 Профи", 500),
    (5000, "👑 Мастер", 1000),
    (15000, "🏆 Легенда", 5000),
    (50000, "🌟 Король", 10000),
]
