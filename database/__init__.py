  
"""
Database package for job automation system.

This package contains database models, connection management,
and migration utilities.
"""

from .models import Base, UserProfile, JobApplication, JobPosting, AutomationSession, ErrorLog
from .connection import DatabaseManager, get_db_session

__all__ = [
    "Base",
    "UserProfile", 
    "JobApplication",
    "JobPosting",
    "AutomationSession",
    "ErrorLog",
    "DatabaseManager",
    "get_db_session",
]