from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from antifraud import is_spam


class AntiSpamMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery):
            if is_spam(event.from_user.id):
                try:
                    await event.answer("⚠️ Слишком быстро!", show_alert=True)
                except Exception:
                    pass
                return
        return await handler(event, data)
