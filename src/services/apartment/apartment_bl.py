# TODO: implement apartment_bl.py

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.apartment.apartment_dal import add_apartment, get_all_apartments, get_apartment_by_id
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
    is_valid: bool
):
    return await add_apartment(session, user, timestamp, post_link, text, price, location, phone_numbers, image_urls, mentions, summary, source, group_id, is_valid)

async def list_apartments(session: AsyncSession):
    return await get_all_apartments(session)

async def get_apartment(session: AsyncSession, apartment_id: int) -> Optional[Apartment]:
    """Get a single apartment by its ID"""
    return await get_apartment_by_id(session, apartment_id)
