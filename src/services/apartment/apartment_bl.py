# TODO: implement apartment_bl.py

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from src.services.apartment.apartment_models import Apartment
from src.services.apartment.apartment_dal import ApartmentDAL

class ApartmentBL:
    """Business Logic Layer for managing apartments"""
    
    # Note: removed unused methods get_apartment and get_all_apartments

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
        return await ApartmentDAL.create_apartment(
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
    async def get_post_ids_by_group(
        cls,
        db: AsyncSession,
        group_id: str
    ) -> List[str]:
        """Get all post IDs for a specific group"""
        return await ApartmentDAL.get_post_ids_by_group(db, group_id)
