# -*- coding: utf-8 -*-
"""
Earn Coins Task Flow Handler
Supports WATCH (enforced timer countdown), LIKE & COMMENT (screenshot proof),
and SUBSCRIBE (public subscription check via API).
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import (
    get_channel_by_user_id,
    get_active_campaign_for_user,
    start_task_execution,
    get_task_execution,
    get_execution_by_id,
    complete_task_execution,
    submit_task_proof,
    get_campaign_by_id
)
from services.anti_abuse import AntiAbuseService
from services.youtube import YouTubeService, YouTubeAPIError
from services.i18n import t
from ads.manager import AdManager
from bot.keyboards.inline import get_task_action_keyboard, get_back_button
from bot.states.user_states import TaskProofState

router = Router(name="earn")

@router.callback_query(F.data == "menu_earn")
@router.callback_query(F.data == "skip_task")
async def show_earn_task(callback: CallbackQuery, state: FSMContext, user, lang: str, session: AsyncSession):
    await state.clear()

    # 1. Verification Requirement Check
    channel = await get_channel_by_user_id(session, user.id)
    if not channel or not channel.is_verified:
        unverified_notice = (
            "⚠️ <b>Verification Required!</b>\n\n"
            "To maintain a high-quality community, you must verify your YouTube channel "
            "before completing tasks.\n\n"
            "👉 Please go to <b>[📺 My Channel]</b> to verify in 60 seconds."
        ) if lang == "en" else (
            "⚠️ <b>सत्यापन आवश्यक है!</b>\n\n"
            "सिक्के कमाने के लिए पहले अपना YouTube चैनल लिंक और सत्यापित करें।\n\n"
            "👉 कृपया मेनू से <b>[📺 मेरा चैनल]</b> पर जाएं।"
        )
        await callback.message.edit_text(text=unverified_notice, reply_markup=get_back_button(lang), parse_mode="HTML")
        await callback.answer()
        return

    # 2. Cooldown Rate-Limit Check
    is_allowed, remaining_cooldown = AntiAbuseService.check_task_cooldown(user.id)
    if not is_allowed:
        await callback.answer(
            t("task_cooldown_active", lang, seconds=remaining_cooldown),
            show_alert=True
        )
        return

    # 3. Fetch Active Campaign
    campaign = await get_active_campaign_for_user(session, user.id)
    if not campaign:
        await callback.message.edit_text(
            text=t("earn_no_campaigns", lang),
            reply_markup=get_back_button(lang),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # 4. Register Task Initiation
    execution = await start_task_execution(session, campaign.id, user.id)
    AntiAbuseService.record_task_start(user.id)

    # 5. Formulate Instruction Text
    if campaign.task_type == "WATCH":
        instr = t("task_instr_watch", lang, seconds=settings.WATCH_TIMER_SECONDS)
    elif campaign.task_type == "LIKE":
        instr = t("task_instr_like", lang)
    elif campaign.task_type == "COMMENT":
        instr = t("task_instr_comment", lang)
    else:
        instr = t("task_instr_sub", lang)

    card_text = t(
        "earn_campaign_card",
        lang,
        task_type=campaign.task_type,
        video_url=campaign.video_url,
        video_title=campaign.video_title,
        reward=campaign.reward_per_action,
        instruction=instr
    )

    await callback.message.edit_text(
        text=card_text,
        reply_markup=get_task_action_keyboard(
            campaign_id=campaign.id,
            video_url=campaign.video_url,
            task_type=campaign.task_type,
            lang=lang,
            timer_ready=False
        ),
        parse_mode="HTML",
        disable_web_page_preview=False
    )
    await callback.answer()

@router.callback_query(F.data.startswith("check_timer:"))
async def handle_check_timer(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    campaign_id = int(callback.data.split(":")[1])
    is_ready, remaining = AntiAbuseService.verify_watch_timer(user.id, settings.WATCH_TIMER_SECONDS)

    campaign = await get_campaign_by_id(session, campaign_id)
    if not campaign:
        await callback.answer("Campaign not found or expired.", show_alert=True)
        return

    if not is_ready:
        await callback.answer(
            f"⏳ Still watching! Please wait {remaining} more seconds.",
            show_alert=True
        )
        return

    # Timer fulfilled! Update button to Claim
    card_text = t(
        "earn_campaign_card",
        lang,
        task_type=campaign.task_type,
        video_url=campaign.video_url,
        video_title=campaign.video_title,
        reward=campaign.reward_per_action,
        instruction="✅ Timer complete! Click below to claim your coins."
    )
    await callback.message.edit_text(
        text=card_text,
        reply_markup=get_task_action_keyboard(
            campaign_id=campaign.id,
            video_url=campaign.video_url,
            task_type=campaign.task_type,
            lang=lang,
            timer_ready=True
        ),
        parse_mode="HTML"
    )
    await callback.answer("✅ Watch time verified! Claim your reward now.")

@router.callback_query(F.data.startswith("claim_watch:"))
async def handle_claim_watch(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    campaign_id = int(callback.data.split(":")[1])
    is_ready, _ = AntiAbuseService.verify_watch_timer(user.id, settings.WATCH_TIMER_SECONDS)

    if not is_ready:
        await callback.answer("⚠️ Timer verification failed. Please complete the watch time.", show_alert=True)
        return

    execution = await get_task_execution(session, campaign_id, user.id)
    if not execution or execution.status == "VERIFIED":
        await callback.answer(t("task_already_attempted", lang), show_alert=True)
        return

    campaign = await get_campaign_by_id(session, campaign_id)
    reward = campaign.reward_per_action if campaign else settings.TASK_WATCH_REWARD

    # Credit reward and log completion
    success = await complete_task_execution(session, execution.id, reward)
    AntiAbuseService.record_task_completion(user.id)

    if success:
        reward_msg = t("task_confirmed_reward", lang, reward=reward)

        # Check if sponsored ad should be presented
        if await AdManager.should_show_sponsored_msg(session, user.completed_tasks_count + 1):
            sponsored = await AdManager.get_sponsored_message(session)
            if sponsored:
                reward_msg += f"\n\n{sponsored}"

        await callback.message.edit_text(
            text=reward_msg,
            reply_markup=get_back_button(lang),
            parse_mode="HTML"
        )
        await callback.answer("🎉 Coins added to your wallet!")
    else:
        await callback.answer("Task could not be credited. Please try another.", show_alert=True)

@router.callback_query(F.data.startswith("submit_proof:"))
async def handle_submit_proof_prompt(callback: CallbackQuery, state: FSMContext, lang: str):
    campaign_id = int(callback.data.split(":")[1])
    await state.update_data(campaign_id=campaign_id)
    await state.set_state(TaskProofState.waiting_for_screenshot)

    prompt = (
        "📸 <b>Upload Proof Screenshot</b>\n\n"
        "Please take a screenshot showing your Like or Comment on the video, "
        "and send the image here as a photo."
    ) if lang == "en" else (
        "📸 <b>स्क्रीनशॉट प्रमाण भेजें</b>\n\n"
        "कृपया वीडियो लाइक या कमेंट करने का स्क्रीनशॉट लें और यहां फोटो भेजें।"
    )
    await callback.message.edit_text(text=prompt, reply_markup=get_back_button(lang), parse_mode="HTML")
    await callback.answer()

@router.message(TaskProofState.waiting_for_screenshot, F.photo)
async def process_proof_screenshot(message: Message, state: FSMContext, user, lang: str, session: AsyncSession):
    data = await state.get_data()
    campaign_id = data.get("campaign_id")
    if not campaign_id:
        await message.answer("Session expired. Please select task again from menu.")
        await state.clear()
        return

    photo_file_id = message.photo[-1].file_id
    execution = await get_task_execution(session, campaign_id, user.id)

    if not execution:
        execution = await start_task_execution(session, campaign_id, user.id)

    await submit_task_proof(session, execution.id, photo_file_id)
    AntiAbuseService.record_task_completion(user.id)
    await state.clear()

    await message.answer(
        text=t("task_proof_submitted", lang),
        reply_markup=get_back_button(lang),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("verify_sub:"))
async def handle_verify_subscription(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    campaign_id = int(callback.data.split(":")[1])
    campaign = await get_campaign_by_id(session, campaign_id)
    user_channel = await get_channel_by_user_id(session, user.id)

    if not campaign or not user_channel:
        await callback.answer("Unable to verify subscription.", show_alert=True)
        return

    # Check via YouTube API public subscriptions endpoint
    is_subscribed = await YouTubeService.verify_public_subscription(
        user_channel_id=user_channel.channel_id,
        target_channel_id=campaign.video_id  # In sub campaigns, video_id stores target channel_id
    )

    execution = await get_task_execution(session, campaign_id, user.id)
    if not execution:
        execution = await start_task_execution(session, campaign_id, user.id)

    if is_subscribed is True:
        await complete_task_execution(session, execution.id, campaign.reward_per_action)
        AntiAbuseService.record_task_completion(user.id)
        await callback.message.edit_text(
            text=t("task_confirmed_reward", lang, reward=campaign.reward_per_action),
            reply_markup=get_back_button(lang),
            parse_mode="HTML"
        )
        await callback.answer("Subscribed confirmed!")
    elif is_subscribed is False:
        await callback.answer("❌ Subscription not detected. Make sure you subscribed to the channel.", show_alert=True)
    else:
        # Private subscriptions
        notice = (
            "🔒 <b>Private Subscriptions Detected</b>\n\n"
            "Your YouTube subscription list is set to private, so the bot cannot verify automatically.\n\n"
            "👉 Either make your subscriptions public in your YouTube Settings, or submit a screenshot proof."
        )
        await callback.message.edit_text(
            text=notice,
            reply_markup=get_task_action_keyboard(
                campaign_id=campaign.id,
                video_url=campaign.video_url,
                task_type="LIKE",  # shows proof button
                lang=lang
            ),
            parse_mode="HTML"
        )
        await callback.answer()
