# -*- coding: utf-8 -*-
"""
Coin Purchase & Payment Handler
Supports Telegram Stars (XTR) native digital payments and manual UPI deposit flows.
"""

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, PreCheckoutQuery,
    LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
)
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import add_coins
from services.i18n import t
from bot.keyboards.inline import get_coin_shop_keyboard, get_back_button
from utils.logger import logger

router = Router(name="payment")

@router.callback_query(F.data == "menu_buy_coins")
async def handle_buy_coins_menu(callback: CallbackQuery, lang: str):
    intro = t("buy_coins_intro", lang)
    await callback.message.edit_text(
        text=intro,
        reply_markup=get_coin_shop_keyboard(settings.ADMIN_UPI_ID),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_stars:"))
async def handle_create_stars_invoice(callback: CallbackQuery, lang: str):
    _, coins_str, stars_str = callback.data.split(":")
    coins = int(coins_str)
    stars = int(stars_str)

    title = f"{coins:,} CreatorBoost Coins"
    description = f"Instantly credits {coins:,} coins to promote your YouTube videos!"
    payload = f"stars_pack_{coins}_{stars}"

    # Telegram Stars uses currency 'XTR'
    prices = [LabeledPrice(label=title, amount=stars)]

    try:
        await callback.message.answer_invoice(
            title=title,
            description=description,
            payload=payload,
            currency="XTR",
            prices=prices
        )
        await callback.answer("⭐ Invoice generated!")
    except Exception as e:
        logger.error(f"Failed to generate Telegram Stars invoice: {e}")
        await callback.answer("Stars payment currently unavailable. Try UPI.", show_alert=True)

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Must answer True within 10 seconds for Telegram Stars transactions."""
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message, user, session: AsyncSession):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if payload.startswith("stars_pack_"):
        parts = payload.split("_")
        coins = int(parts[2])
        stars = int(parts[3])

        # Credit coins to user wallet
        new_balance = await add_coins(
            session=session,
            user_id=user.id,
            amount=coins,
            tx_type="STARS_PURCHASE",
            description=f"Purchased {coins:,} coins for {stars} Telegram Stars"
        )

        receipt_text = (
            f"🎉 <b>Payment Successful!</b>\n\n"
            f"• <b>Package:</b> +{coins:,} Coins\n"
            f"• <b>Paid:</b> {stars} Telegram Stars (XTR)\n"
            f"• <b>New Balance:</b> <code>{new_balance}</code> Coins\n\n"
            "Thank you for supporting CreatorBoost! You can now launch campaigns."
        )
        await message.answer(text=receipt_text, reply_markup=get_back_button("en"), parse_mode="HTML")

@router.callback_query(F.data == "buy_upi_info")
async def handle_upi_payment_instructions(callback: CallbackQuery, lang: str):
    upi_id = settings.ADMIN_UPI_ID
    info_text = (
        "💳 <b>Manual UPI Payment Deposit</b>\n\n"
        f"👉 <b>Official UPI VPA:</b> <code>{upi_id}</code> <i>(Tap to copy)</i>\n\n"
        "<b>Available UPI Coin Packs:</b>\n"
        "• ₹99  👉 1,000 Coins\n"
        "• ₹249 👉 3,000 Coins\n"
        "• ₹499 👉 7,000 Coins\n\n"
        "<b>Steps to complete purchase:</b>\n"
        "1. Pay the desired amount to the UPI ID above via GPay, PhonePe, or Paytm.\n"
        "2. Send your payment screenshot and 12-digit UTR reference number to Admin: @creatorboost_admin\n"
        "3. Your coins will be credited within 10 minutes!"
    )
    await callback.message.edit_text(text=info_text, reply_markup=get_back_button(lang), parse_mode="HTML")
    await callback.answer()
