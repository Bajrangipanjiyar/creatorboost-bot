# -*- coding: utf-8 -*-
"""
Daily Bonus & Streak Reward Handler
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import claim_daily_bonus
from services.i18n import t
from bot.keyboards.inline import get_back_button

router = Router(name="daily")

@router.callback_query(F.data == "menu_daily")
async def handle_daily_bonus(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    success, coins, streak, msg = await claim_daily_bonus(session, user.id)

    if success:
        text = t("daily_bonus_claimed", lang, streak=streak, coins=coins)
        await callback.message.edit_text(text=text, reply_markup=get_back_button(lang), parse_mode="HTML")
        await callback.answer(f"🎉 +{coins} Coins claimed!", show_alert=True)
    else:
        text = t("daily_bonus_cooldown", lang, time_left=msg, streak=streak)
        await callback.message.edit_text(text=text, reply_markup=get_back_button(lang), parse_mode="HTML")
        await callback.answer("Daily bonus already claimed for today.", show_alert=False)
