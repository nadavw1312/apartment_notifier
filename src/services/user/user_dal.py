from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user.user_models import User
from sqlalchemy import select

async def add_user(
    session: AsyncSession,
    name: str,
    email: str,
    password: str,
    telegram_id: str | None = None,
    phone_number: str | None = None,
    notify_telegram: bool = False,
    notify_email: bool = False,
    notify_whatsapp: bool = False,
    min_price: int | None = None,
    max_price: int | None = None,
    min_area: int | None = None,
    max_area: int | None = None,
    min_rooms: int | None = None,
    max_rooms: int | None = None
) -> User:
    user = User(
        name=name,
        email=email,
        password=password,
        telegram_id=telegram_id,
        phone_number=phone_number,
        notify_telegram=notify_telegram,
        notify_email=notify_email,
        notify_whatsapp=notify_whatsapp,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        min_rooms=min_rooms,
        max_rooms=max_rooms
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def update_user_preferences_by_telegram_id(
    session: AsyncSession,
    telegram_id: str,
    min_price: int | None = None,
    max_price: int | None = None,
    min_area: int | None = None,
    max_area: int | None = None,
    min_rooms: int | None = None,
    max_rooms: int | None = None
) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise ValueError("User not found")
    if min_price is not None:
        user.min_price = min_price
    if max_price is not None:
        user.max_price = max_price
    if min_area is not None:
        user.min_area = min_area
    if max_area is not None:
        user.max_area = max_area
    if min_rooms is not None:
        user.min_rooms = min_rooms
    if max_rooms is not None:
        user.max_rooms = max_rooms
    await session.commit()  
    await session.refresh(user)
    return user

async def get_user_by_telegram_id(session, telegram_id):
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalars().first()