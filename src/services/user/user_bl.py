from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user.user_dal import add_user, update_user_preferences_by_telegram_id

async def create_user(session: AsyncSession, name: str, email: str, password: str, telegram_id: str | None, phone_number: str | None, notify_telegram: bool, notify_email: bool, notify_whatsapp: bool, min_price: int | None, max_price: int | None, min_area: int | None, max_area: int | None, min_rooms: int | None, max_rooms: int | None):
    return await add_user(session, name, email, password, telegram_id, phone_number, notify_telegram, notify_email, notify_whatsapp, min_price, max_price, min_area, max_area, min_rooms, max_rooms)

async def update_user_preferences(session: AsyncSession, telegram_id: str, min_price: int | None, max_price: int | None, min_area: int | None, max_area: int | None, min_rooms: int | None, max_rooms: int | None):
    return await update_user_preferences_by_telegram_id(session, telegram_id, min_price, max_price, min_area, max_area, min_rooms, max_rooms)