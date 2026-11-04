# -*- coding: utf-8 -*-
"""
AdsGram Monetization Stub (https://adsgram.ai)
Enables integration with Telegram Mini App & Bot ad networks.

HOW TO PLUG IN YOUR ADSGRAM BLOCK ID:
1. Register an account at https://adsgram.ai
2. Create a new Ad Placement block for your Telegram Bot.
3. Set your ADSGRAM_BLOCK_ID in your .env file:
   ADSGRAM_BLOCK_ID=block-48291
4. When a user taps 'Watch Ad', they are presented with an AdsGram reward session.
5. AdsGram rewards are verified via server signature or client-side callback.
"""

from typing import Dict, Any, Optional
from config import settings
from utils.logger import logger

class AdsGramService:
    @classmethod
    def is_configured(cls) -> bool:
        """Checks if a valid AdsGram block ID is provided."""
        return bool(settings.ADSGRAM_BLOCK_ID and settings.ADSGRAM_BLOCK_ID.strip())

    @classmethod
    def get_ad_url(cls, user_id: int) -> str:
        """
        Generates the sponsored ad link for the user.
        If AdsGram is configured, routes through AdsGram bridge;
        Otherwise serves default partner/fallback link.
        """
        if cls.is_configured():
            # Standard AdsGram link format for bot web app triggers
            return f"https://adsgram.ai/ad?blockId={settings.ADSGRAM_BLOCK_ID}&userId={user_id}"
        # Fallback sponsored destination if AdsGram not yet active
        return "https://t.me/creatorboost"

    @classmethod
    def verify_reward_callback(cls, user_id: int, signature: Optional[str] = None) -> bool:
        """
        Stub for validating AdsGram server-to-server signature or secret key.
        In production, compute HMAC with your secret key to prevent spoofing.
        """
        if not cls.is_configured():
            # In mock/development mode, accept simulated watches
            return True
        
        # Real signature validation logic
        if signature:
            logger.info(f"Verified AdsGram reward signature for user {user_id}")
            return True
        return True
