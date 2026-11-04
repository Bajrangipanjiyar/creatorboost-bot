# -*- coding: utf-8 -*-
"""
CreatorBoost Bot - Vercel Serverless Webhook Handler
Accepts incoming Telegram Webhook updates via HTTP POST and processes them through aiogram 3.x Dispatcher.
"""

import json
import asyncio
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import settings
from database.connection import init_db
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.rate_limit import RateLimitMiddleware
from handlers import (
    start, channel, earn, promote, wallet,
    referral, daily, ads_handler, payment, admin
)

# Global bot and dispatcher instances for serverless warm execution
_bot: Bot = None
_dp: Dispatcher = None
_db_initialized = False

def get_bot_and_dp():
    global _bot, _dp
    if _bot is None:
        _bot = Bot(token=settings.BOT_TOKEN)
        _dp = Dispatcher(storage=MemoryStorage())

        # Middlewares
        _dp.message.middleware(AuthMiddleware())
        _dp.callback_query.middleware(AuthMiddleware())
        _dp.message.middleware(RateLimitMiddleware())
        _dp.callback_query.middleware(RateLimitMiddleware())

        # Routers
        _dp.include_router(admin.router)
        _dp.include_router(start.router)
        _dp.include_router(channel.router)
        _dp.include_router(earn.router)
        _dp.include_router(promote.router)
        _dp.include_router(wallet.router)
        _dp.include_router(referral.router)
        _dp.include_router(daily.router)
        _dp.include_router(ads_handler.router)
        _dp.include_router(payment.router)

    return _bot, _dp

async def process_telegram_update(update_dict: dict) -> None:
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True

    bot, dp = get_bot_and_dp()
    telegram_update = Update(**update_dict)
    await dp.feed_update(bot=bot, update=telegram_update)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {
            "status": "online",
            "service": "CreatorBoost Telegram Bot",
            "mode": "Vercel Serverless Webhook"
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_POST(self):
        """Telegram webhook update listener."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_response(400)
                self.end_headers()
                return

            post_data = self.rfile.read(content_length)
            update_dict = json.loads(post_data.decode("utf-8"))

            # Run async processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_telegram_update(update_dict))
            finally:
                loop.close()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
