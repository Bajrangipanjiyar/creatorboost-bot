# -*- coding: utf-8 -*-
"""
Monetization & "Watch Ad, Earn Coins" Handler
Integrates AdsGram / custom sponsored destination with daily frequency caps.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from ads.manager import AdManager
from ads.adsgram import AdsGramService
from services.i18n import t
from bot.keyboards.inline import get_back_button

router = Router(name="ads")

@router.callback_query(F.data == "menu_watch_ad")
async def handle_watch_ad_prompt(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    is_eligible, views_today, daily_limit = await AdManager.check_watch_ad_eligibility(session, user.id)

    if not is_eligible:
        limit_text = (
            "⏳ <b>Daily Limit Reached!</b>\n\n"
            f"You have watched all <b>{daily_limit}/{daily_limit}</b> sponsored ads for today.\n"
            "More ads will become available at midnight UTC!"
        ) if lang == "en" else (
            "⏳ <b>दैनिक सीमा समाप्त!</b>\n\n"
            f"आप आज के सभी <b>{daily_limit}/{daily_limit}</b> प्रायोजित विज्ञापन देख चुके हैं।\n"
            "कल पुनः नए विज्ञापन उपलब्ध होंगे!"
        )
        await callback.message.edit_text(text=limit_text, reply_markup=get_back_button(lang), parse_mode="HTML")
        await callback.answer()
        return

    ad_url = AdsGramService.get_ad_url(user.id)
    prompt_text = (
        "📺 <b>Watch Sponsored Ad & Earn Coins</b>\n\n"
        "• <b>Reward:</b> +15 Coins per Ad\n"
        f"• <b>Today's Progress:</b> {views_today} / {daily_limit} watched\n\n"
        "1. Click the button below to view the sponsor's link.\n"
        "2. Stay on the page for at least 15 seconds.\n"
        "3. Click <b>[Claim Ad Coins]</b> below."
    ) if lang == "en" else (
        "📺 <b>विज्ञापन देखें और सिक्के कमाएं</b>\n\n"
        "• <b>इनाम:</b> +15 सिक्के प्रति विज्ञापन\n"
        f"• <b>आज की प्रगति:</b> {views_today} / {daily_limit} देखे गए\n\n"
        "1. नीचे दिए गए लिंक पर क्लिक करें और विज्ञापन देखें।\n"
        "2. कम से कम 15 सेकंड प्रतीक्षा करें।\n"
        "3. नीचे <b>[सिक्के क्लेम करें]</b> पर क्लिक करें।"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Open Sponsored Ad", url=ad_url)],
            [InlineKeyboardButton(text="✅ Claim Ad Coins", callback_data="claim_watch_ad")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_to_menu")]
        ]
    )

    await callback.message.edit_text(text=prompt_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "claim_watch_ad")
async def handle_claim_ad_coins(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    reward = await AdManager.claim_watch_ad_reward(session, user.id)

    if reward:
        success_msg = f"🎉 <b>Reward Claimed!</b> +{reward} coins have been added to your wallet!"
        await callback.message.edit_text(text=success_msg, reply_markup=get_back_button(lang), parse_mode="HTML")
        await callback.answer(f"+{reward} Coins added!", show_alert=True)
    else:
        await callback.answer("Daily ad limit reached or already claimed.", show_alert=True)
