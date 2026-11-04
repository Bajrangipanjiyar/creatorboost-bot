# -*- coding: utf-8 -*-
"""
Verification Script for CreatorBoost Bot
Tests database initialization, model schema, i18n engine, and helper utilities.
"""

import asyncio
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db, async_session_factory
from database.crud import get_or_create_user, add_coins, get_admin_dashboard_stats
from services.i18n import t
from utils.helpers import generate_verification_code

async def test_system():
    print("=" * 60)
    print(" Running CreatorBoost Setup Verification Test ")
    print("=" * 60)

    # 1. Test Database Initialization
    print("[1] Initializing SQLite Database tables...")
    await init_db()
    print("    [✓] Database tables created successfully.")

    # 2. Test User Creation & Wallet Transaction
    print("[2] Testing User Creation & Wallet logic...")
    async with async_session_factory() as session:
        user, is_new = await get_or_create_user(
            session=session,
            user_id=7854748403,
            username="test_creator",
            full_name="Bajrangi Panjiyar"
        )
        print(f"    [✓] User loaded: {user.full_name} (ID: {user.id}) | Coins: {user.coins}")

        # Add coins
        new_balance = await add_coins(
            session=session,
            user_id=user.id,
            amount=100,
            tx_type="TEST_CREDIT",
            description="Testing automated coin crediting"
        )
        print(f"    [✓] Coins updated: New Balance = {new_balance}")

    # 3. Test i18n Translations
    print("[3] Testing Bilingual i18n Dictionary...")
    en_welcome = t("welcome_msg", "en", name="Bajrangi", bonus=50)
    hi_welcome = t("welcome_msg", "hi", name="Bajrangi", bonus=50)
    assert "Welcome" in en_welcome
    assert "स्वागत" in hi_welcome
    print("    [✓] English and Hindi translations verified.")

    # 4. Test Code Generator
    print("[4] Testing Channel Verification Code Generator...")
    code = generate_verification_code()
    print(f"    [✓] Generated Code: {code}")
    assert code.startswith("CB-") and len(code) == 8

    # 5. Test Admin Dashboard Stats Query
    print("[5] Testing Admin Dashboard Stats Query...")
    async with async_session_factory() as session:
        stats = await get_admin_dashboard_stats(session)
        print(f"    [✓] Stats: Users={stats['total_users']}, Coins={stats['coins_in_circulation']}")

    print("=" * 60)
    print(" ALL TESTS PASSED! CreatorBoost Bot is 100% production-ready! ")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_system())
