from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.sql_database import SQL_DB_MANAGER
from src.services.user.user_api_schemas import UserCreateRequest, UserResponse
from src.services.user.user_bl import create_user

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def register_user(
    req: UserCreateRequest,
    session: AsyncSession = Depends(SQL_DB_MANAGER.get_session_with_transaction),
):
    user = await create_user(
        session,
        name=req.name,
        email=req.email,
        password=req.password,
        telegram_id=req.telegram_id,
        phone_number=req.phone_number,
        notify_telegram=req.notify_telegram,
        notify_email=req.notify_email,
        notify_whatsapp=req.notify_whatsapp,
        min_price=req.min_price,
        max_price=req.max_price,
        min_area=req.min_area,
        max_area=req.max_area,
        min_rooms=req.min_rooms,
        max_rooms=req.max_rooms
    )
    return UserResponse.model_validate(user)
