# -*- coding: utf-8 -*-
"""
Inline Keyboards for CreatorBoost Bot
Dynamic keyboard builders for user navigation and task actions.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.i18n import t

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Returns bilingual language switcher."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton(text="🇮🇳 हिन्दी (Hindi)", callback_data="lang_hi")
            ]
        ]
    )

def get_main_menu_keyboard(lang: str = "en", is_admin: bool = False) -> InlineKeyboardMarkup:
    """Returns full main dashboard inline keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text=t("menu_channel", lang), callback_data="menu_channel"),
            InlineKeyboardButton(text=t("menu_earn", lang), callback_data="menu_earn")
        ],
        [
            InlineKeyboardButton(text=t("menu_promote", lang), callback_data="menu_promote"),
            InlineKeyboardButton(text=t("menu_wallet", lang), callback_data="menu_wallet")
        ],
        [
            InlineKeyboardButton(text=t("menu_referral", lang), callback_data="menu_referral"),
            InlineKeyboardButton(text=t("menu_daily", lang), callback_data="menu_daily")
        ],
        [
            InlineKeyboardButton(text=t("menu_buy_coins", lang), callback_data="menu_buy_coins"),
            InlineKeyboardButton(text=t("menu_watch_ad", lang, coins=15), callback_data="menu_watch_ad")
        ],
        [
            InlineKeyboardButton(text=t("menu_help", lang), callback_data="menu_help"),
            InlineKeyboardButton(text="🌐 Language", callback_data="menu_language")
        ]
    ]

    if is_admin:
        buttons.append([InlineKeyboardButton(text="👑 Admin Dashboard", callback_data="admin_dashboard")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_channel_verify_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard prompting user to verify ownership code in description."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_verify", lang), callback_data="verify_channel_code")],
            [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="cancel_channel_reg")]
        ]
    )

def get_task_action_keyboard(
    campaign_id: int,
    video_url: str,
    task_type: str,
    lang: str = "en",
    timer_ready: bool = False
) -> InlineKeyboardMarkup:
    """
    Renders task action keyboard.
    If task is WATCH, shows Open Video + Confirm Button (which unlocks after timer).
    """
    buttons = [
        [InlineKeyboardButton(text="▶️ Open YouTube Video", url=video_url)]
    ]

    if task_type == "WATCH":
        if timer_ready:
            buttons.append([
                InlineKeyboardButton(
                    text="✅ Confirm & Claim Coins",
                    callback_data=f"claim_watch:{campaign_id}"
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text="⏳ Watching... Click to Check Timer",
                    callback_data=f"check_timer:{campaign_id}"
                )
            ])
    elif task_type in ("LIKE", "COMMENT"):
        buttons.append([
            InlineKeyboardButton(
                text=t("btn_proof", lang),
                callback_data=f"submit_proof:{campaign_id}"
            )
        ])
    elif task_type == "SUBSCRIBE":
        buttons.append([
            InlineKeyboardButton(
                text="🔔 Verify Subscription",
                callback_data=f"verify_sub:{campaign_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text=t("btn_skip", lang), callback_data="skip_task"),
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_promote_task_types_keyboard(
    watch_enabled: bool = True,
    like_enabled: bool = True,
    comment_enabled: bool = True,
    sub_enabled: bool = False
) -> InlineKeyboardMarkup:
    """Keyboard for selecting engagement type for campaign creation."""
    buttons = []
    row1 = []
    if watch_enabled:
        row1.append(InlineKeyboardButton(text="👀 Watch Views", callback_data="promote_type:WATCH"))
    if like_enabled:
        row1.append(InlineKeyboardButton(text="👍 Video Likes", callback_data="promote_type:LIKE"))
    if row1:
        buttons.append(row1)

    row2 = []
    if comment_enabled:
        row2.append(InlineKeyboardButton(text="💬 Comments", callback_data="promote_type:COMMENT"))
    if sub_enabled:
        row2.append(InlineKeyboardButton(text="🔔 Subscribers", callback_data="promote_type:SUBSCRIBE"))
    if row2:
        buttons.append(row2)

    buttons.append([InlineKeyboardButton(text="❌ Cancel", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_coin_shop_keyboard(upi_id: str) -> InlineKeyboardMarkup:
    """Keyboard for purchasing coin packs via Telegram Stars or UPI."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 500 Coins (50 Stars)", callback_data="buy_stars:500:50"),
                InlineKeyboardButton(text="⭐ 1,200 Coins (100 Stars)", callback_data="buy_stars:1200:100")
            ],
            [
                InlineKeyboardButton(text="⭐ 3,000 Coins (250 Stars)", callback_data="buy_stars:3000:250"),
                InlineKeyboardButton(text="⭐ 7,000 Coins (500 Stars)", callback_data="buy_stars:7000:500")
            ],
            [
                InlineKeyboardButton(text=f"💳 Pay with UPI ({upi_id})", callback_data="buy_upi_info")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
    )

def get_back_button(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_to_menu")]
        ]
    )
