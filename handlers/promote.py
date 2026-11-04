# -*- coding: utf-8 -*-
"""
Video Promotion & Campaign Management Handler
Allows creators to create, monitor, pause, or cancel campaigns with coin refunds.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import (
    get_channel_by_user_id,
    create_campaign,
    get_user_campaigns,
    cancel_campaign,
    toggle_campaign_pause,
    get_system_setting
)
from services.youtube import YouTubeService, YouTubeAPIError, YouTubeQuotaExceededError
from services.i18n import t
from bot.keyboards.inline import get_promote_task_types_keyboard, get_back_button
from bot.states.user_states import PromoteState

router = Router(name="promote")

@router.callback_query(F.data == "menu_promote")
async def handle_promote_menu(callback: CallbackQuery, state: FSMContext, user, lang: str, session: AsyncSession):
    await state.clear()

    # Channel verification check
    channel = await get_channel_by_user_id(session, user.id)
    if not channel or not channel.is_verified:
        unverified_text = (
            "⚠️ <b>Verification Required!</b>\n\n"
            "Please link and verify your YouTube channel before creating campaigns."
        ) if lang == "en" else (
            "⚠️ <b>सत्यापन आवश्यक है!</b>\n\n"
            "कैंपेन बनाने से पहले कृपया अपना YouTube चैनल सत्यापित करें।"
        )
        await callback.message.edit_text(text=unverified_text, reply_markup=get_back_button(lang), parse_mode="HTML")
        await callback.answer()
        return

    intro_text = (
        "🚀 <b>Promote Your YouTube Video</b>\n\n"
        f"💰 <b>Your Available Balance:</b> <code>{user.coins}</code> Coins\n\n"
        "Select an option below to launch a new promotion or manage existing campaigns:"
    ) if lang == "en" else (
        "🚀 <b>अपना YouTube वीडियो प्रमोट करें</b>\n\n"
        f"💰 <b>आपका उपलब्ध बैलेंस:</b> <code>{user.coins}</code> सिक्के\n\n"
        "नया कैंपेन शुरू करने या मौजूदा कैंपेन देखने के लिए नीचे विकल्प चुनें:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Launch New Campaign", callback_data="promote_new")],
            [InlineKeyboardButton(text="📊 My Active Campaigns", callback_data="promote_my_campaigns")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_to_menu")]
        ]
    )

    await callback.message.edit_text(text=intro_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "promote_new")
async def start_new_promotion(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(PromoteState.waiting_for_video_url)
    await callback.message.edit_text(
        text=t("promote_ask_url", lang),
        reply_markup=get_back_button(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(PromoteState.waiting_for_video_url)
async def process_video_url(message: Message, state: FSMContext, lang: str):
    url = message.text.strip()
    status_msg = await message.answer("⏳ Resolving video details...")

    try:
        video_info = await YouTubeService.get_video_details(url)
    except YouTubeQuotaExceededError as e:
        await status_msg.edit_text(f"⚠️ {str(e)}", reply_markup=get_back_button(lang))
        return
    except YouTubeAPIError as e:
        await status_msg.edit_text(f"❌ {str(e)}", reply_markup=get_back_button(lang))
        return

    if not video_info:
        await status_msg.edit_text(
            t("promote_invalid_url", lang),
            reply_markup=get_back_button(lang)
        )
        return

    await state.update_data(
        video_id=video_info["video_id"],
        video_title=video_info["title"],
        video_url=video_info["url"]
    )
    await state.set_state(PromoteState.waiting_for_task_type)

    prompt = (
        f"🎬 <b>Selected Video:</b> <code>{video_info['title']}</code>\n\n"
        "👉 Select the type of engagement you want to receive:"
    )

    await status_msg.edit_text(
        text=prompt,
        reply_markup=get_promote_task_types_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("promote_type:"))
async def select_task_type(callback: CallbackQuery, state: FSMContext, lang: str):
    task_type = callback.data.split(":")[1]
    data = await state.get_data()
    title = data.get("video_title", "Video")

    # Base reward and cost calculation
    reward = getattr(settings, f"TASK_{task_type}_REWARD", 20)
    fee_percent = settings.PLATFORM_FEE_PERCENT
    cost_per_action = int(reward * (1 + fee_percent / 100))

    await state.update_data(
        task_type=task_type,
        reward_per_action=reward,
        cost_per_action=cost_per_action
    )
    await state.set_state(PromoteState.waiting_for_quantity)

    prompt = t(
        "promote_ask_quantity",
        lang,
        title=title,
        task_type=task_type,
        cost=cost_per_action
    )

    await callback.message.edit_text(text=prompt, reply_markup=get_back_button(lang), parse_mode="HTML")
    await callback.answer()

@router.message(PromoteState.waiting_for_quantity)
async def process_campaign_quantity(message: Message, state: FSMContext, user, lang: str, session: AsyncSession):
    qty_text = message.text.strip()
    if not qty_text.isdigit():
        await message.answer("❌ Please enter a valid number (e.g. 10, 25, 100):")
        return

    quantity = int(qty_text)
    if quantity < 5 or quantity > 500:
        await message.answer("❌ Quantity must be between 5 and 500 actions. Please try again:")
        return

    data = await state.get_data()
    cost_per_action = data["cost_per_action"]
    total_cost = cost_per_action * quantity

    if user.coins < total_cost:
        insufficient_msg = t(
            "promote_insufficient_coins",
            lang,
            total_cost=total_cost,
            balance=user.coins
        )
        await message.answer(text=insufficient_msg, reply_markup=get_back_button(lang), parse_mode="HTML")
        await state.clear()
        return

    campaign = await create_campaign(
        session=session,
        user_id=user.id,
        video_id=data["video_id"],
        video_title=data["video_title"],
        video_url=data["video_url"],
        task_type=data["task_type"],
        reward_per_action=data["reward_per_action"],
        cost_per_action=cost_per_action,
        quantity=quantity
    )

    await state.clear()

    success_msg = t(
        "promote_success",
        lang,
        title=data["video_title"],
        task_type=data["task_type"],
        quantity=quantity,
        total_cost=total_cost
    )

    await message.answer(text=success_msg, reply_markup=get_back_button(lang), parse_mode="HTML")

@router.callback_query(F.data == "promote_my_campaigns")
async def show_user_campaigns(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    campaigns = await get_user_campaigns(session, user.id)

    if not campaigns:
        empty_text = "📭 You do not have any campaigns yet. Launch one today!"
        await callback.message.edit_text(text=empty_text, reply_markup=get_back_button(lang))
        await callback.answer()
        return

    lines = ["📊 <b>Your Promotion Campaigns:</b>\n"]
    buttons = []

    for c in campaigns[:8]:
        status_emoji = {"ACTIVE": "🟢", "PAUSED": "⏸️", "COMPLETED": "✅", "CANCELLED": "❌"}.get(c.status, "⚪")
        lines.append(
            f"{status_emoji} <b>{c.task_type}:</b> {c.video_title[:30]}...\n"
            f"   Progress: <code>{c.completed_quantity} / {c.total_quantity}</code> | Status: {c.status}"
        )
        if c.status in ("ACTIVE", "PAUSED"):
            buttons.append([
                InlineKeyboardButton(text=f"⚙️ Manage #{c.id}", callback_data=f"manage_camp:{c.id}")
            ])

    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_promote")])
    await callback.message.edit_text(
        text="\n\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("manage_camp:"))
async def manage_single_campaign(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    campaign_id = int(callback.data.split(":")[1])
    campaigns = await get_user_campaigns(session, user.id)
    target = next((c for c in campaigns if c.id == campaign_id), None)

    if not target:
        await callback.answer("Campaign not found.", show_alert=True)
        return

    pause_btn_text = "▶️ Resume Campaign" if target.status == "PAUSED" else "⏸️ Pause Campaign"
    unfulfilled = max(0, target.total_quantity - target.completed_quantity)
    refund_val = unfulfilled * target.cost_per_action

    card = (
        f"🎬 <b>Campaign #{target.id}</b>\n\n"
        f"• <b>Video:</b> {target.video_title}\n"
        f"• <b>Type:</b> {target.task_type}\n"
        f"• <b>Status:</b> {target.status}\n"
        f"• <b>Progress:</b> {target.completed_quantity} / {target.total_quantity} completed\n"
        f"• <b>Refund value if cancelled now:</b> {refund_val} coins"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=pause_btn_text, callback_data=f"camp_toggle_pause:{target.id}")],
            [InlineKeyboardButton(text="❌ Cancel & Refund Unused Coins", callback_data=f"camp_cancel:{target.id}")],
            [InlineKeyboardButton(text="⬅️ Back to Campaigns", callback_data="promote_my_campaigns")]
        ]
    )

    await callback.message.edit_text(text=card, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("camp_toggle_pause:"))
async def handle_toggle_pause(callback: CallbackQuery, user, session: AsyncSession):
    campaign_id = int(callback.data.split(":")[1])
    new_status = await toggle_campaign_pause(session, campaign_id, user.id)
    if new_status:
        await callback.answer(f"Campaign status updated to {new_status}!", show_alert=True)
        # Refresh management view
        await show_user_campaigns(callback, user, "en", session)
    else:
        await callback.answer("Unable to toggle campaign.", show_alert=True)

@router.callback_query(F.data.startswith("camp_cancel:"))
async def handle_cancel_campaign(callback: CallbackQuery, user, session: AsyncSession):
    campaign_id = int(callback.data.split(":")[1])
    refund = await cancel_campaign(session, campaign_id, user.id)
    if refund is not None:
        await callback.answer(f"✅ Campaign cancelled! {refund} unused coins refunded to your wallet.", show_alert=True)
        await show_user_campaigns(callback, user, "en", session)
    else:
        await callback.answer("Unable to cancel campaign.", show_alert=True)
