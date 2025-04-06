from typing import Optional, List
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from src.services.telegram.telegram_bl import TelegramBL
from src.services.user.user_bl import UserBL
from src.db.sql_database import SQL_DB_MANAGER

class TelegramMessaging:
    """Handles sending messages to Telegram users"""

    def __init__(self, bot: Bot):
        self._bot = bot

    async def send_message(
        self,
        telegram_id: int,
        message: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Send a message to a Telegram user"""
        try:
            await self._bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramAPIError as e:
            print(f"Error sending message to {telegram_id}: {e}")
            return False

    async def send_apartment_notification(
        self,
        telegram_id: int,
        title: str,
        description: str,
        price: Optional[int] = None,
        area: Optional[int] = None,
        rooms: Optional[int] = None,
        location: Optional[str] = None,
        url: Optional[str] = None,
        images: Optional[List[str]] = None
    ) -> bool:
        """Send an apartment notification to a Telegram user"""
        # Format message
        message_parts = [f"🏠 *{title}*\n"]

        if price is not None:
            message_parts.append(f"💰 Price: {price:,} ILS")
        if area is not None:
            message_parts.append(f"📏 Area: {area} m²")
        if rooms is not None:
            message_parts.append(f"🚪 Rooms: {rooms}")
        if location:
            message_parts.append(f"📍 Location: {location}")
        if description:
            message_parts.append(f"\n📝 {description}")
        if url:
            message_parts.append(f"\n🔗 [View listing]({url})")

        message = "\n".join(message_parts)

        # Send message
        success = await self.send_message(
            telegram_id=telegram_id,
            message=message,
            parse_mode="Markdown"
        )

        # Send images if available
        if success and images:
            for image_url in images[:5]:  # Limit to 5 images
                try:
                    await self._bot.send_photo(
                        chat_id=telegram_id,
                        photo=image_url
                    )
                except TelegramAPIError as e:
                    print(f"Error sending image to {telegram_id}: {e}")

        return success

    async def notify_users(
        self,
        title: str,
        description: str,
        price: Optional[int] = None,
        area: Optional[int] = None,
        rooms: Optional[int] = None,
        location: Optional[str] = None,
        url: Optional[str] = None,
        images: Optional[List[str]] = None
    ) -> int:
        """
        Send apartment notification to all active users who have Telegram notifications enabled
        and whose preferences match the apartment.
        
        Returns the number of users notified.
        """
        notified_count = 0

        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            # Get all active Telegram users
            telegram_users = await TelegramBL.get_active_telegram_users(session)
            
            for telegram_user in telegram_users:
                # Get user preferences
                user = await UserBL.get_user(session, telegram_user.user_id)
                if not user:
                    continue

                # Check if user wants Telegram notifications
                if not user.notify_telegram:
                    continue

                # Check if apartment matches user preferences
                if price is not None:
                    if user.min_price is not None and price < user.min_price:
                        continue
                    if user.max_price is not None and price > user.max_price:
                        continue

                if area is not None:
                    if user.min_area is not None and area < user.min_area:
                        continue
                    if user.max_area is not None and area > user.max_area:
                        continue

                if rooms is not None:
                    if user.min_rooms is not None and rooms < user.min_rooms:
                        continue
                    if user.max_rooms is not None and rooms > user.max_rooms:
                        continue

                # Send notification
                success = await self.send_apartment_notification(
                    telegram_id=telegram_user.telegram_id,
                    title=title,
                    description=description,
                    price=price,
                    area=area,
                    rooms=rooms,
                    location=location,
                    url=url,
                    images=images
                )

                if success:
                    notified_count += 1

        return notified_count 