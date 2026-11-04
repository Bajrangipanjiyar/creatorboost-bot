# -*- coding: utf-8 -*-
"""
Wallet and Transaction History Handler
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from database.models import Campaign
from database.crud import get_transactions
from services.i18n import t
from bot.keyboards.inline import get_back_button

router = Router(name="wallet")

@router.callback_query(F.data == "menu_wallet")
async def handle_wallet(callback: CallbackQuery, user, lang: str, session: AsyncSession):
    # Count active campaigns
    camp_stmt = select(func.count(Campaign.id)).where(
        and_(Campaign.user_id == user.id, Campaign.status == "ACTIVE")
    )
    active_camps = await session.scalar(camp_stmt) or 0

    # Fetch recent transactions
    txs = await get_transactions(session, user.id, limit=6)

    tx_lines = []
    for tx in txs:
        sign = "+" if tx.amount > 0 else ""
        icon = "🟢" if tx.amount > 0 else "🔴"
        date_str = tx.created_at.strftime("%b %d, %H:%M")
        tx_lines.append(f"{icon} <b>{sign}{tx.amount} Coins</b> | {tx.description}\n   <i>{date_str}</i>")

    history_text = "\n".join(tx_lines) if tx_lines else "<i>No transactions yet.</i>"

    card_text = t(
        "wallet_card",
        lang,
        coins=user.coins,
        completed_tasks=user.completed_tasks_count,
        active_campaigns=active_camps,
        tx_history=history_text
    )

    await callback.message.edit_text(text=card_text, reply_markup=get_back_button(lang), parse_mode="HTML")
    await callback.answer()
