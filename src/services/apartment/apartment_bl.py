# TODO: implement apartment_bl.py

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.apartment.apartment_dal import add_apartment, get_all_apartments

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
    group_id: str   
):
    return await add_apartment(session, user, timestamp, post_link, text, price, location, phone_numbers, image_urls, mentions, summary, source, group_id)

async def list_apartments(session: AsyncSession):
    return await get_all_apartments(session)
