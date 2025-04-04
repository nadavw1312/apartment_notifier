# TODO: implement apartment_api.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.sql_database import SQL_DB_MANAGER
from src.services.apartment.apartment_api_schemas import ApartmentCreateRequest, ApartmentResponse
from src.services.apartment.apartment_bl import create_apartment, list_apartments

router = APIRouter()

@router.post("/new", response_model=ApartmentResponse)
async def add_new_apartment(
    req: ApartmentCreateRequest,
    session: AsyncSession = Depends(SQL_DB_MANAGER.get_session_with_transaction),
):
    apartment = await create_apartment(
        session,
        user=req.user,
        timestamp=req.timestamp,
        post_link=req.post_link,
        text=req.text,
        price=req.price,
        location=req.location,
        phone_numbers=req.phone_numbers,
        image_urls=req.image_urls,
        mentions=req.mentions,
        summary=req.summary,
        source=req.source,
        group_id=req.group_id,
        is_valid=req.is_valid
    )
    return ApartmentResponse.model_validate(apartment)

@router.get("/", response_model=list[ApartmentResponse])
async def get_apartments(
    session: AsyncSession = Depends(SQL_DB_MANAGER.get_session),
):
    apartments = await list_apartments(session)
    return [ApartmentResponse.model_validate(apt) for apt in apartments]
