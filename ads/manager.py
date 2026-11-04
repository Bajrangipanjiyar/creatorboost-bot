# -*- coding: utf-8 -*-
"""
Monetization & Advertising Engine
Manages sponsored broadcast snippets, banner ads, and "Watch Ad, Earn Coins" tasks.
"""

from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import get_system_setting, count_today_ad_views, log_ad_view, add_coins
from config import settings

class AdManager:
    @classmethod
    async def should_show_sponsored_msg(cls, session: AsyncSession, completed_tasks_count: int) -> bool:
        """Determines if a sponsored snippet should be appended based on task interval."""
        interval_str = await get_system_setting(session, "sponsored_msg_interval", str(settings.SPONSORED_MSG_INTERVAL))
        try:
            interval = int(interval_str)
        except ValueError:
            interval = settings.SPONSORED_MSG_INTERVAL

        if interval <= 0:
            return False
        return (completed_tasks_count > 0) and (completed_tasks_count % interval == 0)

    @classmethod
    async def get_sponsored_message(cls, session: AsyncSession) -> Optional[str]:
        """Fetches the active sponsored text message set by admin."""
        default_msg = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📢 <b>SPONSORED:</b> Grow your social presence 10x with <a href=\"https://creatorboost.com\">CreatorBoost Pro</a>! "
            "Get verified YouTube & Instagram engagement at scale."
        )
        msg = await get_system_setting(session, "sponsored_text", default_msg)
        return msg if msg.strip() else None

    @classmethod
    async def get_banner_ad(cls, session: AsyncSession) -> Optional[Dict[str, str]]:
        """
        Retrieves active banner ad info: image_file_id, caption, button_text, button_url.
        """
        banner_img = await get_system_setting(session, "banner_image_id", "")
        banner_url = await get_system_setting(session, "banner_url", "https://t.me/creatorboost")
        banner_caption = await get_system_setting(
            session,
            "banner_caption",
            "🚀 <b>Boost Your Channel Today!</b> Reach thousands of real creators instantly."
        )
        banner_btn_text = await get_system_setting(session, "banner_btn_text", "👉 Learn More")

        if not banner_img and not banner_url:
            return None

        return {
            "image": banner_img,
            "url": banner_url,
            "caption": banner_caption,
            "button_text": banner_btn_text
        }

    @classmethod
    async def check_watch_ad_eligibility(cls, session: AsyncSession, user_id: int) -> Tuple[bool, int, int]:
        """
        Checks daily watch-ad limit for user.
        Returns: (is_eligible, views_today, daily_limit)
        """
        limit_str = await get_system_setting(session, "watch_ad_daily_limit", str(settings.DAILY_WATCH_AD_LIMIT))
        try:
            limit = int(limit_str)
        except ValueError:
            limit = settings.DAILY_WATCH_AD_LIMIT

        views_today = await count_today_ad_views(session, user_id, ad_type="WATCH_AD")
        return views_today < limit, views_today, limit

    @classmethod
    async def claim_watch_ad_reward(cls, session: AsyncSession, user_id: int) -> Optional[int]:
        """Credits reward for watching an ad and records in log."""
        eligible, views, limit = await cls.check_watch_ad_eligibility(session, user_id)
        if not eligible:
            return None

        reward_str = await get_system_setting(session, "watch_ad_coins", str(settings.WATCH_AD_COINS))
        try:
            reward = int(reward_str)
        except ValueError:
            reward = settings.WATCH_AD_COINS

        await add_coins(
            session=session,
            user_id=user_id,
            amount=reward,
            tx_type="WATCH_AD_REWARD",
            description=f"Reward for watching sponsored ad ({views + 1}/{limit})"
        )
        await log_ad_view(session, user_id, ad_type="WATCH_AD", reward=reward)
        return reward
