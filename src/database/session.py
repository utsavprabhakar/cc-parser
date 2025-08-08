from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Global database manager instance
_db_manager = None

def get_database_manager():
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        from src.database.database import DatabaseManager
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Usage:
        with get_db_session() as session:
            # Do database operations
            session.commit()
    """
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()

def close_database():
    """Close the global database connection"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
