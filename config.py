# -*- coding: utf-8 -*-
"""
CreatorBoost Bot - Central Configuration
Loads environment variables safely with strict validation and sane defaults.
"""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    # Telegram & API Credentials
    BOT_TOKEN: str = "YOUR_BOT_TOKEN_HERE"
    YOUTUBE_API_KEY: str = "YOUR_YOUTUBE_API_KEY_HERE"
    ADMIN_IDS: List[int] = [7854748403]
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'creatorboost.db'}"
    
    # Monetization & Ads
    ADSGRAM_BLOCK_ID: str = ""
    ADMIN_UPI_ID: str = "creatorboost@upi"
    
    # Platform Mechanics & Rewards
    DEFAULT_LANGUAGE: str = "en"
    WATCH_TIMER_SECONDS: int = 45
    PLATFORM_FEE_PERCENT: int = 10
    SPONSORED_MSG_INTERVAL: int = 3
    DAILY_WATCH_AD_LIMIT: int = 5
    WATCH_AD_COINS: int = 15
    DAILY_BONUS_BASE: int = 10
    REFERRAL_BONUS: int = 100
    REFERRAL_TASK_THRESHOLD: int = 3
    WELCOME_BONUS_COINS: int = 50
    
    # Default Task Rewards & Status
    TASK_WATCH_REWARD: int = 20
    TASK_LIKE_REWARD: int = 15
    TASK_COMMENT_REWARD: int = 25
    TASK_SUBSCRIBE_REWARD: int = 40
    
    TASK_WATCH_ENABLED: bool = True
    TASK_LIKE_ENABLED: bool = True
    TASK_COMMENT_ENABLED: bool = True
    TASK_SUBSCRIBE_ENABLED: bool = False  # Disabled by default per requirements
    
    # Anti-Abuse Rate Limits
    TASK_COOLDOWN_SECONDS: int = 20
    MAX_FAILS_BEFORE_FLAG: int = 5
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, int, List[int]]) -> List[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            clean = [int(i.strip()) for i in v.split(",") if i.strip().isdigit()]
            return clean or [7854748403]
        if isinstance(v, list):
            return [int(x) for x in v]
        return [7854748403]

settings = Settings()
