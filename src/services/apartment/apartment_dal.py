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
    async def add(
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
    async def get_all(
        cls,
        session: AsyncSession
    ) -> list[Apartment]:
        """Get all apartments"""
        result = await session.execute(select(Apartment))
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        apartment_id: int
    ) -> Optional[Apartment]:
        """Get a single apartment by its ID"""
        result = await session.execute(select(Apartment).where(Apartment.id == apartment_id))
        return result.scalar_one_or_none()

    @classmethod
    async def search_paginated(
        cls,
        session: AsyncSession,
        search_text: str,
        page: int = 0,
        per_page: int = 10,
        last_seen_id: Optional[int] = None,
        last_seen_score: Optional[float] = None
    ) -> tuple[list[Apartment], dict]:
        """Search apartments with pagination"""
        # Generate embedding for the search text
        search_embedding = model.encode(search_text, output_value="sentence_embedding")
        search_embedding_list = list(search_embedding)  # Convert numpy array to list directly
        
        # Decide which pagination method to use
        if last_seen_id is not None and last_seen_score is not None:
            # Use keyset pagination (more efficient for large datasets)
            query = text("""
                WITH similarity_scores AS (
                    SELECT id, (1 - (text_embedding <=> :search_embedding)) AS score
                    FROM apartments 
                    WHERE text_embedding IS NOT NULL
                )
                SELECT a.* 
                FROM apartments a
                JOIN similarity_scores s ON a.id = s.id
                WHERE (s.score < :last_score) OR (s.score = :last_score AND a.id > :last_id)
                ORDER BY s.score DESC, a.id
                LIMIT :limit
            """)
            
            params = {
                "search_embedding": search_embedding_list,
                "last_score": last_seen_score,
                "last_id": last_seen_id,
                "limit": per_page
            }
        else:
            # Use offset pagination (simpler but less efficient for deep pages)
            query = text("""
                WITH similarity_scores AS (
                    SELECT id, (1 - (text_embedding <=> :search_embedding)) AS score
                    FROM apartments 
                    WHERE text_embedding IS NOT NULL
                )
                SELECT a.* 
                FROM apartments a
                JOIN similarity_scores s ON a.id = s.id
                ORDER BY s.score DESC, a.id
                LIMIT :limit OFFSET :offset
            """)
            
            params = {
                "search_embedding": search_embedding_list,
                "limit": per_page,
                "offset": page * per_page
            }
        
        # Execute the query
        result = await session.execute(query, params)
        
        # Convert to list of Apartment objects
        apartments = list(result.mappings())
        apartment_objects = []
        
        # Get the total count for pagination metadata
        count_query = text("""
            SELECT COUNT(*) 
            FROM apartments
            WHERE text_embedding IS NOT NULL
        """)
        count_result = await session.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Calculate pagination metadata
        has_next = (page + 1) * per_page < total_count
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        
        # Get last item details for keyset pagination
        last_id = None
        last_score = None
        
        # Process apartments and extract pagination keys
        for apt_data in apartments:
            # Create Apartment instance
            apt = Apartment(**{k: v for k, v in apt_data.items() if k in Apartment.__table__.columns.keys()})
            apartment_objects.append(apt)
            
            # Store the last item's ID for keyset pagination
            last_id = apt.id
            
            # Calculate similarity score for the last item
            if apt.text_embedding is not None and search_embedding_list is not None:
                apt_embedding = np.array(apt.text_embedding)
                search_embedding_array = np.array(search_embedding_list)
                similarity = 1 - np.linalg.norm(apt_embedding - search_embedding_array)
                last_score = float(similarity)
        
        # Prepare pagination metadata
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages,
            "has_next": has_next,
            "next_page": page + 1 if has_next else None,
            "last_seen_id": last_id,
            "last_seen_score": last_score
        }
        
        return apartment_objects, pagination

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

    @classmethod
    async def get_by_user(
        cls,
        session: AsyncSession,
        user_id: int
    ) -> list[Apartment]:
        """Get all apartments for a specific user"""
        # Get the user's email from the database
        from src.services.user.user_models import User
        user = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()
        if not user:
            return []

        # Get apartments for this user's email
        result = await session.execute(
            select(Apartment).where(Apartment.user == user.email)
        )
        return list(result.scalars().all())
