# -*- coding: utf-8 -*-
"""
Referral System Handler
Tracks referral links and rewards users when invitees verify and engage.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import get_referral_stats
from services.i18n import t

router = Router(name="referral")

@router.callback_query(F.data == "menu_referral")
async def handle_referral_menu(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user.id}"
    stats = await get_referral_stats(session, user.id)

    card_text = t(
        "referral_card",
        lang,
        reward=settings.REFERRAL_BONUS,
        threshold=settings.REFERRAL_TASK_THRESHOLD,
        ref_link=ref_link,
        total_referred=stats["total_referred"],
        qualified=stats["qualified"],
        total_coins=stats["total_coins"]
    )

    share_text = f"Join CreatorBoost to grow your YouTube channel! Earn free views and subscribers: {ref_link}"
    share_url = f"https://t.me/share/url?url={ref_link}&text=Boost+your+YouTube+Channel+with+CreatorBoost!"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Share Link with Friends", url=share_url)],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_to_menu")]
        ]
    )

    await callback.message.edit_text(text=card_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
