import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Optional
import logging

from src.models.database_models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: SQLAlchemy database URL. If None, uses SQLite in project root
        """
        if database_url is None:
            # Create SQLite database in project root
            db_path = Path(__file__).parent.parent.parent / "cc_parser.db"
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create engine
            if self.database_url.startswith('sqlite'):
                # SQLite specific configuration
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False  # Set to True for SQL debugging
                )
            else:
                self.engine = create_engine(
                    self.database_url,
                    echo=False
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info(f"Database initialized successfully: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def get_session(self):
        """Get database session"""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
    
    def reset_database(self):
        """Drop all tables and recreate them (for development/testing)"""
        if self.engine:
            Base.metadata.drop_all(bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database reset completed")
    
    def get_database_info(self):
        """Get database information"""
        if not self.engine:
            return {"status": "not_initialized"}
        
        try:
            with self.engine.connect() as conn:
                # Get table names
                tables = Base.metadata.tables.keys()
                
                # Get row counts for each table
                table_counts = {}
                for table_name in tables:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = result.scalar()
                    table_counts[table_name] = count
                
                return {
                    "status": "connected",
                    "database_url": self.database_url,
                    "tables": list(tables),
                    "table_counts": table_counts
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
