# TODO: implement apartment_api.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.sql_database import SQL_DB_MANAGER
from src.services.apartment.apartment_api_schemas import ApartmentCreateRequest, ApartmentResponse
from src.services.apartment.apartment_bl import ApartmentBL

router = APIRouter()

