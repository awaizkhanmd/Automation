"""
Database configuration and connection settings.

This module provides database-specific configuration management
and connection string generation.
"""

from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .settings import get_settings


class DatabaseConfig:
    """Database configuration management."""
    
    def __init__(self):
        self.settings = get_settings()
        self._engine = None
        self._session_factory = None
    
    @property
    def connection_url(self) -> str:
        """Get database connection URL."""
        return self.settings.database_url_with_credentials
    
    @property
    def engine_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration."""
        return {
            "poolclass": QueuePool,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "echo": self.settings.debug_mode,
        }
    
    def create_engine(self):
        """Create SQLAlchemy engine with proper configuration."""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_url,
                **self.engine_config
            )
        return self._engine
    
    def create_session_factory(self):
        """Create SQLAlchemy session factory."""
        if self._session_factory is None:
            engine = self.create_engine()
            self._session_factory = sessionmaker(bind=engine)
        return self._session_factory
    
    @property
    def alembic_config(self) -> Dict[str, str]:
        """Get Alembic migration configuration."""
        return {
            "sqlalchemy.url": self.connection_url,
            "script_location": "database/migrations",
            "file_template": "%rev%_%slug%",
        }
