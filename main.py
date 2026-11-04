# -*- coding: utf-8 -*-
"""
CreatorBoost Bot - Main Entry Point
Configures aiogram 3.x dispatcher, registers routers and middlewares, and launches async long-polling.
"""

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database.connection import init_db
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.rate_limit import RateLimitMiddleware
from handlers import (
    start, channel, earn, promote, wallet,
    referral, daily, ads_handler, payment, admin
)
from utils.logger import logger

async def set_bot_commands(bot: Bot) -> None:
    """Sets user commands visible in Telegram menu button."""
    commands = [
        BotCommand(command="start", description="🚀 Open Main Menu / Restart Bot"),
        BotCommand(command="admin", description="👑 Admin Control Center (Admins only)")
    ]
    await bot.set_my_commands(commands)

async def main() -> None:
    logger.info("Initializing CreatorBoost Bot platform...")

    # 1. Initialize SQLite / PostgreSQL Database tables
    try:
        await init_db()
        logger.info("Database schema verified and initialized.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        sys.exit(1)

    # 2. Instantiate Bot & Dispatcher with MemoryStorage
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Register Global Middlewares
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())

    # 4. Attach Feature Routers
    dp.include_router(admin.router)       # Place admin before general matching
    dp.include_router(start.router)
    dp.include_router(channel.router)
    dp.include_router(earn.router)
    dp.include_router(promote.router)
    dp.include_router(wallet.router)
    dp.include_router(referral.router)
    dp.include_router(daily.router)
    dp.include_router(ads_handler.router)
    dp.include_router(payment.router)

    # 5. Set standard Telegram commands
    try:
        await set_bot_commands(bot)
    except Exception as e:
        logger.warning(f"Could not set Telegram bot commands: {e}")

    # 6. Delete webhook if leftover and start long polling
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info(f"Bot authenticated as @{me.username} ({me.id}). Ready for creators!")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()
        logger.info("Bot session closed safely.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("CreatorBoost Bot stopped.")
