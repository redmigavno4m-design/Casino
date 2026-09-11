TEXTS = {
    "welcome": {"ru": "🎰 Добро пожаловать!", "en": "🎰 Welcome!", "uz": "🎰 Xush kelibsiz!"},
    "menu": {"ru": "⬅️ В меню", "en": "⬅️ Menu", "uz": "⬅️ Menyu"},
}


def t(key, lang="ru"):
    e = TEXTS.get(key, {})
    return e.get(lang, e.get("ru", key))


def lang_name(lang):
    return {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "uz": "🇺🇿 O'zbekcha"}.get(lang, lang)
