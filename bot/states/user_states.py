# -*- coding: utf-8 -*-
"""
Finite State Machine (FSM) States for CreatorBoost Bot
Organizes multi-step user dialogues.
"""

from aiogram.fsm.state import State, StatesGroup

class ChannelVerificationState(StatesGroup):
    waiting_for_link = State()
    waiting_for_confirmation = State()

class PromoteState(StatesGroup):
    waiting_for_video_url = State()
    waiting_for_task_type = State()
    waiting_for_quantity = State()

class TaskProofState(StatesGroup):
    waiting_for_screenshot = State()

class AdminState(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_coin_user_id = State()
    waiting_for_coin_amount = State()
    waiting_for_banner_image = State()
    waiting_for_banner_caption = State()
    waiting_for_banner_url = State()
    waiting_for_sponsored_text = State()
