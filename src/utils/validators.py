  
"""
Data validation utilities for job automation system.

This module provides validation functions for user input,
configuration data, and system parameters.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ProfileValidator:
    """Validator for user profile data."""
    
    @staticmethod
    def validate_profile_data(profile_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate complete user profile data.
        
        Args:
            profile_data: Profile data dictionary
            
        Returns:
            Dict of validation errors by field
        """
        errors = {}
        
        # Required fields
        required_fields = ['profile_name', 'first_name', 'last_name', 'email']
        for field in required_fields:
            if not profile_data.get(field):
                errors.setdefault(field, []).append(f"{field} is required")
        
        # Validate specific fields
        if profile_data.get('email'):
            email_errors = ProfileValidator.validate_email(profile_data['email'])
            if email_errors:
                errors['email'] = email_errors
        
        if profile_data.get('phone'):
            phone_errors = ProfileValidator.validate_phone(profile_data['phone'])
            if phone_errors:
                errors['phone'] = phone_errors
        
        if profile_data.get('experience_years'):
            exp_errors = ProfileValidator.validate_experience_years(profile_data['experience_years'])
            if exp_errors:
                errors['experience_years'] = exp_errors
        
        if profile_data.get('salary_min') and profile_data.get('salary_max'):
            salary_errors = ProfileValidator.validate_salary_range(
                profile_data['salary_min'], profile_data['salary_max']
            )
            if salary_errors:
                errors['salary'] = salary_errors
        
        return errors
    
    @staticmethod
    def validate_email(email: str) -> List[str]:
        """Validate email address."""
        errors = []
        
        if not email:
            errors.append("Email is required")
            return errors
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")
        
        if len(email) > 255:
            errors.append("Email address is too long (max 255 characters)")
        
        return errors
    
    @staticmethod
    def validate_phone(phone: str) -> List[str]:
        """Validate phone number."""
        errors = []
        
        if not phone:
            return errors  # Phone is optional
        
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[^\d]', '', phone)
        
        if len(cleaned_phone) < 10:
            errors.append("Phone number must have at least 10 digits")
        elif len(cleaned_phone) > 15:
            errors.append("Phone number is too long (max 15 digits)")
        
        return errors
    
    @staticmethod
    def validate_experience_years(years: Union[int, str]) -> List[str]:
        """Validate years of experience."""
        errors = []
        
        try:
            years_int = int(years)
            if years_int < 0:
                errors.append("Experience years cannot be negative")
            elif years_int > 50:
                errors.append("Experience years seems unrealistic (max 50)")
        except (ValueError, TypeError):
            errors.append("Experience years must be a valid number")
        
        return errors
    
    @staticmethod
    def validate_salary_range(min_salary: Union[int, str], max_salary: Union[int, str]) -> List[str]:
        """Validate salary range."""
        errors = []
        
        try:
            min_sal = int(min_salary)
            max_sal = int(max_salary)
            
            if min_sal < 0 or max_sal < 0:
                errors.append("Salary values cannot be negative")
            elif min_sal > max_sal:
                errors.append("Minimum salary cannot be greater than maximum salary")
            elif min_sal > 1000000 or max_sal > 1000000:
                errors.append("Salary values seem unrealistic (max $1,000,000)")
            
        except (ValueError, TypeError):
            errors.append("Salary values must be valid numbers")
        
        return errors


