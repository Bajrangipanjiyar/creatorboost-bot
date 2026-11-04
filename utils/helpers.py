# -*- coding: utf-8 -*-
"""
Helper utilities for CreatorBoost Bot
"""

import random
import string
from typing import Optional

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
