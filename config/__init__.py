  
"""
Configuration package for job automation system.

This package contains all configuration-related modules including
database settings, job site configurations, and application settings.

"""

from .settings import Settings, get_settings
from .database import DatabaseConfig

__all__ = ["Settings", "get_settings", "DatabaseConfig"]