"""
Dice job application automator.
"""

import logging
from typing import Dict, List, Optional, Any
from src.automation.base_automator import BaseAutomator

logger = logging.getLogger(__name__)


class DiceAutomator(BaseAutomator):
    """Dice job application automation."""
    
    def __init__(self, browser_manager):
        super().__init__(browser_manager, "dice")
        
        self.selectors = {
            "login_email": "#email",
            "login_password": "#password",
            "login_button": "button[type='submit']",
            "job_search": "#typeaheadInput",
            "location_search": "input[data-cy='location-typeahead-input']",
            "search_button": "#submitSearch-button",
            "job_cards": "[data-cy='search-result-card']",
            "apply_button": "[data-cy='apply-button-link']"
        }
    
    async def login(self, credentials: Dict[str, str]) -> bool:
        """Login to Dice."""
        try:
            logger.info("Logging into Dice...")
            
            await self.browser.navigate_to("https://www.dice.com/dashboard/login")
            
            await self.browser.fill_input(self.selectors["login_email"], credentials["email"])
            await self.browser.fill_input(self.selectors["login_password"], credentials["password"])
            await self.browser.click_element(self.selectors["login_button"])
            
            await self.browser.wait_for_navigation()
            
            if "dashboard" in self.browser.page.url:
                self.is_logged_in = True
                logger.info("Dice login successful")
                return True
            else:
                logger.error("Dice login failed")
                return False
                
        except Exception as e:
            logger.error(f"Dice login error: {e}")
            await self.take_error_screenshot("login")
            return False
    
    async def search_jobs(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for jobs on Dice."""
        try:
            await self.browser.navigate_to("https://www.dice.com/jobs")
            
            keywords = search_params.get("keywords", "")
            location = search_params.get("location", "")
            
            if keywords:
                await self.browser.fill_input(self.selectors["job_search"], keywords)
            
            if location:
                await self.browser.fill_input(self.selectors["location_search"], location)
            
            await self.browser.click_element(self.selectors["search_button"])
            await self.browser.wait_for_navigation()
            
            jobs = await self.browser.execute_javascript("""
                return Array.from(document.querySelectorAll('[data-cy="search-result-card"]')).map(card => {
                    const titleEl = card.querySelector('h5 a');
                    const companyEl = card.querySelector('[data-cy="search-result-company-name"]');
                    const locationEl = card.querySelector('[data-cy="job-location"]');
                    
                    return {
                        title: titleEl ? titleEl.innerText.trim() : '',
                        company: companyEl ? companyEl.innerText.trim() : '',
                        location: locationEl ? locationEl.innerText.trim() : '',
                        url: titleEl ? titleEl.href : ''
                    };
                }).filter(job => job.url);
            """)
            
            logger.info(f"Found {len(jobs)} job listings on Dice")
            return jobs[:20]
            
        except Exception as e:
            logger.error(f"Dice job search error: {e}")
            await self.take_error_screenshot("search")
            return []
    
    async def apply_to_job(self, job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> bool:
        """Apply to job on Dice."""
        try:
            await self.browser.navigate_to(job_data["url"])
            
            if await self.check_already_applied(job_data["url"]):
                return False
            
            apply_button = await self.browser.is_element_present(self.selectors["apply_button"])
            
            if apply_button:
                await self.browser.click_element(self.selectors["apply_button"])
                await self.browser.human_delay(2, 4)
                
                await self.form_handler.fill_form_intelligently(profile_data)
                
                submit_button = await self.browser.is_element_present("button[type='submit']")
                if submit_button:
                    await self.browser.click_element("button[type='submit']")
                    logger.info(f"Applied to {job_data['title']} at {job_data['company']}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Dice application error: {e}")
            await self.take_error_screenshot("apply")
            return False