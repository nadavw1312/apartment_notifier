from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from src.services.user.user_models import User

class UserDAL:
    """Data Access Layer for managing users"""
    
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Optional[User]:
        """Get a user by ID"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_email(
        cls,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """Get a user by email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_telegram_id(
        cls,
        db: AsyncSession,
        telegram_id: str
    ) -> Optional[User]:
        """Get a user by Telegram ID"""
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_all(
        cls,
        db: AsyncSession
    ) -> List[User]:
        """Get all users"""
        result = await db.execute(select(User))
        return list(result.scalars().all())

    @classmethod
    async def get_active(
        cls,
        db: AsyncSession
    ) -> List[User]:
        """Get all active users"""
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())

    @classmethod
    async def add(
        cls,
        db: AsyncSession,
        email: str,
        password: str,
        name: Optional[str] = None,
        telegram_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        notify_telegram: bool = False,
        notify_email: bool = False,
        notify_whatsapp: bool = False,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_area: Optional[int] = None,
        max_area: Optional[int] = None,
        min_rooms: Optional[int] = None,
        max_rooms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """Add a new user"""
        user = User(
            email=email,
            password=password,
            name=name,
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
            max_rooms=max_rooms,
            metadata=metadata
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """Update a user"""
        user = await cls.get_by_id(db, user_id)
        
        if not user:
            return None
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def update_preferences_by_telegram_id(
        cls,
        db: AsyncSession,
        telegram_id: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_area: Optional[int] = None,
        max_area: Optional[int] = None,
        min_rooms: Optional[int] = None,
        max_rooms: Optional[int] = None
    ) -> Optional[User]:
        """Update user preferences by Telegram ID"""
        user = await cls.get_by_telegram_id(db, telegram_id)
        if not user:
            return None
            
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
            
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """Delete a user"""
        result = await db.execute(
            delete(User).where(User.id == user_id)
        )
        await db.commit()
        return result.rowcount > 0

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