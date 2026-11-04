# -*- coding: utf-8 -*-
"""
Helper utilities for CreatorBoost Bot
"""

import random
import string
from typing import Optional

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

def generate_verification_code() -> str:
    """Generates a clean 5-digit verification code like CB-48291."""
    digits = "".join(random.choices(string.digits, k=5))
    return f"CB-{digits}"

def format_number(val: int) -> str:
    """Formats integers with thousands comma separation."""
    return f"{val:,}"

def clean_html(text: str) -> str:
    """Escapes raw text for Telegram HTML parse mode."""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def safe_edit_message(message: Message, text: str, reply_markup=None, parse_mode: str = "HTML") -> None:
    """Edits a Telegram message, gracefully ignoring 'message is not modified' duplicate click errors."""
    try:
        await message.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
