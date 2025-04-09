# messaging_features.py

import asyncio
import mimetypes
import logging
from typing import List, Optional, cast
from collections.abc import Sequence


from aiogram import Bot
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InputPollOption, 
    InputPollOptionUnion,
    FSInputFile
)

from aiogram.enums import ChatAction

logger = logging.getLogger(__name__)


class MessagingFeatures:
    @classmethod
    async def _simulate_typing(cls, bot: Bot, chat_id: int, delay: float = 0.5):
        try:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Error simulating typing: {e}")

    @classmethod
    def create_inline_buttons(cls, buttons: List[dict]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn['text'], callback_data=btn['callback_data']) for btn in buttons]
        ])

    @classmethod
    def create_reply_buttons(cls, buttons: List[str], resize_keyboard=True, one_time_keyboard=False) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn)] for btn in buttons],
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard
        )

    @classmethod
    async def send_text(cls, bot: Bot, chat_id: int, text: str, reply_markup=None, delay: float = 0.5):
        await cls._simulate_typing(bot, chat_id, delay)
        try:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Failed to send text: {e}")

    @classmethod
    async def remove_keyboard(cls, bot: Bot, chat_id: int, text: str = "Keyboard removed", delay: float = 0.5):
        await cls._simulate_typing(bot, chat_id, delay)
        try:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            logger.error(f"Failed to remove keyboard: {e}")

    @classmethod
    async def send_location(cls, bot: Bot, chat_id: int, latitude: float, longitude: float, delay: float = 0.5):
        await cls._simulate_typing(bot, chat_id, delay)
        try:
            await bot.send_location(chat_id=chat_id, latitude=latitude, longitude=longitude)
        except Exception as e:
            logger.error(f"Failed to send location: {e}")

    @classmethod
    async def send_poll(
        cls,
        bot: Bot,
        chat_id: int,
        question: str,
        options: List[str],
        is_anonymous: bool = True,
        allows_multiple_answers: bool = False,
        delay: float = 0.5
    ):
        await cls._simulate_typing(bot, chat_id, delay)
        try:
            # Create a list of poll options from a list of strings.
            poll_options = [InputPollOption(text=option) for option in options]
            # Type cast our list to satisfy the parameter type which expects
            # List[InputPollOptionUnion]. This tells the type checker that our
            # poll_options list is acceptable.
            casted_options = cast(List[InputPollOptionUnion], poll_options)
            await bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=casted_options,
                is_anonymous=is_anonymous,
                allows_multiple_answers=allows_multiple_answers
            )
        except Exception as e:
            logger.error(f"Failed to send poll: {e}")

    @classmethod
    async def send_contact(cls, bot: Bot, chat_id: int, phone_number: str, first_name: str, last_name: Optional[str] = None, delay: float = 0.5):
        await cls._simulate_typing(bot, chat_id, delay)
        try:
            await bot.send_contact(chat_id=chat_id, phone_number=phone_number, first_name=first_name, last_name=last_name)
        except Exception as e:
            logger.error(f"Failed to send contact: {e}")

    @classmethod
    async def send_venue(cls, bot: Bot, chat_id: int, latitude: float, longitude: float, title: str, address: str, delay: float = 0.5):
        await cls._simulate_typing(bot, chat_id, delay)
        try:
            await bot.send_venue(chat_id=chat_id, latitude=latitude, longitude=longitude, title=title, address=address)
        except Exception as e:
            logger.error(f"Failed to send venue: {e}")

    @classmethod
    async def send_dice(cls, bot: Bot, chat_id: int, emoji: str = "🎲", delay: float = 0.5):
        await cls._simulate_typing(bot, chat_id, delay)
        try:
            await bot.send_dice(chat_id=chat_id, emoji=emoji)
        except Exception as e:
            logger.error(f"Failed to send dice: {e}")

    @classmethod
    async def send_file(cls, bot: Bot, chat_id: int, file_path: str, caption: Optional[str] = None, delay: float = 0.5):
        await cls._simulate_typing(bot, chat_id, delay)

        mime_type, _ = mimetypes.guess_type(file_path)
        file = FSInputFile(file_path)

        try:
            if mime_type:
                if mime_type.startswith('image'):
                    await bot.send_photo(chat_id=chat_id, photo=file, caption=caption)
                elif mime_type.startswith('video'):
                    await bot.send_video(chat_id=chat_id, video=file, caption=caption)
                elif mime_type.startswith('audio'):
                    await bot.send_audio(chat_id=chat_id, audio=file, caption=caption)
                elif mime_type == 'image/gif':
                    await bot.send_animation(chat_id=chat_id, animation=file, caption=caption)
                else:
                    await bot.send_document(chat_id=chat_id, document=file, caption=caption)
            else:
                await bot.send_document(chat_id=chat_id, document=file, caption=caption)
        except Exception as e:
            logger.error(f"Failed to send file: {e}")

