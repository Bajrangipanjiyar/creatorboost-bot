# -*- coding: utf-8 -*-
"""
Start, Language, and Main Menu Handlers
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.crud import update_user_language
from services.i18n import t
from bot.keyboards.inline import get_language_keyboard, get_main_menu_keyboard, get_back_button
from ads.manager import AdManager
from utils.helpers import safe_edit_message

router = Router(name="start")

@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext, user, lang: str, session: AsyncSession):
    await state.clear()
    is_admin = user.id in settings.ADMIN_IDS

    welcome_text = t(
        "welcome_msg",
        lang,
        name=message.from_user.first_name,
        bonus=settings.WELCOME_BONUS_COINS
    )

    # Check and prepend banner ad if configured
    banner = await AdManager.get_banner_ad(session)
    if banner and banner.get("image"):
        try:
            await message.answer_photo(
                photo=banner["image"],
                caption=banner["caption"],
                parse_mode="HTML"
            )
        except Exception:
            pass  # Fall back gracefully if image ID is invalid

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(lang, is_admin=is_admin),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery, state: FSMContext, user, lang: str):
    await state.clear()
    is_admin = user.id in settings.ADMIN_IDS
    welcome_text = t("welcome_msg", lang, name=callback.from_user.first_name, bonus=settings.WELCOME_BONUS_COINS)

    await safe_edit_message(
        message=callback.message,
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(lang, is_admin=is_admin),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "menu_language")
async def handle_language_menu(callback: CallbackQuery, lang: str):
    await safe_edit_message(
        message=callback.message,
        text=t("choose_lang", lang),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("lang_"))
async def handle_set_language(callback: CallbackQuery, user, session: AsyncSession):
    new_lang = callback.data.split("_")[1]
    await update_user_language(session, user.id, new_lang)
    is_admin = user.id in settings.ADMIN_IDS

    confirmation = t("lang_updated", new_lang)
    welcome_text = t("welcome_msg", new_lang, name=callback.from_user.first_name, bonus=settings.WELCOME_BONUS_COINS)

    await safe_edit_message(
        message=callback.message,
        text=f"{confirmation}\n\n{welcome_text}",
        reply_markup=get_main_menu_keyboard(new_lang, is_admin=is_admin),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "menu_help")
async def handle_help_menu(callback: CallbackQuery, lang: str):
    await safe_edit_message(
        message=callback.message,
        text=t("help_text", lang),
        reply_markup=get_back_button(lang),
        parse_mode="HTML"
    )
    await callback.answer()
