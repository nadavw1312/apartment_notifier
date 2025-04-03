from pydantic import BaseModel, EmailStr

class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str | None = None
    telegram_id: str | None = None
    notify_telegram: bool = True
    notify_email: bool = True
    notify_whatsapp: bool = True
    min_price: int | None = None
    max_price: int | None = None
    min_area: int | None = None
    max_area: int | None = None
    min_rooms: int | None = None
    max_rooms: int | None = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    telegram_id: str | None
    phone_number: str | None
    notify_telegram: bool
    notify_email: bool
    notify_whatsapp: bool
    min_price: int | None
    max_price: int | None
    min_area: int | None
    max_area: int | None
    min_rooms: int | None
    max_rooms: int | None
    
    class Config:
        from_attributes = True
