# -*- coding: utf-8 -*-
"""
Channel Registration & Ownership Verification Handler (No OAuth)
Verifies YouTube channel ownership via unique code placed in channel About/Description.
Enforces 1 Telegram account = 1 YouTube channel rule.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import (
    get_channel_by_user_id,
    get_channel_by_youtube_id,
    create_or_update_channel,
    mark_channel_verified
)
from services.youtube import YouTubeService, YouTubeQuotaExceededError, YouTubeAPIError
from services.i18n import t
from utils.helpers import generate_verification_code, format_number
from bot.keyboards.inline import get_channel_verify_keyboard, get_back_button
from bot.states.user_states import ChannelVerificationState

router = Router(name="channel")

@router.callback_query(F.data == "menu_channel")
async def handle_my_channel(callback: CallbackQuery, state: FSMContext, user, lang: str, session: AsyncSession):
    await state.clear()
    channel = await get_channel_by_user_id(session, user.id)

    if channel and channel.is_verified:
        verified_date = channel.verified_at.strftime("%Y-%m-%d %H:%M UTC") if channel.verified_at else "Verified"
        text = t(
            "channel_info_verified",
            lang,
            title=channel.title,
            custom_url=channel.custom_url or "N/A",
            channel_id=channel.channel_id,
            subscribers=channel.subscribers,
            verified_at=verified_date
        )
        await callback.message.edit_text(text=text, reply_markup=get_back_button(lang), parse_mode="HTML")
        await callback.answer()
        return

    # If unverified or no channel linked
    prompt_text = t("channel_unverified_title", lang) + t("channel_prompt_link", lang)
    await state.set_state(ChannelVerificationState.waiting_for_link)
    await callback.message.edit_text(
        text=prompt_text,
        reply_markup=get_back_button(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ChannelVerificationState.waiting_for_link)
async def process_channel_link(message: Message, state: FSMContext, user, lang: str, session: AsyncSession):
    link_or_handle = message.text.strip()
    status_msg = await message.answer(t("channel_resolving", lang))

    try:
        channel_info = await YouTubeService.resolve_channel(link_or_handle)
    except YouTubeQuotaExceededError as e:
        await status_msg.edit_text(f"⚠️ {str(e)}", reply_markup=get_back_button(lang))
        return
    except YouTubeAPIError as e:
        await status_msg.edit_text(f"❌ {str(e)}", reply_markup=get_back_button(lang))
        return

    if not channel_info or not channel_info.get("channel_id"):
        await status_msg.edit_text(
            t("channel_not_found", lang),
            reply_markup=get_back_button(lang)
        )
        return

    yt_channel_id = channel_info["channel_id"]

    # Check 1:1 restriction: Has another user already verified or linked this channel?
    existing_owner = await get_channel_by_youtube_id(session, yt_channel_id)
    if existing_owner and existing_owner.user_id != user.id and existing_owner.is_verified:
        await status_msg.edit_text(
            t("channel_already_registered", lang),
            reply_markup=get_back_button(lang)
        )
        await state.clear()
        return

    # Generate unique ownership code e.g. CB-48291
    verification_code = generate_verification_code()

    # Save pending channel record in DB
    await create_or_update_channel(
        session=session,
        user_id=user.id,
        channel_id=yt_channel_id,
        title=channel_info["title"],
        custom_url=channel_info.get("custom_url"),
        verification_code=verification_code,
        subscribers=channel_info.get("subscribers", 0),
        video_count=channel_info.get("video_count", 0)
    )

    instructions = t(
        "channel_verify_instructions",
        lang,
        title=channel_info["title"],
        channel_id=yt_channel_id,
        subscribers=channel_info.get("subscribers", 0),
        code=verification_code
    )

    await state.set_state(ChannelVerificationState.waiting_for_confirmation)
    await status_msg.edit_text(
        text=instructions,
        reply_markup=get_channel_verify_keyboard(lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "verify_channel_code")
async def handle_verify_channel_click(callback: CallbackQuery, state: FSMContext, user, lang: str, session: AsyncSession):
    channel = await get_channel_by_user_id(session, user.id)
    if not channel:
        await callback.message.edit_text("❌ Channel registration session expired. Please start again from menu.")
        await state.clear()
        return

    await callback.answer("⏳ Checking channel description...", show_alert=False)

    try:
        is_verified = await YouTubeService.verify_channel_code(channel.channel_id, channel.verification_code)
    except YouTubeQuotaExceededError as e:
        await callback.message.answer(f"⚠️ {str(e)}")
        return
    except YouTubeAPIError as e:
        await callback.message.answer(f"❌ {str(e)}")
        return

    if is_verified:
        await mark_channel_verified(session, user.id)
        await state.clear()
        success_text = t("channel_verify_success", lang, title=channel.title)
        await callback.message.edit_text(
            text=success_text,
            reply_markup=get_back_button(lang),
            parse_mode="HTML"
        )
    else:
        fail_text = t("channel_verify_fail", lang, code=channel.verification_code)
        await callback.message.edit_text(
            text=fail_text,
            reply_markup=get_channel_verify_keyboard(lang),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "cancel_channel_reg")
async def cancel_channel_registration(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.clear()
    await callback.message.edit_text(
        text=t("action_cancelled", lang),
        reply_markup=get_back_button(lang)
    )
    await callback.answer()
