"""
Factory for creating job site automators.
"""

from typing import Dict, Type
from src.core.browser_manager import BrowserManager
from src.automation.base_automator import BaseAutomator
from src.automation.linkedin_automator import LinkedInAutomator
from src.automation.indeed_automator import IndeedAutomator
from src.automation.dice_automator import DiceAutomator


class JobSiteFactory:
    """Factory for creating job site automator instances."""
    
    _automators: Dict[str, Type[BaseAutomator]] = {
        "linkedin": LinkedInAutomator,
        "indeed": IndeedAutomator,
        "dice": DiceAutomator
    }
    
    @classmethod
    def create_automator(cls, site_name: str, browser_manager: BrowserManager) -> BaseAutomator:
        """Create automator for specified job site."""
        automator_class = cls._automators.get(site_name.lower())
        if not automator_class:
            raise ValueError(f"Unsupported job site: {site_name}")
        
        return automator_class(browser_manager)
    
    @classmethod
    def get_supported_sites(cls) -> list[str]:
        """Get list of supported job sites."""
        return list(cls._automators.keys())