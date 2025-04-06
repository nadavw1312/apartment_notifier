from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.sql_database import SQL_DB_MANAGER
from src.services.user.user_api_schemas import UserCreateRequest, UserResponse


router = APIRouter()

