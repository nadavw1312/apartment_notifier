# TODO: implement apartment_bl.py

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.apartment.apartment_dal import add_apartment, get_all_apartments, get_apartment_by_id, get_post_ids_by_group
from typing import Optional
from src.services.apartment.apartment_models import Apartment

async def create_apartment(
    session: AsyncSession,
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
):
    return await add_apartment(session, user, timestamp, post_link, text, price, location, phone_numbers, image_urls, mentions, summary, source, group_id, is_valid, post_id)

async def list_apartments(session: AsyncSession):
    return await get_all_apartments(session)

async def get_apartment(session: AsyncSession, apartment_id: int) -> Optional[Apartment]:
    """Get a single apartment by its ID"""
    return await get_apartment_by_id(session, apartment_id)

async def get_processed_post_ids(session, group_id: str) -> list:
    """
    Get a list of post IDs that have already been processed for a specific group
    
    Args:
        session: Database session
        group_id: Facebook group ID
        
    Returns:
        List of post IDs that have already been processed
    """
    try:
        # Get post IDs from database
        post_ids = await get_post_ids_by_group(session, group_id)
        return post_ids
    except Exception as e:
        print(f"Error getting processed post IDs: {e}")
        return []
