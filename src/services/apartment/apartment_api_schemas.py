from pydantic import BaseModel

class ApartmentCreateRequest(BaseModel):
    user: str
    timestamp: str
    post_link: str
    text: str
    price: float
    location: str
    phone_numbers: list[str]
    image_urls: list[str]
    mentions: list[str]
    summary: str
    source: str
    group_id: str

class ApartmentResponse(BaseModel):
    id: int
    user: str
    timestamp: str
    post_link: str
    text: str
    price: float
    location: str
    phone_numbers: list[str]
    image_urls: list[str]
    mentions: list[str]
    summary: str
    source: str
    group_id: str
