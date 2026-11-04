# -*- coding: utf-8 -*-
"""
SQLAlchemy 2.0 Async Models for CreatorBoost Bot
Structured cleanly for seamless SQLite -> PostgreSQL portability.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Integer, String, Text, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128), default="Creator")
    language: Mapped[str] = mapped_column(String(8), default="en")  # 'en' or 'hi'
    
    coins: Mapped[int] = mapped_column(Integer, default=50)  # Starts with 50 welcome coins
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_bonus_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    referral_reward_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_tasks_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    channel: Mapped[Optional["Channel"]] = relationship("Channel", back_populates="user", uselist=False)
    campaigns: Mapped[List["Campaign"]] = relationship("Campaign", back_populates="user")
    tasks: Mapped[List["TaskExecution"]] = relationship("TaskExecution", back_populates="user")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="user")

class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True, index=True)
    channel_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # YouTube UC... ID
    title: Mapped[str] = mapped_column(String(255))
    custom_url: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # @handle
    verification_code: Mapped[str] = mapped_column(String(32))  # e.g., CB-48291
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    subscribers: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="channel")

class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    video_id: Mapped[str] = mapped_column(String(32), index=True)
    video_title: Mapped[str] = mapped_column(String(255))
    video_url: Mapped[str] = mapped_column(String(255))
    
    # Task Type: 'WATCH', 'LIKE', 'COMMENT', 'SUBSCRIBE'
    task_type: Mapped[str] = mapped_column(String(16), default="WATCH")
    reward_per_action: Mapped[int] = mapped_column(Integer, default=20)
    cost_per_action: Mapped[int] = mapped_column(Integer, default=22)  # includes platform fee
    
    total_quantity: Mapped[int] = mapped_column(Integer)
    completed_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status: 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED'
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="campaigns")
    executions: Mapped[List["TaskExecution"]] = relationship("TaskExecution", back_populates="campaign")

class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    
    # Status: 'STARTED', 'VERIFIED', 'SUBMITTED_PROOF', 'REJECTED'
    status: Mapped[str] = mapped_column(String(24), default="STARTED", index=True)
    reward_credited: Mapped[int] = mapped_column(Integer, default=0)
    proof_photo_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", name="uq_campaign_user_task"),
    )

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="executions")
    user: Mapped["User"] = relationship("User", back_populates="tasks")

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)  # +credit or -debit
    balance_after: Mapped[int] = mapped_column(Integer)
    
    # Tx Types: 'WELCOME_BONUS', 'TASK_REWARD', 'CAMPAIGN_CREATE', 'CAMPAIGN_REFUND',
    #           'DAILY_BONUS', 'REFERRAL_BONUS', 'ADMIN_ADJUST', 'STARS_PURCHASE', 'WATCH_AD_REWARD'
    tx_type: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="transactions")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class AdViewLog(Base):
    __tablename__ = "ad_view_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    ad_type: Mapped[str] = mapped_column(String(32))  # 'SPONSORED_MSG', 'BANNER', 'WATCH_AD'
    reward_credited: Mapped[int] = mapped_column(Integer, default=0)
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
