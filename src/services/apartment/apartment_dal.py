from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.services.apartment.apartment_models import Apartment
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from typing import Optional
import numpy as np
# Initialize the embedding model once.
model = SentenceTransformer("all-MiniLM-L6-v2")


async def add_apartment(
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
) -> Apartment:
    # Generate embedding from the text (convert to a list of floats)
    embedding = model.encode(text, output_value="sentence_embedding").tolist()
    # Convert price to string (if needed) since the model expects TEXT
    price_str = str(price) if price is not None else None

    # Create an Apartment instance with the embedding stored in the "embedding" field.
    apartment = Apartment(
        user=user,
        timestamp=timestamp,
        post_link=post_link,
        text=text,
        text_embedding=embedding,
        price=price_str,
        location=location,
        phone_numbers=phone_numbers,
        image_urls=image_urls,
        mentions=mentions,
        summary=summary,
        source=source,
        group_id=group_id,
        is_valid=is_valid
    )
    session.add(apartment)
    await session.commit()
    await session.refresh(apartment)
    return apartment


async def get_all_apartments(session: AsyncSession) -> list[Apartment]:
    result = await session.execute(select(Apartment))
    return list(result.scalars().all())


async def get_apartment_by_id(session: AsyncSession, apartment_id: int) -> Optional[Apartment]:
    """Get a single apartment by its ID"""
    result = await session.execute(select(Apartment).where(Apartment.id == apartment_id))
    return result.scalar_one_or_none()


async def search_apartments_with_scores(
    session: AsyncSession,
    search_text: str,
    limit: int = 10
) -> list[tuple[Apartment, float]]:
    """
    Search for apartments and return with similarity scores.
    
    Args:
        session: Database session
        search_text: Text to search for
        limit: Maximum number of results to return
        
    Returns:
        List of tuples (apartment, similarity_score) sorted by similarity
    """
    # Convert search text to embedding vector
    search_embedding = model.encode(search_text, output_value="sentence_embedding").tolist()
    
    # Use pgvector's cosine similarity function
    # 1.0 means exactly similar, 0.0 means completely different

    
    # SQL query using pgvector's cosine similarity function
    query = text("""
        SELECT *, 
            (1 - (text_embedding <=> :search_embedding)) AS similarity_score
        FROM apartments
        WHERE text_embedding IS NOT NULL
        ORDER BY similarity_score DESC
        LIMIT :limit
    """)
    
    result = await session.execute(
        query,
        {"search_embedding": search_embedding, "limit": limit}
    )
    
    # Get results with similarity scores
    rows = list(result.mappings())
    
    # Extract apartments and scores
    apartments_with_scores = []
    for row in rows:
        # Create Apartment object from row data (excluding similarity_score)
        apt_data = {k: v for k, v in row.items() if k != 'similarity_score'}
        apartment = Apartment(**apt_data)
        similarity_score = row['similarity_score']
        apartments_with_scores.append((apartment, similarity_score))
    
    return apartments_with_scores


async def search_apartments_paginated(
    session: AsyncSession,
    search_text: str,
    page: int = 0,
    per_page: int = 10,
    last_seen_id: Optional[int] = None,
    last_seen_score: Optional[float] = None
) -> tuple[list[Apartment], dict]:
    """
    Search for apartments with pagination support using vector similarity.
    
    Args:
        session: Database session
        search_text: Text to search for
        page: Current page (0-indexed)
        per_page: Number of results per page
        last_seen_id: ID of the last item on the previous page (for keyset pagination)
        last_seen_score: Similarity score of the last item (for keyset pagination)
        
    Returns:
        Tuple of (list of apartments, pagination metadata)
    """
    # Convert search text to embedding vector
    search_embedding = model.encode(search_text, output_value="sentence_embedding")
    # Force conversion to numpy array and then to list
    search_embedding = np.array(search_embedding).tolist()
    
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
            "search_embedding": search_embedding,
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
            "search_embedding": search_embedding,
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
        if apt.text_embedding is not None and search_embedding is not None:
            apt_embedding = np.array(apt.text_embedding)
            search_embedding_array = np.array(search_embedding)
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
