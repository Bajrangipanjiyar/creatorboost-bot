# -*- coding: utf-8 -*-
"""
Admin Command Center & Moderation Handler
Accessible exclusively to authorized ADMIN_IDS.
Provides real-time analytics, proof moderation, broadcasts, coin adjustments, and settings.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database.models import User, Campaign
from database.crud import (
    get_admin_dashboard_stats,
    get_pending_proofs,
    get_execution_by_id,
    get_campaign_by_id,
    complete_task_execution,
    add_coins,
    ban_unban_user,
    set_system_setting,
    get_system_setting
)
from bot.keyboards.admin import (
    get_admin_main_keyboard,
    get_proof_moderation_keyboard,
    get_task_settings_keyboard,
    get_admin_back_button
)
from bot.states.user_states import AdminState
from utils.logger import logger

router = Router(name="admin")

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

@router.message(Command("admin"))
@router.callback_query(F.data == "admin_dashboard")
async def handle_admin_panel(event: Message | CallbackQuery, state: FSMContext, user):
    if not is_admin(user.id):
        if isinstance(event, CallbackQuery):
            await event.answer("⛔ Access denied.", show_alert=True)
        return

    await state.clear()
    panel_text = (
        "👑 <b>CreatorBoost Admin Command Center</b>\n\n"
        "Manage platform economy, verify task proofs, broadcast announcements, "
        "and toggle system configurations below:"
    )

    if isinstance(event, Message):
        await event.answer(panel_text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")
    else:
        await event.message.edit_text(panel_text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")
        await event.answer()

@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery, user, session: AsyncSession):
    if not is_admin(user.id):
        return

    stats = await get_admin_dashboard_stats(session)
    # Estimate ad revenue based on impressions (e.g. $1.50 CPM estimate)
    est_ad_rev = (stats["total_completed_tasks"] * 0.002)

    stats_msg = (
        "📊 <b>Platform Analytics & Economy Overview</b>\n\n"
        f"• 👥 <b>Total Registered Users:</b> {stats['total_users']:,}\n"
        f"• 📺 <b>Verified YouTube Channels:</b> {stats['verified_channels']:,}\n"
        f"• 🚀 <b>Active Campaigns Running:</b> {stats['active_campaigns']:,}\n"
        f"• 💰 <b>Total Coins in Circulation:</b> {stats['coins_in_circulation']:,} Coins\n"
        f"• ✅ <b>Total Tasks Completed:</b> {stats['total_completed_tasks']:,}\n"
        f"• 📸 <b>Pending Proofs Awaiting Review:</b> {stats['pending_proofs']}\n"
        f"• 💵 <b>Estimated Ad Monetization:</b> ~${est_ad_rev:.2f}"
    )

    await callback.message.edit_text(stats_msg, reply_markup=get_admin_back_button(), parse_mode="HTML")
    await callback.answer()

# ==============================================================================
# PROOF REVIEW QUEUE
# ==============================================================================

@router.callback_query(F.data == "admin_proofs")
async def handle_admin_proofs(callback: CallbackQuery, user, session: AsyncSession):
    if not is_admin(user.id):
        return

    pending = await get_pending_proofs(session, limit=1)
    if not pending:
        await callback.message.edit_text(
            text="✅ <b>All Caught Up!</b>\n\nThere are no pending task proofs to review right now.",
            reply_markup=get_admin_back_button(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    item = pending[0]
    campaign = await get_campaign_by_id(session, item.campaign_id)

    caption = (
        f"📸 <b>Pending Proof Review (#{item.id})</b>\n\n"
        f"• <b>Earner User ID:</b> <code>{item.user_id}</code>\n"
        f"• <b>Task Type:</b> {campaign.task_type if campaign else 'N/A'}\n"
        f"• <b>Reward:</b> {campaign.reward_per_action if campaign else 0} coins\n"
        f"• <b>Video:</b> <a href=\"{campaign.video_url if campaign else '#'}\">{campaign.video_title if campaign else 'Video'}</a>\n"
        f"• <b>Submitted At:</b> {item.started_at.strftime('%Y-%m-%d %H:%M UTC')}"
    )

    if item.proof_photo_file_id:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=item.proof_photo_file_id,
            caption=caption,
            reply_markup=get_proof_moderation_keyboard(item.id),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(caption, reply_markup=get_proof_moderation_keyboard(item.id), parse_mode="HTML")

    await callback.answer()

@router.callback_query(F.data.startswith("proof_approve:"))
async def approve_proof(callback: CallbackQuery, user, session: AsyncSession):
    if not is_admin(user.id):
        return

    execution_id = int(callback.data.split(":")[1])
    execution = await get_execution_by_id(session, execution_id)
    if not execution or execution.status == "VERIFIED":
        await callback.answer("Proof already processed.", show_alert=True)
        return

    campaign = await get_campaign_by_id(session, execution.campaign_id)
    reward = campaign.reward_per_action if campaign else settings.TASK_LIKE_REWARD

    await complete_task_execution(session, execution.id, reward)

    # Notify earner
    try:
        await callback.bot.send_message(
            chat_id=execution.user_id,
            text=f"🎉 <b>Proof Approved!</b> Your screenshot proof for task #{execution.campaign_id} was approved. +{reward} coins credited!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer("✅ Proof approved & coins credited!", show_alert=True)
    await handle_admin_proofs(callback, user, session)

@router.callback_query(F.data.startswith("proof_reject:"))
async def reject_proof(callback: CallbackQuery, user, session: AsyncSession):
    if not is_admin(user.id):
        return

    execution_id = int(callback.data.split(":")[1])
    execution = await get_execution_by_id(session, execution_id)
    if execution:
        execution.status = "REJECTED"
        await session.commit()

        try:
            await callback.bot.send_message(
                chat_id=execution.user_id,
                text=f"❌ <b>Proof Rejected:</b> Your screenshot for task #{execution.campaign_id} was rejected by moderation as invalid or incomplete.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await callback.answer("Proof rejected.", show_alert=True)
    await handle_admin_proofs(callback, user, session)

# ==============================================================================
# BROADCAST ANNOUNCEMENTS
# ==============================================================================

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext, user):
    if not is_admin(user.id):
        return

    await state.set_state(AdminState.waiting_for_broadcast_text)
    prompt = (
        "📢 <b>Broadcast Announcement</b>\n\n"
        "Please type or paste the message you want to broadcast to ALL registered users.\n"
        "HTML tags (<b>, <i>, <a>, <code>) are supported."
    )
    await callback.message.edit_text(prompt, reply_markup=get_admin_back_button(), parse_mode="HTML")
    await callback.answer()

@router.message(AdminState.waiting_for_broadcast_text)
async def execute_broadcast(message: Message, state: FSMContext, user, session: AsyncSession):
    if not is_admin(user.id):
        return

    text = message.text or message.caption or ""
    status_msg = await message.answer("⏳ Dispatching broadcast to all creators...")

    stmt = select(User.id).where(User.is_banned == False)
    res = await session.execute(stmt)
    user_ids = list(res.scalars().all())

    delivered = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            delivered += 1
        except Exception:
            failed += 1

    await state.clear()
    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n\n"
        f"• ✅ Delivered: <b>{delivered}</b>\n"
        f"• ❌ Failed/Blocked: <b>{failed}</b>",
        reply_markup=get_admin_back_button(),
        parse_mode="HTML"
    )

# ==============================================================================
# COIN ADJUSTMENT & BAN/UNBAN
# ==============================================================================

@router.callback_query(F.data == "admin_adjust_coins")
async def prompt_coin_adjust(callback: CallbackQuery, state: FSMContext, user):
    if not is_admin(user.id):
        return

    await state.set_state(AdminState.waiting_for_coin_user_id)
    await callback.message.edit_text(
        "💰 <b>Coin Adjuster</b>\n\nPlease send the Telegram User ID of the creator:",
        reply_markup=get_admin_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminState.waiting_for_coin_user_id)
async def process_coin_target_user(message: Message, state: FSMContext):
    uid_text = message.text.strip()
    if not uid_text.isdigit():
        await message.answer("❌ Invalid User ID. Please send numeric Telegram ID:")
        return

    await state.update_data(target_user_id=int(uid_text))
    await state.set_state(AdminState.waiting_for_coin_amount)
    await message.answer("👉 Enter amount to adjust (+500 to add, -500 to deduct):")

@router.message(AdminState.waiting_for_coin_amount)
async def process_coin_amount(message: Message, state: FSMContext, session: AsyncSession):
    amt_text = message.text.strip()
    try:
        amount = int(amt_text)
    except ValueError:
        await message.answer("❌ Please enter a valid integer amount:")
        return

    data = await state.get_data()
    target_id = data["target_user_id"]

    new_bal = await add_coins(
        session=session,
        user_id=target_id,
        amount=amount,
        tx_type="ADMIN_ADJUST",
        description=f"Admin manual adjustment by {message.from_user.id}"
    )

    await state.clear()
    if new_bal is not None:
        await message.answer(
            f"✅ <b>Coins Updated!</b> User <code>{target_id}</code> balance is now: <code>{new_bal}</code> coins.",
            reply_markup=get_admin_back_button(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ User not found or insufficient balance.", reply_markup=get_admin_back_button())

@router.callback_query(F.data == "admin_ban_user")
async def prompt_ban_user(callback: CallbackQuery, session: AsyncSession, user):
    if not is_admin(user.id):
        return
    await callback.message.edit_text(
        "🚫 <b>Ban/Unban Control</b>\n\nUse command: <code>/ban &lt;user_id&gt;</code> or <code>/unban &lt;user_id&gt;</code>",
        reply_markup=get_admin_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("ban"))
async def handle_ban_command(message: Message, user, session: AsyncSession):
    if not is_admin(user.id):
        return
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        target_id = int(parts[1])
        await ban_unban_user(session, target_id, is_banned=True)
        await message.answer(f"🚫 User <code>{target_id}</code> has been banned.")
    else:
        await message.answer("Usage: <code>/ban &lt;user_id&gt;</code>")

@router.message(Command("unban"))
async def handle_unban_command(message: Message, user, session: AsyncSession):
    if not is_admin(user.id):
        return
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        target_id = int(parts[1])
        await ban_unban_user(session, target_id, is_banned=False)
        await message.answer(f"✅ User <code>{target_id}</code> has been unbanned.")
    else:
        await message.answer("Usage: <code>/unban &lt;user_id&gt;</code>")

# ==============================================================================
# TASK & AD CONFIGURATIONS
# ==============================================================================

@router.callback_query(F.data == "admin_task_settings")
async def show_task_settings(callback: CallbackQuery, user, session: AsyncSession):
    if not is_admin(user.id):
        return

    w = (await get_system_setting(session, "task_watch_enabled", "true")).lower() == "true"
    l = (await get_system_setting(session, "task_like_enabled", "true")).lower() == "true"
    c = (await get_system_setting(session, "task_comment_enabled", "true")).lower() == "true"
    s = (await get_system_setting(session, "task_sub_enabled", "false")).lower() == "true"

    await callback.message.edit_text(
        "⚙️ <b>Task Type Toggles</b>\n\nTap to enable or disable specific task categories:",
        reply_markup=get_task_settings_keyboard(w, l, c, s),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_task:"))
async def toggle_task_setting(callback: CallbackQuery, user, session: AsyncSession):
    if not is_admin(user.id):
        return

    task = callback.data.split(":")[1]
    key = f"task_{task.lower()}_enabled"
    current = (await get_system_setting(session, key, "true")).lower() == "true"
    new_val = "false" if current else "true"
    await set_system_setting(session, key, new_val)

    await show_task_settings(callback, user, session)

@router.callback_query(F.data == "admin_manage_banner")
async def manage_banner_prompt(callback: CallbackQuery, state: FSMContext, user):
    if not is_admin(user.id):
        return

    await state.set_state(AdminState.waiting_for_banner_image)
    await callback.message.edit_text(
        "🖼️ <b>Set Banner Ad</b>\n\nPlease send the photo you want to use as the banner:",
        reply_markup=get_admin_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminState.waiting_for_banner_image, F.photo)
async def process_banner_photo(message: Message, state: FSMContext, session: AsyncSession):
    file_id = message.photo[-1].file_id
    await set_system_setting(session, "banner_image_id", file_id)
    await state.set_state(AdminState.waiting_for_banner_caption)
    await message.answer("📝 Send the caption text for the banner:")

@router.message(AdminState.waiting_for_banner_caption)
async def process_banner_caption(message: Message, state: FSMContext, session: AsyncSession):
    await set_system_setting(session, "banner_caption", message.text or "")
    await state.set_state(AdminState.waiting_for_banner_url)
    await message.answer("🔗 Send the destination URL for the banner button:")

@router.message(AdminState.waiting_for_banner_url)
async def process_banner_url(message: Message, state: FSMContext, session: AsyncSession):
    await set_system_setting(session, "banner_url", message.text.strip())
    await state.clear()
    await message.answer("✅ <b>Banner Ad Updated!</b>", reply_markup=get_admin_back_button(), parse_mode="HTML")

@router.callback_query(F.data == "admin_manage_sponsored")
async def manage_sponsored_prompt(callback: CallbackQuery, state: FSMContext, user):
    if not is_admin(user.id):
        return
    await state.set_state(AdminState.waiting_for_sponsored_text)
    await callback.message.edit_text(
        "📝 <b>Edit Sponsored Text Snippet</b>\n\nSend the text to display after every N tasks (HTML allowed):",
        reply_markup=get_admin_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminState.waiting_for_sponsored_text)
async def process_sponsored_text(message: Message, state: FSMContext, session: AsyncSession):
    await set_system_setting(session, "sponsored_text", message.text.strip())
    await state.clear()
    await message.answer("✅ <b>Sponsored Text Snippet Saved!</b>", reply_markup=get_admin_back_button(), parse_mode="HTML")
