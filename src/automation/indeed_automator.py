"""
Indeed job application automator.
"""

import logging
from typing import Dict, List, Optional, Any
from src.automation.base_automator import BaseAutomator

logger = logging.getLogger(__name__)


class IndeedAutomator(BaseAutomator):
    """Indeed job application automation."""
    
    def __init__(self, browser_manager):
        super().__init__(browser_manager, "indeed")
        
        self.selectors = {
            "login_email": "#ifl-InputFormField-3",
            "login_password": "#ifl-InputFormField-4",
            "login_button": "button[type='submit']",
            "job_search": "#text-input-what",
            "location_search": "#text-input-where",
            "search_button": ".yosegi-InlineWhatWhere-primaryButton",
            "job_cards": "[data-jk]",
            "apply_button": "[aria-label*='Apply now']",
            "continue_button": "button[aria-label*='Continue']"
        }
    
    async def login(self, credentials: Dict[str, str]) -> bool:
        """Login to Indeed."""
        try:
            logger.info("Logging into Indeed...")
            
            await self.browser.navigate_to("https://secure.indeed.com/account/login")
            
            # Fill login form
            await self.browser.fill_input(self.selectors["login_email"], credentials["email"])
            await self.browser.fill_input(self.selectors["login_password"], credentials["password"])
            await self.browser.click_element(self.selectors["login_button"])
            
            await self.browser.wait_for_navigation()
            
            # Check login success
            if "account" in self.browser.page.url:
                self.is_logged_in = True
                logger.info("Indeed login successful")
                return True
            else:
                logger.error("Indeed login failed")
                return False
                
        except Exception as e:
            logger.error(f"Indeed login error: {e}")
            await self.take_error_screenshot("login")
            return False
    
    async def search_jobs(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for jobs on Indeed."""
        try:
            await self.browser.navigate_to("https://www.indeed.com/")
            
            # Fill search form
            keywords = search_params.get("keywords", "")
            location = search_params.get("location", "")
            
            if keywords:
                await self.browser.fill_input(self.selectors["job_search"], keywords)
            
            if location:
                await self.browser.fill_input(self.selectors["location_search"], location)
            
            await self.browser.click_element(self.selectors["search_button"])
            await self.browser.wait_for_navigation()
            
            # Extract job listings
            jobs = await self.browser.execute_javascript("""
                return Array.from(document.querySelectorAll('[data-jk]')).map(card => {
                    const titleEl = card.querySelector('h2 a span');
                    const companyEl = card.querySelector('[data-testid="company-name"]');
                    const locationEl = card.querySelector('[data-testid="job-location"]');
                    const linkEl = card.querySelector('h2 a');
                    
                    return {
                        title: titleEl ? titleEl.innerText.trim() : '',
                        company: companyEl ? companyEl.innerText.trim() : '',
                        location: locationEl ? locationEl.innerText.trim() : '',
                        url: linkEl ? 'https://indeed.com' + linkEl.getAttribute('href') : ''
                    };
                }).filter(job => job.url);
            """)
            
            logger.info(f"Found {len(jobs)} job listings on Indeed")
            return jobs[:20]
            
        except Exception as e:
            logger.error(f"Indeed job search error: {e}")
            await self.take_error_screenshot("search")
            return []
    
    async def apply_to_job(self, job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> bool:
        """Apply to job on Indeed."""
        try:
            await self.browser.navigate_to(job_data["url"])
            
            if await self.check_already_applied(job_data["url"]):
                logger.info("Already applied to this job")
                return False
            
            # Look for apply button
            apply_button = await self.browser.is_element_present(self.selectors["apply_button"])
            
            if apply_button:
                await self.browser.click_element(self.selectors["apply_button"])
                await self.browser.human_delay(2, 4)
                
                # Fill application form
                await self.form_handler.fill_form_intelligently(profile_data)
                
                # Submit application
                continue_button = await self.browser.is_element_present(self.selectors["continue_button"])
                if continue_button:
                    await self.browser.click_element(self.selectors["continue_button"])
                    logger.info(f"Applied to {job_data['title']} at {job_data['company']}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Indeed application error: {e}")
            await self.take_error_screenshot("apply")
            return False