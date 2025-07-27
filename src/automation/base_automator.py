"""
Base automator class for job site automation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from src.core.browser_manager import BrowserManager
from src.core.form_handler import FormHandler
from database.models import UserProfile, JobPosting, JobApplication, ApplicationStatus

logger = logging.getLogger(__name__)


class BaseAutomator(ABC):
    """Base class for job site automators."""
    
    def __init__(self, browser_manager: BrowserManager, site_name: str):
        self.browser = browser_manager
        self.site_name = site_name
        self.form_handler = FormHandler(browser_manager)
        self.is_logged_in = False
    
    @abstractmethod
    async def login(self, credentials: Dict[str, str]) -> bool:
        """Login to the job site."""
        pass
    
    @abstractmethod
    async def search_jobs(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for jobs based on parameters."""
        pass
    
    @abstractmethod
    async def apply_to_job(self, job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> bool:
        """Apply to a specific job."""
        pass
    
    async def get_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a job posting."""
        try:
            await self.browser.navigate_to(job_url)
            
            # Extract basic job information
            title = await self.browser.get_element_text("h1")
            company = await self.browser.get_element_text("[data-automation-id='job-detail-company']")
            location = await self.browser.get_element_text("[data-automation-id='job-detail-location']")
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "site": self.site_name
            }
        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            return None
    
    async def check_already_applied(self, job_url: str) -> bool:
        """Check if already applied to this job."""
        # Look for "Applied" indicators
        indicators = [
            "applied", "application sent", "already applied",
            "view application", "application submitted"
        ]
        
        page_text = await self.browser.execute_javascript(
            "return document.body.innerText.toLowerCase()"
        )
        
        return any(indicator in page_text for indicator in indicators)
    
    async def take_error_screenshot(self, context: str) -> str:
        """Take screenshot for error debugging."""
        return await self.browser.take_screenshot(f"{self.site_name}_error_{context}")