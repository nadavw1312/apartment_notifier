# TODO: implement apartment_bl.py

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from src.services.apartment.apartment_models import Apartment
from src.services.apartment.apartment_dal import ApartmentDAL

class ApartmentBL:
    """Business Logic Layer for managing apartments"""
    
    @classmethod
    async def get_apartment(
        cls,
        db: AsyncSession,
        apartment_id: int
    ) -> Optional[Apartment]:
        """Get an apartment by ID"""
        return await ApartmentDAL.get_by_id(db, apartment_id)

    @classmethod
    async def get_all_apartments(
        cls,
        db: AsyncSession
    ) -> List[Apartment]:
        """Get all apartments"""
        return await ApartmentDAL.get_all(db)

    @classmethod
    async def create_apartment(
        cls,
        db: AsyncSession,
        user: str,
        timestamp: str,
        post_link: str,
        text: str,
        price: float,
        location: str,
        phone_numbers: list[str],
        image_urls: list[str],
        mentions: list[str],
        summary: str,
        source: str,
        group_id: str,
        is_valid: bool,
        post_id: Optional[str] = None
    ) -> Apartment:
        """Create a new apartment"""
        return await ApartmentDAL.add(
            session=db,
            user=user,
            timestamp=timestamp,
            post_link=post_link,
            text=text,
            price=price,
            location=location,
            phone_numbers=phone_numbers,
            image_urls=image_urls,
            mentions=mentions,
            summary=summary,
            source=source,
            group_id=group_id,
            is_valid=is_valid,
            post_id=post_id
        )

    @classmethod
    async def search_apartments(
        cls,
        db: AsyncSession,
        search_text: str,
        page: int = 0,
        per_page: int = 10,
        last_seen_id: Optional[int] = None,
        last_seen_score: Optional[float] = None
    ) -> tuple[List[Apartment], dict]:
        """Search apartments with pagination"""
        return await ApartmentDAL.search_paginated(
            session=db,
            search_text=search_text,
            page=page,
            per_page=per_page,
            last_seen_id=last_seen_id,
            last_seen_score=last_seen_score
        )

    @classmethod
    async def get_post_ids_by_group(
        cls,
        db: AsyncSession,
        group_id: str
    ) -> List[str]:
        """Get all post IDs for a specific group"""
        return await ApartmentDAL.get_post_ids_by_group(db, group_id)

    @classmethod
    async def get_user_apartments(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> List[Apartment]:
        """Get all apartments for a specific user"""
        return await ApartmentDAL.get_by_user(db, user_id)
