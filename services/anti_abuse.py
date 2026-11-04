# -*- coding: utf-8 -*-
"""
Anti-Abuse & Rate-Limiting Engine
Protects platform integrity against bot automation, rapid-clicking, and duplicate exploitation.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, Optional
from cachetools import TTLCache
from config import settings
from utils.logger import logger

# In-memory caches for temporal anti-abuse tracking
# User task start timestamps: user_id -> datetime
user_task_started: Dict[int, datetime] = TTLCache(maxsize=10000, ttl=600)
# User last task completion timestamp: user_id -> datetime (enforces cooldown)
user_last_completion: Dict[int, datetime] = TTLCache(maxsize=10000, ttl=300)
# Suspicious fast attempts counter: user_id -> count
user_early_click_attempts: Dict[int, int] = TTLCache(maxsize=5000, ttl=3600)

class AntiAbuseService:
    @classmethod
    def record_task_start(cls, user_id: int) -> None:
        """Records the exact UTC second when a user started a task."""
        user_task_started[user_id] = datetime.now(timezone.utc)

    @classmethod
    def check_task_cooldown(cls, user_id: int) -> Tuple[bool, int]:
        """
        Ensures a mandatory cooldown between completing one task and starting another.
        Returns: (is_allowed, remaining_seconds)
        """
        if user_id in user_last_completion:
            elapsed = (datetime.now(timezone.utc) - user_last_completion[user_id]).total_seconds()
            required = settings.TASK_COOLDOWN_SECONDS
            if elapsed < required:
                return False, int(required - elapsed)
        return True, 0

    @classmethod
    def verify_watch_timer(cls, user_id: int, required_seconds: int) -> Tuple[bool, int]:
        """
        Verifies that at least `required_seconds` have legitimately passed
        since the user clicked 'Start Watching'.
        """
        start_time = user_task_started.get(user_id)
        if not start_time:
            # Task start was never registered or expired
            return False, required_seconds

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        if elapsed < required_seconds:
            # User clicked too early - increment suspicious counter
            attempts = user_early_click_attempts.get(user_id, 0) + 1
            user_early_click_attempts[user_id] = attempts
            logger.warning(f"User {user_id} attempted early verification ({int(elapsed)}s < {required_seconds}s). Early count: {attempts}")
            return False, int(required_seconds - elapsed)

        return True, 0

    @classmethod
    def record_task_completion(cls, user_id: int) -> None:
        """Records completion time and resets start timer."""
        user_last_completion[user_id] = datetime.now(timezone.utc)
        user_task_started.pop(user_id, None)

    @classmethod
    def is_flagged_for_review(cls, user_id: int) -> bool:
        """Checks if user has made excessive early click violations."""
        return user_early_click_attempts.get(user_id, 0) >= settings.MAX_FAILS_BEFORE_FLAG
