# -*- coding: utf-8 -*-
"""
Rate-Limiting Middleware
Prevents aggressive clicking or flood spam on Telegram bot handlers.
"""

from typing import Callable, Dict, Any, Awaitable
from datetime import datetime, timezone
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery
from cachetools import TTLCache

# Global cache: user_id -> timestamp of last interaction
action_cache = TTLCache(maxsize=10000, ttl=1.0)

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        now = datetime.now(timezone.utc).timestamp()
        last_time = action_cache.get(user.id)

        # Allow maximum 1 request per 0.5s for normal interactions
        if last_time and (now - last_time < 0.4):
            if isinstance(event, CallbackQuery):
                await event.answer("⚡ Slow down! Processing...", show_alert=False)
            return

        action_cache[user.id] = now
        return await handler(event, data)
