# -*- coding: utf-8 -*-
"""
Admin Keyboards for CreatorBoost Bot
Controls for stats, proof approval, settings, and broadcasts.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Returns the primary admin control center keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Platform Stats", callback_data="admin_stats"),
                InlineKeyboardButton(text="📸 Review Proofs", callback_data="admin_proofs")
            ],
            [
                InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="💰 Coin Adjuster", callback_data="admin_adjust_coins")
            ],
            [
                InlineKeyboardButton(text="🖼️ Manage Banner Ad", callback_data="admin_manage_banner"),
                InlineKeyboardButton(text="📝 Edit Sponsored Ad", callback_data="admin_manage_sponsored")
            ],
            [
                InlineKeyboardButton(text="⚙️ Task Settings", callback_data="admin_task_settings"),
                InlineKeyboardButton(text="🚫 Ban / Unban User", callback_data="admin_ban_user")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="back_to_menu")
            ]
        ]
    )

def get_proof_moderation_keyboard(execution_id: int) -> InlineKeyboardMarkup:
    """Buttons to approve or reject a user's screenshot proof."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve & Credit", callback_data=f"proof_approve:{execution_id}"),
                InlineKeyboardButton(text="❌ Reject Proof", callback_data=f"proof_reject:{execution_id}")
            ],
            [
                InlineKeyboardButton(text="⏭️ Next Pending", callback_data="admin_proofs")
            ]
        ]
    )

def get_task_settings_keyboard(
    watch_on: bool,
    like_on: bool,
    comment_on: bool,
    sub_on: bool
) -> InlineKeyboardMarkup:
    """Toggle switch keyboard for individual task types."""
    w_icon = "🟢" if watch_on else "🔴"
    l_icon = "🟢" if like_on else "🔴"
    c_icon = "🟢" if comment_on else "🔴"
    s_icon = "🟢" if sub_on else "🔴"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{w_icon} Watch Tasks", callback_data="toggle_task:WATCH")],
            [InlineKeyboardButton(text=f"{l_icon} Like Tasks", callback_data="toggle_task:LIKE")],
            [InlineKeyboardButton(text=f"{c_icon} Comment Tasks", callback_data="toggle_task:COMMENT")],
            [InlineKeyboardButton(text=f"{s_icon} Subscribe Tasks", callback_data="toggle_task:SUBSCRIBE")],
            [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_dashboard")]
        ]
    )

def get_admin_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Admin Dashboard", callback_data="admin_dashboard")]
        ]
    )
