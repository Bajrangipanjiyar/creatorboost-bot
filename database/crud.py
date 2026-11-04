# -*- coding: utf-8 -*-
"""
Database CRUD Operations for CreatorBoost Bot
Asynchronous queries using SQLAlchemy 2.0.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, update, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    User, Channel, Campaign, TaskExecution, Transaction,
    SystemSetting, AdViewLog, utc_now
)
from config import settings

# ==============================================================================
# USER OPERATIONS
# ==============================================================================

async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str] = None,
    full_name: str = "Creator",
    referrer_id: Optional[int] = None
) -> Tuple[User, bool]:
    """Retrieve an existing user or create a new user with welcome bonus."""
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Update username / full_name if changed
        if user.username != username or user.full_name != full_name:
            user.username = username
            user.full_name = full_name
            await session.commit()
        return user, False

    # Prevent self-referral
    valid_referrer_id = referrer_id if referrer_id and referrer_id != user_id else None

    # Verify referrer exists if provided
    if valid_referrer_id:
        ref_check = await session.execute(select(User.id).where(User.id == valid_referrer_id))
        if not ref_check.scalar_one_or_none():
            valid_referrer_id = None

    new_user = User(
        id=user_id,
        username=username,
        full_name=full_name,
        coins=settings.WELCOME_BONUS_COINS,
        referrer_id=valid_referrer_id
    )
    session.add(new_user)
    await session.flush()

    # Log welcome bonus transaction
    tx = Transaction(
        user_id=user_id,
        amount=settings.WELCOME_BONUS_COINS,
        balance_after=settings.WELCOME_BONUS_COINS,
        tx_type="WELCOME_BONUS",
        description="Welcome starter coins"
    )
    session.add(tx)
    await session.commit()
    await session.refresh(new_user)
    return new_user, True

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_language(session: AsyncSession, user_id: int, lang_code: str) -> None:
    stmt = update(User).where(User.id == user_id).values(language=lang_code)
    await session.execute(stmt)
    await session.commit()

async def add_coins(
    session: AsyncSession,
    user_id: int,
    amount: int,
    tx_type: str,
    description: str
) -> Optional[int]:
    """Atomically adjust user coins and record a transaction."""
    stmt = select(User).where(User.id == user_id).with_for_update()
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None

    # Check for negative balance
    new_balance = user.coins + amount
    if new_balance < 0:
        return None  # Insufficient coins

    user.coins = new_balance
    tx = Transaction(
        user_id=user_id,
        amount=amount,
        balance_after=new_balance,
        tx_type=tx_type,
        description=description
    )
    session.add(tx)
    await session.commit()
    return new_balance

async def ban_unban_user(session: AsyncSession, user_id: int, is_banned: bool) -> bool:
    stmt = update(User).where(User.id == user_id).values(is_banned=is_banned)
    res = await session.execute(stmt)
    await session.commit()
    return res.rowcount > 0

async def flag_suspicious_user(session: AsyncSession, user_id: int, is_suspicious: bool = True) -> None:
    stmt = update(User).where(User.id == user_id).values(
        is_suspicious=is_suspicious,
        warning_count=User.warning_count + 1
    )
    await session.execute(stmt)
    await session.commit()

# ==============================================================================
# CHANNEL OPERATIONS (1 USER = 1 CHANNEL)
# ==============================================================================

async def get_channel_by_user_id(session: AsyncSession, user_id: int) -> Optional[Channel]:
    stmt = select(Channel).where(Channel.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_channel_by_youtube_id(session: AsyncSession, channel_id: str) -> Optional[Channel]:
    stmt = select(Channel).where(Channel.channel_id == channel_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_or_update_channel(
    session: AsyncSession,
    user_id: int,
    channel_id: str,
    title: str,
    custom_url: Optional[str],
    verification_code: str,
    subscribers: int = 0,
    video_count: int = 0
) -> Channel:
    """Create a new channel entry or replace unverified channel for the user."""
    stmt = select(Channel).where(Channel.user_id == user_id)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.channel_id = channel_id
        existing.title = title
        existing.custom_url = custom_url
        existing.verification_code = verification_code
        existing.is_verified = False
        existing.subscribers = subscribers
        existing.video_count = video_count
        await session.commit()
        await session.refresh(existing)
        return existing

    new_channel = Channel(
        user_id=user_id,
        channel_id=channel_id,
        title=title,
        custom_url=custom_url,
        verification_code=verification_code,
        is_verified=False,
        subscribers=subscribers,
        video_count=video_count
    )
    session.add(new_channel)
    await session.commit()
    await session.refresh(new_channel)
    return new_channel

async def mark_channel_verified(session: AsyncSession, user_id: int) -> bool:
    stmt = update(Channel).where(Channel.user_id == user_id).values(
        is_verified=True,
        verified_at=utc_now()
    )
    res = await session.execute(stmt)
    await session.commit()
    return res.rowcount > 0

# ==============================================================================
# CAMPAIGN OPERATIONS
# ==============================================================================

async def create_campaign(
    session: AsyncSession,
    user_id: int,
    video_id: str,
    video_title: str,
    video_url: str,
    task_type: str,
    reward_per_action: int,
    cost_per_action: int,
    quantity: int
) -> Optional[Campaign]:
    """Deduct coins and create a video promotion campaign."""
    total_cost = cost_per_action * quantity
    balance = await add_coins(
        session=session,
        user_id=user_id,
        amount=-total_cost,
        tx_type="CAMPAIGN_CREATE",
        description=f"Created {task_type} campaign for {quantity} actions"
    )
    if balance is None:
        return None  # Insufficient coins

    campaign = Campaign(
        user_id=user_id,
        video_id=video_id,
        video_title=video_title,
        video_url=video_url,
        task_type=task_type,
        reward_per_action=reward_per_action,
        cost_per_action=cost_per_action,
        total_quantity=quantity,
        completed_quantity=0,
        status="ACTIVE"
    )
    session.add(campaign)
    await session.commit()
    await session.refresh(campaign)
    return campaign

async def get_active_campaign_for_user(
    session: AsyncSession,
    user_id: int,
    preferred_task_type: Optional[str] = None
) -> Optional[Campaign]:
    """
    Finds one active campaign that:
    1. Does not belong to the user.
    2. Has remaining unfulfilled slots (completed_quantity < total_quantity).
    3. User has NOT already started/completed.
    """
    # Subquery of campaign IDs already attempted by this user
    attempted_subq = select(TaskExecution.campaign_id).where(TaskExecution.user_id == user_id)

    query = select(Campaign).where(
        and_(
            Campaign.status == "ACTIVE",
            Campaign.user_id != user_id,
            Campaign.completed_quantity < Campaign.total_quantity,
            ~Campaign.id.in_(attempted_subq)
        )
    )

    if preferred_task_type:
        query = query.where(Campaign.task_type == preferred_task_type)

    query = query.order_by(Campaign.created_at.asc()).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none()

async def get_user_campaigns(session: AsyncSession, user_id: int) -> List[Campaign]:
    stmt = select(Campaign).where(Campaign.user_id == user_id).order_by(desc(Campaign.created_at))
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_campaign_by_id(session: AsyncSession, campaign_id: int) -> Optional[Campaign]:
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def cancel_campaign(session: AsyncSession, campaign_id: int, user_id: int) -> Optional[int]:
    """Cancels an active/paused campaign and refunds unused coins."""
    stmt = select(Campaign).where(and_(Campaign.id == campaign_id, Campaign.user_id == user_id)).with_for_update()
    result = await session.execute(stmt)
    campaign = result.scalar_one_or_none()

    if not campaign or campaign.status in ("COMPLETED", "CANCELLED"):
        return None

    unfulfilled = max(0, campaign.total_quantity - campaign.completed_quantity)
    refund_amount = unfulfilled * campaign.cost_per_action

    campaign.status = "CANCELLED"

    if refund_amount > 0:
        await add_coins(
            session=session,
            user_id=user_id,
            amount=refund_amount,
            tx_type="CAMPAIGN_REFUND",
            description=f"Refund for cancelled campaign #{campaign.id} ({unfulfilled} actions)"
        )

    await session.commit()
    return refund_amount

async def toggle_campaign_pause(session: AsyncSession, campaign_id: int, user_id: int) -> Optional[str]:
    stmt = select(Campaign).where(and_(Campaign.id == campaign_id, Campaign.user_id == user_id))
    result = await session.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign or campaign.status in ("COMPLETED", "CANCELLED"):
        return None

    new_status = "PAUSED" if campaign.status == "ACTIVE" else "ACTIVE"
    campaign.status = new_status
    await session.commit()
    return new_status

# ==============================================================================
# TASK EXECUTION OPERATIONS
# ==============================================================================

async def start_task_execution(session: AsyncSession, campaign_id: int, user_id: int) -> TaskExecution:
    stmt = select(TaskExecution).where(
        and_(TaskExecution.campaign_id == campaign_id, TaskExecution.user_id == user_id)
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    execution = TaskExecution(
        campaign_id=campaign_id,
        user_id=user_id,
        status="STARTED",
        started_at=utc_now()
    )
    session.add(execution)
    await session.commit()
    await session.refresh(execution)
    return execution

async def get_task_execution(session: AsyncSession, campaign_id: int, user_id: int) -> Optional[TaskExecution]:
    stmt = select(TaskExecution).where(
        and_(TaskExecution.campaign_id == campaign_id, TaskExecution.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_execution_by_id(session: AsyncSession, execution_id: int) -> Optional[TaskExecution]:
    stmt = select(TaskExecution).where(TaskExecution.id == execution_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def complete_task_execution(
    session: AsyncSession,
    execution_id: int,
    reward: int
) -> bool:
    """Marks task as verified, increments campaign count, and credits coins."""
    stmt = select(TaskExecution).where(TaskExecution.id == execution_id).with_for_update()
    res = await session.execute(stmt)
    execution = res.scalar_one_or_none()

    if not execution or execution.status == "VERIFIED":
        return False

    execution.status = "VERIFIED"
    execution.reward_credited = reward
    execution.completed_at = utc_now()

    # Increment campaign progress
    camp_stmt = select(Campaign).where(Campaign.id == execution.campaign_id).with_for_update()
    c_res = await session.execute(camp_stmt)
    campaign = c_res.scalar_one_or_none()

    if campaign:
        campaign.completed_quantity += 1
        if campaign.completed_quantity >= campaign.total_quantity:
            campaign.status = "COMPLETED"

    # Increment user task count
    user_stmt = select(User).where(User.id == execution.user_id).with_for_update()
    u_res = await session.execute(user_stmt)
    user = u_res.scalar_one_or_none()
    if user:
        user.completed_tasks_count += 1

    # Credit reward coins
    await add_coins(
        session=session,
        user_id=execution.user_id,
        amount=reward,
        tx_type="TASK_REWARD",
        description=f"Reward for completing {campaign.task_type if campaign else 'task'} #{execution.campaign_id}"
    )

    await session.commit()

    # Check referral criteria
    await check_and_reward_referral(session, execution.user_id)
    return True

async def submit_task_proof(session: AsyncSession, execution_id: int, photo_file_id: str) -> bool:
    stmt = update(TaskExecution).where(TaskExecution.id == execution_id).values(
        status="SUBMITTED_PROOF",
        proof_photo_file_id=photo_file_id
    )
    res = await session.execute(stmt)
    await session.commit()
    return res.rowcount > 0

async def get_pending_proofs(session: AsyncSession, limit: int = 10) -> List[TaskExecution]:
    stmt = (
        select(TaskExecution)
        .where(TaskExecution.status == "SUBMITTED_PROOF")
        .order_by(TaskExecution.started_at.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

# ==============================================================================
# REFERRAL & DAILY BONUS
# ==============================================================================

async def check_and_reward_referral(session: AsyncSession, user_id: int) -> bool:
    """
    Rewards referrer once the referred user has:
    1. Verified a channel.
    2. Completed at least settings.REFERRAL_TASK_THRESHOLD tasks.
    """
    stmt = select(User).where(User.id == user_id).with_for_update()
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.referrer_id or user.referral_reward_claimed:
        return False

    # Check channel verified
    ch_stmt = select(Channel.is_verified).where(Channel.user_id == user_id)
    ch_res = await session.execute(ch_stmt)
    is_verified = ch_res.scalar_one_or_none()

    if not is_verified:
        return False

    if user.completed_tasks_count >= settings.REFERRAL_TASK_THRESHOLD:
        user.referral_reward_claimed = True
        await add_coins(
            session=session,
            user_id=user.referrer_id,
            amount=settings.REFERRAL_BONUS,
            tx_type="REFERRAL_BONUS",
            description=f"Referral reward for verified creator @{user.username or user.id}"
        )
        await session.commit()
        return True

    return False

async def claim_daily_bonus(session: AsyncSession, user_id: int) -> Tuple[bool, int, int, str]:
    """
    Handles streak calculation and rewards:
    Returns (success, coins_awarded, streak_day, message)
    """
    stmt = select(User).where(User.id == user_id).with_for_update()
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        return False, 0, 0, "User not found"

    now = utc_now()
    if user.last_daily_bonus_at:
        delta = now - user.last_daily_bonus_at
        if delta < timedelta(hours=24):
            remaining = timedelta(hours=24) - delta
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            mins, _ = divmod(remainder, 60)
            return False, 0, user.daily_streak, f"{hours}h {mins}m"

        # If more than 48 hours, streak breaks
        if delta > timedelta(hours=48):
            user.daily_streak = 0

    # Calculate streak reward: Day 1 (10) -> Day 7 (70)
    user.daily_streak = (user.daily_streak % 7) + 1
    coins_to_award = settings.DAILY_BONUS_BASE * user.daily_streak
    user.last_daily_bonus_at = now

    await add_coins(
        session=session,
        user_id=user_id,
        amount=coins_to_award,
        tx_type="DAILY_BONUS",
        description=f"Daily bonus streak Day {user.daily_streak}"
    )
    await session.commit()
    return True, coins_to_award, user.daily_streak, "Claimed successfully"

async def get_referral_stats(session: AsyncSession, user_id: int) -> Dict[str, Any]:
    total_referred = await session.scalar(select(func.count(User.id)).where(User.referrer_id == user_id)) or 0
    
    # Qualified referrals (channel verified & tasks done)
    qualified = await session.scalar(
        select(func.count(User.id)).where(
            and_(User.referrer_id == user_id, User.referral_reward_claimed == True)
        )
    ) or 0

    total_coins_earned = qualified * settings.REFERRAL_BONUS
    return {
        "total_referred": total_referred,
        "qualified": qualified,
        "total_coins": total_coins_earned
    }

async def get_transactions(session: AsyncSession, user_id: int, limit: int = 10) -> List[Transaction]:
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.created_at))
        .limit(limit)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())

# ==============================================================================
# SYSTEM SETTINGS & ADS LOGS
# ==============================================================================

async def get_system_setting(session: AsyncSession, key: str, default: str = "") -> str:
    stmt = select(SystemSetting.value).where(SystemSetting.key == key)
    res = await session.execute(stmt)
    val = res.scalar_one_or_none()
    return val if val is not None else default

async def set_system_setting(session: AsyncSession, key: str, value: str, description: str = "") -> None:
    stmt = select(SystemSetting).where(SystemSetting.key == key)
    res = await session.execute(stmt)
    setting = res.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        session.add(SystemSetting(key=key, value=value, description=description))
    await session.commit()

async def log_ad_view(session: AsyncSession, user_id: int, ad_type: str, reward: int = 0) -> None:
    session.add(AdViewLog(user_id=user_id, ad_type=ad_type, reward_credited=reward))
    await session.commit()

async def count_today_ad_views(session: AsyncSession, user_id: int, ad_type: str) -> int:
    start_of_day = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.count(AdViewLog.id)).where(
        and_(
            AdViewLog.user_id == user_id,
            AdViewLog.ad_type == ad_type,
            AdViewLog.viewed_at >= start_of_day
        )
    )
    return await session.scalar(stmt) or 0

# ==============================================================================
# ADMIN DASHBOARD STATS
# ==============================================================================

async def get_admin_dashboard_stats(session: AsyncSession) -> Dict[str, Any]:
    total_users = await session.scalar(select(func.count(User.id))) or 0
    verified_channels = await session.scalar(select(func.count(Channel.id)).where(Channel.is_verified == True)) or 0
    active_campaigns = await session.scalar(select(func.count(Campaign.id)).where(Campaign.status == "ACTIVE")) or 0
    coins_in_circulation = await session.scalar(select(func.sum(User.coins))) or 0
    total_completed_tasks = await session.scalar(select(func.count(TaskExecution.id)).where(TaskExecution.status == "VERIFIED")) or 0
    pending_proofs = await session.scalar(select(func.count(TaskExecution.id)).where(TaskExecution.status == "SUBMITTED_PROOF")) or 0

    return {
        "total_users": total_users,
        "verified_channels": verified_channels,
        "active_campaigns": active_campaigns,
        "coins_in_circulation": coins_in_circulation,
        "total_completed_tasks": total_completed_tasks,
        "pending_proofs": pending_proofs
    }
