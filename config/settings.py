"""
Application settings and configuration management.

This module handles all application settings, environment variables,
and configuration validation using Pydantic for type safety.
"""

import os
from typing import Optional
from pydantic import BaseModel, field_validator  # Updated import
from pydantic_settings import BaseSettings      # Updated import location
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Uses Pydantic BaseSettings for automatic environment variable
    loading and validation.
    """
    
    # Database Configuration
    database_url: str = "postgresql://localhost:5432/job_automation"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "job_automation"
    db_user: str = "postgres"
    db_password: str = ""
    
    # Application Configuration
    log_level: str = "INFO"
    log_file_path: str = "data/logs/automation.log"
    debug_mode: bool = False
    
    # Browser Configuration
    browser_headless: bool = False
    browser_timeout: int = 30000
    screenshot_on_error: bool = True
    
    # Automation Configuration
    max_applications_per_session: int = 50
    application_delay_min: int = 2
    application_delay_max: int = 5
    
    # AI Configuration (for future versions)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator("log_level")  # Updated decorator
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the accepted values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("log_file_path")  # Updated decorator
    @classmethod
    def create_log_directory(cls, v):
        """Ensure log directory exists."""
        log_path = Path(v)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return str(log_path)
    
    @field_validator("browser_timeout")  # Updated decorator
    @classmethod
    def validate_browser_timeout(cls, v):
        """Ensure browser timeout is reasonable."""
        if v < 5000 or v > 120000:
            raise ValueError("Browser timeout must be between 5 and 120 seconds")
        return v
    
    @field_validator("max_applications_per_session")  # Updated decorator
    @classmethod
    def validate_max_applications(cls, v):
        """Ensure reasonable application limits."""
        if v < 1 or v > 200:
            raise ValueError("Max applications per session must be between 1 and 200")
        return v
    
    @property
    def database_url_with_credentials(self) -> str:
        """Generate complete database URL with credentials."""
        if self.database_url and "://" in self.database_url:
            return self.database_url
        
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Settings: Application settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    Returns:
        Settings: Reloaded settings instance
    """
    global _settings
    _settings = Settings()
    return _settings