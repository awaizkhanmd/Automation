"""
Utility helper functions for job automation system.

This module contains common utility functions used across
the automation system for data processing, file handling,
and other general operations.
"""

import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and periods
    sanitized = sanitized.strip('. ')
    
    # Truncate if too long
    if len(sanitized) > max_length:
        # Keep file extension if present
        path = Path(sanitized)
        if path.suffix:
            max_stem_length = max_length - len(path.suffix)
            sanitized = str(path.stem[:max_stem_length]) + path.suffix
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized


def generate_hash(data: Union[str, Dict[str, Any]], algorithm: str = 'md5') -> str:
    """
    Generate hash for data (useful for detecting duplicates).
    
    Args:
        data: Data to hash (string or dict)
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hex hash string
    """
    if isinstance(data, dict):
        # Sort keys for consistent hashing
        data_str = json.dumps(data, sort_keys=True)
    else:
        data_str = str(data)
    
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data_str.encode('utf-8'))
    return hash_obj.hexdigest()


def extract_job_id_from_url(url: str, site: str) -> Optional[str]:
    """
    Extract job ID from job posting URL.
    
    Args:
        url: Job posting URL
        site: Job site name (linkedin, indeed, dice)
        
    Returns:
        Extracted job ID or None
    """
    try:
        parsed_url = urlparse(url)
        
        if site.lower() == 'linkedin':
            # LinkedIn job URLs: /jobs/view/12345678
            match = re.search(r'/jobs/view/(\d+)', parsed_url.path)
            return match.group(1) if match else None
            
        elif site.lower() == 'indeed':
            # Indeed job URLs: ?jk=abc123def456
            query_params = parse_qs(parsed_url.query)
            jk_values = query_params.get('jk', [])
            return jk_values[0] if jk_values else None
            
        elif site.lower() == 'dice':
            # Dice job URLs: /job/detail/abc-123-def-456
            match = re.search(r'/job/detail/([^/?]+)', parsed_url.path)
            return match.group(1) if match else None
            
    except Exception as e:
        logger.warning(f"Failed to extract job ID from URL {url}: {e}")
    
    return None


def normalize_job_title(title: str) -> str:
    """
    Normalize job title for comparison and matching.
    
    Args:
        title: Original job title
        
    Returns:
        Normalized job title
    """
    if not title:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = title.lower().strip()
    
    # Remove common prefixes/suffixes that don't affect the core role
    patterns_to_remove = [
        r'\b(senior|sr\.?|junior|jr\.?|lead|principal|staff)\b',
        r'\b(entry.?level|mid.?level|experienced?)\b',
        r'\b(full.?time|part.?time|contract|temporary|temp)\b',
        r'\b(remote|on.?site|hybrid)\b',
        r'\([^)]*\)',  # Remove content in parentheses
    ]
    
    for pattern in patterns_to_remove:
        normalized = re.sub(pattern, ' ', normalized, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def calculate_application_similarity(app1: Dict[str, Any], app2: Dict[str, Any]) -> float:
    """
    Calculate similarity between two job applications to detect duplicates.
    
    Args:
        app1: First application data
        app2: Second application data
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    similarity_score = 0.0
    total_weight = 0.0
    
    # Compare company names (high weight)
    if 'company_name' in app1 and 'company_name' in app2:
        company_similarity = 1.0 if app1['company_name'].lower() == app2['company_name'].lower() else 0.0
        similarity_score += company_similarity * 0.4
        total_weight += 0.4
    
    # Compare job titles (medium weight)
    if 'title' in app1 and 'title' in app2:
        title1 = normalize_job_title(app1['title'])
        title2 = normalize_job_title(app2['title'])
        title_similarity = 1.0 if title1 == title2 else 0.0
        similarity_score += title_similarity * 0.3
        total_weight += 0.3
    
    # Compare locations (low weight)
    if 'location' in app1 and 'location' in app2:
        location_similarity = 1.0 if app1['location'].lower() == app2['location'].lower() else 0.0
        similarity_score += location_similarity * 0.2
        total_weight += 0.2
    
    # Compare URLs (high weight if available)
    if 'job_url' in app1 and 'job_url' in app2:
        url_similarity = 1.0 if app1['job_url'] == app2['job_url'] else 0.0
        similarity_score += url_similarity * 0.1
        total_weight += 0.1
    
    return similarity_score / total_weight if total_weight > 0 else 0.0


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"


def parse_salary_range(salary_text: str) -> Dict[str, Optional[int]]:
    """
    Parse salary range text to extract min and max values.
    
    Args:
        salary_text: Salary range text (e.g., "$80,000 - $120,000")
        
    Returns:
        Dict with 'min' and 'max' salary values
    """
    result = {'min': None, 'max': None}
    
    if not salary_text:
        return result
    
    # Remove common text and normalize
    normalized = re.sub(r'[^\d\-\$k,.]', ' ', salary_text.lower())
    
    # Find salary numbers
    salary_pattern = r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)[k]?'
    matches = re.findall(salary_pattern, normalized)
    
    if matches:
        salaries = []
        for match in matches:
            # Remove commas and convert to int
            salary = int(match.replace(',', ''))
            
            # Handle 'k' suffix (thousands)
            if 'k' in normalized:
                salary *= 1000
            
            salaries.append(salary)
        
        if len(salaries) >= 2:
            result['min'] = min(salaries)
            result['max'] = max(salaries)
        elif len(salaries) == 1:
            result['min'] = result['max'] = salaries[0]
    
    return result


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def safe_dict_get(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value using dot notation.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated key path (e.g., 'user.profile.name')
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    try:
        keys = key_path.split('.')
        value = data
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        
    Returns:
        Function result
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        raise last_exception
    
    return wrapper


def get_timestamp_string(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    Get current timestamp as formatted string.
    
    Args:
        format_str: Datetime format string
        
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_str)


def load_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Safely load JSON file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file cannot be loaded
        
    Returns:
        Loaded JSON data or default value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load JSON file {file_path}: {e}")
        return default


def save_json_file(data: Any, file_path: Union[str, Path], indent: int = 2) -> bool:
    """
    Safely save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
        indent: JSON indentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path_obj = Path(file_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path_obj, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False