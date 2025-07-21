  
"""
Job site configuration and URL management.

This module contains configuration for different job sites
including URLs, selectors, and site-specific settings.
"""

from typing import Dict, Any
from enum import Enum


class JobSite(Enum):
    """Supported job sites enumeration."""
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    DICE = "dice"


class JobSiteConfig:
    """Job site configuration management."""
    
    # Base URLs for job sites
    SITE_URLS = {
        JobSite.LINKEDIN: {
            "base_url": "https://www.linkedin.com",
            "login_url": "https://www.linkedin.com/login",
            "jobs_search_url": "https://www.linkedin.com/jobs/search",
        },
        JobSite.INDEED: {
            "base_url": "https://www.indeed.com",
            "login_url": "https://secure.indeed.com/account/login",
            "jobs_search_url": "https://www.indeed.com/jobs",
        },
        JobSite.DICE: {
            "base_url": "https://www.dice.com",
            "login_url": "https://www.dice.com/dashboard/login",
            "jobs_search_url": "https://www.dice.com/jobs",
        },
    }
    
    # Default search parameters for each site
    DEFAULT_SEARCH_PARAMS = {
        JobSite.LINKEDIN: {
            "location": "",
            "keywords": "",
            "experience_level": "entry_level,associate,mid_senior",
            "job_type": "full_time",
            "sort_by": "date",
        },
        JobSite.INDEED: {
            "location": "",
            "keywords": "",
            "radius": "25",
            "job_type": "fulltime",
            "sort": "date",
        },
        JobSite.DICE: {
            "location": "",
            "keywords": "",
            "radius": "30",
            "employment_type": "CONTRACTS,FULLTIME",
            "sort": "date",
        },
    }
    
    @classmethod
    def get_site_config(cls, site: JobSite) -> Dict[str, Any]:
        """
        Get configuration for a specific job site.
        
        Args:
            site: JobSite enum value
            
        Returns:
            Dict containing site configuration
        """
        return {
            "urls": cls.SITE_URLS.get(site, {}),
            "search_params": cls.DEFAULT_SEARCH_PARAMS.get(site, {}),
        }
    
    @classmethod
    def get_all_sites(cls) -> list[JobSite]:
        """Get list of all supported job sites."""
        return list(JobSite)