"""
LinkedIn job application automator.
"""

import logging
from typing import Dict, List, Optional, Any
from src.automation.base_automator import BaseAutomator

logger = logging.getLogger(__name__)


class LinkedInAutomator(BaseAutomator):
    """LinkedIn job application automation."""
    
    def __init__(self, browser_manager):
        super().__init__(browser_manager, "linkedin")
        
        self.selectors = {
            "login_email": "#username",
            "login_password": "#password", 
            "login_button": "[type='submit']",
            "job_search": "[aria-label='Search']",
            "job_cards": ".job-card-container",
            "apply_button": ".jobs-apply-button",
            "easy_apply": "[aria-label*='Easy Apply']",
            "submit_application": "[aria-label*='Submit application']",
            "upload_resume": "input[type='file']"
        }
    
    async def login(self, credentials: Dict[str, str]) -> bool:
        """Login to LinkedIn."""
        try:
            logger.info("Logging into LinkedIn...")
            
            await self.browser.navigate_to("https://www.linkedin.com/login")
            
            # Fill login form
            await self.browser.fill_input(self.selectors["login_email"], credentials["email"])
            await self.browser.fill_input(self.selectors["login_password"], credentials["password"])
            await self.browser.click_element(self.selectors["login_button"])
            
            # Wait for login to complete
            await self.browser.wait_for_navigation()
            
            # Check if login successful
            if "feed" in self.browser.page.url or "in/" in self.browser.page.url:
                self.is_logged_in = True
                logger.info("LinkedIn login successful")
                return True
            else:
                logger.error("LinkedIn login failed")
                return False
                
        except Exception as e:
            logger.error(f"LinkedIn login error: {e}")
            await self.take_error_screenshot("login")
            return False
    
    async def search_jobs(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for jobs on LinkedIn."""
        try:
            # Navigate to jobs page
            await self.browser.navigate_to("https://www.linkedin.com/jobs/search/")
            
            # Fill search criteria
            keywords = search_params.get("keywords", "")
            location = search_params.get("location", "")
            
            if keywords:
                await self.browser.fill_input("input[aria-label*='Search jobs']", keywords)
            
            if location:
                await self.browser.fill_input("input[aria-label*='City']", location)
            
            # Submit search
            await self.browser.click_element("button[aria-label*='Search']")
            await self.browser.wait_for_navigation()
            
            # Extract job listings
            jobs = await self.browser.execute_javascript("""
                return Array.from(document.querySelectorAll('.job-card-container')).map(card => {
                    const titleEl = card.querySelector('.job-card-list__title');
                    const companyEl = card.querySelector('.job-card-container__company-name');
                    const locationEl = card.querySelector('.job-card-container__metadata-item');
                    const linkEl = card.querySelector('a[data-control-name="job_card_click"]');
                    
                    return {
                        title: titleEl ? titleEl.innerText.trim() : '',
                        company: companyEl ? companyEl.innerText.trim() : '',
                        location: locationEl ? locationEl.innerText.trim() : '',
                        url: linkEl ? linkEl.href : ''
                    };
                }).filter(job => job.url);
            """)
            
            logger.info(f"Found {len(jobs)} job listings on LinkedIn")
            return jobs[:20]  # Limit to first 20 jobs
            
        except Exception as e:
            logger.error(f"LinkedIn job search error: {e}")
            await self.take_error_screenshot("search")
            return []
    
    async def apply_to_job(self, job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> bool:
        """Apply to job on LinkedIn."""
        try:
            # Navigate to job posting
            await self.browser.navigate_to(job_data["url"])
            
            # Check if already applied
            if await self.check_already_applied(job_data["url"]):
                logger.info("Already applied to this job")
                return False
            
            # Look for Easy Apply button
            easy_apply_found = await self.browser.is_element_present(self.selectors["easy_apply"])
            
            if easy_apply_found:
                await self.browser.click_element(self.selectors["easy_apply"])
                await self.browser.human_delay(2, 4)
                
                # Fill application form
                await self.form_handler.fill_form_intelligently(profile_data)
                
                # Submit application
                submit_button = await self.browser.is_element_present(self.selectors["submit_application"])
                if submit_button:
                    await self.browser.click_element(self.selectors["submit_application"])
                    logger.info(f"Applied to {job_data['title']} at {job_data['company']}")
                    return True
                
            else:
                logger.info("Easy Apply not available, skipping job")
                return False
                
        except Exception as e:
            logger.error(f"LinkedIn application error: {e}")
            await self.take_error_screenshot("apply")
            return False