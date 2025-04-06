"""Data saving utilities for Facebook scraper."""

from src.db.sql_database import SQL_DB_MANAGER
from src.services.apartment.apartment_bl import ApartmentBL


async def save_apartment_data(data, group_id):
    """
    Save apartment data to database - this is a create operation
    
    Args:
        data: Dictionary with apartment data
        group_id: ID of the Facebook group (for logging purposes)
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # SQL_DB_MANAGER.get_session_with_transaction is already decorated with 
        # @asynccontextmanager so we can use "async with" directly
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            # Perform the database write operation with transaction support
            await ApartmentBL.create_apartment(session, **data)
            print(f"💾 [{group_id}] Saved post to database: {data['post_link']}")
            # The transaction will be committed when the context exits normally
            # or rolled back if an exception occurs
            return True
    except Exception as e:
        print(f"⚠️ [{group_id}] Database error: {e}")
        return False 