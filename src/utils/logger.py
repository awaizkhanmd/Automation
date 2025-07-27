"""
Logging configuration and utilities for job automation system.

This module provides centralized logging configuration with proper
formatting, file rotation, and different log levels for development
and production environments.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from config.settings import get_settings


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


class AutomationLogger:
    """
    Centralized logger for the automation system.
    
    Provides console and file logging with appropriate formatting
    and log rotation for production use.
    """
    
    def __init__(self, name: str = "job_automation"):
        self.settings = get_settings()
        self.logger = logging.getLogger(name)
        self._configured = False
    
    def configure(self, log_level: Optional[str] = None) -> logging.Logger:
        """
        Configure logging with console and file handlers.
        
        Args:
            log_level: Override default log level
            
        Returns:
            Configured logger instance
        """
        if self._configured:
            return self.logger
        
        # Set log level
        level = log_level or self.settings.log_level
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file_path = Path(self.settings.log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        
        # Error handler (separate file for errors)
        error_log_path = log_file_path.parent / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(file_formatter)
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
        
        self._configured = True
        self.logger.info(f"Logging configured - Level: {level}, File: {log_file_path}")
        
        return self.logger
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance with optional custom name.
        
        Args:
            name: Custom logger name
            
        Returns:
            Logger instance
        """
        if not self._configured:
            self.configure()
        
        if name:
            return logging.getLogger(f"job_automation.{name}")
        return self.logger


# Global logger instance
_automation_logger: Optional[AutomationLogger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get configured logger instance.
    
    Args:
        name: Optional logger name suffix
        
    Returns:
        Configured logger
    """
    global _automation_logger
    if _automation_logger is None:
        _automation_logger = AutomationLogger()
    return _automation_logger.get_logger(name)


def configure_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        log_level: Log level override
        
    Returns:
        Configured logger
    """
    global _automation_logger
    if _automation_logger is None:
        _automation_logger = AutomationLogger()
    return _automation_logger.configure(log_level) 
