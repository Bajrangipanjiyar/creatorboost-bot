# -*- coding: utf-8 -*-
"""
Authentication & Ban Middleware for CreatorBoost Bot
Ensures all Telegram users are registered, resolves language, and blocks banned users.
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
from database.connection import async_session_factory
from database.crud import get_or_create_user
from utils.logger import logger

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_from_user: TgUser = data.get("event_from_user")
        if not event_from_user:
            return await handler(event, data)

        async with async_session_factory() as session:
            # Check referral argument if /start command
            referrer_id = None
            if isinstance(event, Message) and event.text and event.text.startswith("/start"):
                parts = event.text.split()
                if len(parts) > 1 and parts[1].startswith("ref_"):
                    try:
                        referrer_id = int(parts[1].replace("ref_", "").strip())
                    except ValueError:
                        referrer_id = None

            user, is_new = await get_or_create_user(
                session=session,
                user_id=event_from_user.id,
                username=event_from_user.username,
                full_name=event_from_user.full_name,
                referrer_id=referrer_id
            )

            # Block banned users
            if user.is_banned:
                ban_text = "🚫 <b>Account Suspended:</b> Your account has been banned due to fair-play violations."
                if isinstance(event, Message):
                    await event.answer(ban_text, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Your account is banned.", show_alert=True)
                return

            # Inject user and language into handler data
            data["user"] = user
            data["lang"] = user.language or "en"
            data["session"] = session

            return await handler(event, data)
