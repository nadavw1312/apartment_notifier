# TODO: implement apartment_bl.py

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.apartment.apartment_dal import add_apartment, get_all_apartments, get_apartment_by_id, get_post_ids_by_group
from typing import Optional, Dict, Any, List
from src.services.apartment.apartment_models import Apartment

from src.services.apartment.apartment_dal import ApartmentDAL

class ApartmentBL:
    """Business Logic Layer for managing apartments"""
    
    @classmethod
    async def get_apartment(
        cls,
        db: AsyncSession,
        apartment_id: int
    ) -> Optional[Apartment]:
        """Get an apartment by ID"""
        return await ApartmentDAL.get_by_id(db, apartment_id)

    @classmethod
    async def get_apartment_by_source_id(
        cls,
        db: AsyncSession,
        source: str,
        source_id: str
    ) -> Optional[Apartment]:
        """Get an apartment by source and source ID"""
        return await ApartmentDAL.get_by_source_id(db, source, source_id)

    @classmethod
    async def get_all_apartments(
        cls,
        db: AsyncSession
    ) -> List[Apartment]:
        """Get all apartments"""
        return await ApartmentDAL.get_all(db)

    @classmethod
    async def get_active_apartments(
        cls,
        db: AsyncSession
    ) -> List[Apartment]:
        """Get all active apartments"""
        return await ApartmentDAL.get_active(db)

    @classmethod
    async def create_apartment(
        cls,
        db: AsyncSession,
        source: str,
        source_id: str,
        title: str,
        description: Optional[str] = None,
        price: Optional[float] = None,
        location: Optional[str] = None,
        url: Optional[str] = None,
        images: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> Apartment:
        """Create a new apartment"""
        return await ApartmentDAL.add(
            db=db,
            source=source,
            source_id=source_id,
            title=title,
            description=description,
            price=price,
            location=location,
            url=url,
            images=images,
            metadata=metadata,
            is_active=is_active
        )

    @classmethod
    async def update_apartment(
        cls,
        db: AsyncSession,
        apartment_id: int,
        **kwargs
    ) -> Optional[Apartment]:
        """Update an apartment"""
        return await ApartmentDAL.update(db, apartment_id, **kwargs)

    @classmethod
    async def set_apartment_active(
        cls,
        db: AsyncSession,
        apartment_id: int,
        is_active: bool
    ) -> Optional[Apartment]:
        """Set an apartment's active status"""
        return await ApartmentDAL.update_active_status(db, apartment_id, is_active)

    @classmethod
    async def delete_apartment(
        cls,
        db: AsyncSession,
        apartment_id: int
    ) -> bool:
        """Delete an apartment"""
        return await ApartmentDAL.delete(db, apartment_id)

    @classmethod
    async def get_apartments_by_source(
        cls,
        db: AsyncSession,
        source: str
    ) -> List[Apartment]:
        """Get all apartments from a specific source"""
        return await ApartmentDAL.get_by_source(db, source)

    @classmethod
    async def get_active_apartments_by_source(
        cls,
        db: AsyncSession,
        source: str
    ) -> List[Apartment]:
        """Get all active apartments from a specific source"""
        return await ApartmentDAL.get_active_by_source(db, source)

    @classmethod
    async def get_apartments_by_metadata(
        cls,
        db: AsyncSession,
        metadata_key: str,
        metadata_value: Any
    ) -> List[Apartment]:
        """Get apartments with specific metadata"""
        return await ApartmentDAL.get_by_metadata(db, metadata_key, metadata_value)

    @classmethod
    async def get_processed_post_ids(
        cls,
        db: AsyncSession,
        source: str
    ) -> List[str]:
        """Get all processed post IDs for a source"""
        return await ApartmentDAL.get_processed_post_ids(db, source)
