from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_
from src.services.apartment.apartment_models import Apartment
from sentence_transformers import SentenceTransformer
from typing import Optional, List, Dict, Any
import numpy as np
import json

# Initialize the embedding model once.
model = SentenceTransformer("all-MiniLM-L6-v2")

class ApartmentDAL:
    """Data Access Layer for managing apartments"""
    
    @classmethod
    async def create_apartment(
        cls,
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
    ) -> Apartment:
        """Add a new apartment"""
        # Generate embedding from the text (convert to a list of floats)
        embedding = model.encode(text, output_value="sentence_embedding")
        embedding_list = list(embedding)  # Convert numpy array to list directly
        # Convert price to string (if needed) since the model expects TEXT
        price_str = str(price) if price is not None else None

        # Create an Apartment instance with the embedding stored in the "embedding" field.
        apartment = Apartment(
            user=user,
            timestamp=timestamp,
            post_link=post_link,
            text=text,
            text_embedding=embedding_list,
            price=price_str,
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
        session.add(apartment)
        await session.commit()
        await session.refresh(apartment)
        return apartment

    @classmethod
    async def get_post_ids_by_group(
        cls,
        session: AsyncSession,
        group_id: str
    ) -> list:
        """Get all post IDs for a specific group"""
        try:
            result = await session.execute(
                select(Apartment.post_id).where(
                    and_(
                        Apartment.group_id == group_id,
                        Apartment.post_id != None
                    )
                )
            )
            post_ids = [row[0] for row in result.all()]
            return post_ids
        except Exception as e:
            print(f"Error getting post IDs: {e}")
            return []
