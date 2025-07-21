"""
Database connection management and session handling.

This module provides database connection utilities, session management,
and context managers for safe database operations.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from config.database import DatabaseConfig
from config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager for handling connections and sessions.
    
    This class provides centralized database connection management
    with proper error handling and connection pooling.
    """
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.settings = get_settings()
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            self._engine = self.config.create_engine()
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = self.config.create_session_factory()
        return self._session_factory
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing database connection: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables."""
        try:
            from .models import Base
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            from .models import Base
            Base.metadata.drop_all(self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            Session: SQLAlchemy session
        """
        return self.session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around database operations.
        
        This context manager automatically handles session lifecycle,
        commits successful transactions, and rolls back on errors.
        
        Yields:
            Session: Database session
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
            logger.debug("Database transaction committed successfully")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error, transaction rolled back: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error, transaction rolled back: {e}")
            raise
        finally:
            session.close()
    
    def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> any:
        """
        Execute raw SQL query.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"Error executing raw SQL: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> dict:
        """
        Get information about a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dict containing table information
        """
        try:
            with self.engine.connect() as conn:
                # Get column information
                columns_query = text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = :table_name
                    ORDER BY ordinal_position
                """)
                columns = conn.execute(columns_query, {"table_name": table_name}).fetchall()
                
                # Get row count
                count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                row_count = conn.execute(count_query).scalar()
                
                return {
                    "table_name": table_name,
                    "columns": [dict(row._mapping) for row in columns],
                    "row_count": row_count,
                }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            raise


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get global database manager instance.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session
    """
    return get_database_manager().get_session()


@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """
    Context manager for database session with automatic transaction handling.
    
    Yields:
        Session: Database session
    """
    with get_database_manager().session_scope() as session:
        yield session