class JobPostingValidator:
    """Validator for job posting data."""
    
    @staticmethod
    def validate_job_posting(job_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate job posting data.
        
        Args:
            job_data: Job posting data dictionary
            
        Returns:
            Dict of validation errors by field
        """
        errors = {}
        
        # Required fields
        required_fields = ['title', 'company_name', 'job_url', 'job_site']
        for field in required_fields:
            if not job_data.get(field):
                errors.setdefault(field, []).append(f"{field} is required")
        
        # Validate URL
        if job_data.get('job_url'):
            url_errors = JobPostingValidator.validate_url(job_data['job_url'])
            if url_errors:
                errors['job_url'] = url_errors
        
        # Validate job site
        if job_data.get('job_site'):
            site_errors = JobPostingValidator.validate_job_site(job_data['job_site'])
            if site_errors:
                errors['job_site'] = site_errors
        
        return errors
    
    @staticmethod
    def validate_url(url: str) -> List[str]:
        """Validate URL format."""
        errors = []
        
        if not url:
            errors.append("URL is required")
            return errors
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                errors.append("Invalid URL format")
        except Exception:
            errors.append("Invalid URL format")
        
        return errors
    
    @staticmethod
    def validate_job_site(site: str) -> List[str]:
        """Validate job site name."""
        errors = []
        
        valid_sites = ['linkedin', 'indeed', 'dice']
        if site.lower() not in valid_sites:
            errors.append(f"Job site must be one of: {', '.join(valid_sites)}")
        
        return errors


class ConfigurationValidator:
    """Validator for system configuration."""
    
    @staticmethod
    def validate_automation_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate automation configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dict of validation errors by field
        """
        errors = {}
        
        # Validate browser timeout
        if 'browser_timeout' in config:
            timeout_errors = ConfigurationValidator.validate_timeout(config['browser_timeout'])
            if timeout_errors:
                errors['browser_timeout'] = timeout_errors
        
        # Validate application limits
        if 'max_applications_per_session' in config:
            limit_errors = ConfigurationValidator.validate_application_limit(
                config['max_applications_per_session']
            )
            if limit_errors:
                errors['max_applications_per_session'] = limit_errors
        
        # Validate delay settings
        if 'application_delay_min' in config and 'application_delay_max' in config:
            delay_errors = ConfigurationValidator.validate_delay_range(
                config['application_delay_min'], config['application_delay_max']
            )
            if delay_errors:
                errors['application_delay'] = delay_errors
        
        return errors
    
    @staticmethod
    def validate_timeout(timeout: Union[int, str]) -> List[str]:
        """Validate timeout value."""
        errors = []
        
        try:
            timeout_int = int(timeout)
            if timeout_int < 5000:
                errors.append("Timeout must be at least 5 seconds (5000ms)")
            elif timeout_int > 300000:
                errors.append("Timeout cannot exceed 5 minutes (300000ms)")
        except (ValueError, TypeError):
            errors.append("Timeout must be a valid number")
        
        return errors
    
    @staticmethod
    def validate_application_limit(limit: Union[int, str]) -> List[str]:
        """Validate application limit."""
        errors = []
        
        try:
            limit_int = int(limit)
            if limit_int < 1:
                errors.append("Application limit must be at least 1")
            elif limit_int > 200:
                errors.append("Application limit cannot exceed 200 per session")
        except (ValueError, TypeError):
            errors.append("Application limit must be a valid number")
        
        return errors
    
    @staticmethod
    def validate_delay_range(min_delay: Union[int, str], max_delay: Union[int, str]) -> List[str]:
        """Validate delay range."""
        errors = []
        
        try:
            min_del = int(min_delay)
            max_del = int(max_delay)
            
            if min_del < 1 or max_del < 1:
                errors.append("Delay values must be at least 1 second")
            elif min_del > max_del:
                errors.append("Minimum delay cannot be greater than maximum delay")
            elif max_del > 60:
                errors.append("Maximum delay cannot exceed 60 seconds")
            
        except (ValueError, TypeError):
            errors.append("Delay values must be valid numbers")
        
        return errors


def validate_json_structure(data: Any, required_keys: List[str]) -> List[str]:
    """
    Validate JSON data structure.
    
    Args:
        data: JSON data to validate
        required_keys: List of required keys
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a JSON object")
        return errors
    
    for key in required_keys:
        if key not in data:
            errors.append(f"Required key '{key}' is missing")
    
    return errors


def sanitize_input(input_str: str, max_length: int = 255, allow_html: bool = False) -> str:
    """
    Sanitize user input string.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return str(input_str)[:max_length]
    
    # Remove or escape HTML if not allowed
    if not allow_html:
        input_str = re.sub(r'<[^>]+>', '', input_str)
    
    # Remove null bytes and control characters
    input_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
    
    # Truncate to max length
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    return input_str.strip()


def is_valid_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Validate date range.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid date range
    """
    if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
        return False
    
    return start_date <= end_date


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> List[str]:
    """
    Validate file path and extension.
    
    Args:
        file_path: File path to validate
        allowed_extensions: List of allowed file extensions
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if not file_path:
        errors.append("File path is required")
        return errors
    
    # Check for path traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        errors.append("Invalid file path (potential security risk)")
    
    # Check file extension if specified
    if allowed_extensions:
        file_ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
        if file_ext not in [ext.lower().lstrip('.') for ext in allowed_extensions]:
            errors.append(f"File extension must be one of: {', '.join(allowed_extensions)}")
    
    return errors