"""
Test script for Phase 1.3 functionality.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.browser_manager import BrowserManager
from src.core.profile_manager import ProfileManager
from src.automation.job_site_factory import JobSiteFactory
from src.utils.logger import configure_logging

async def test_job_site_automation():
    """Test job site automation functionality."""
    print("🔧 Testing Job Site Automation...")
    
    configure_logging()
    profile_manager = ProfileManager()
    browser_manager = BrowserManager()
    
    try:
        # Load profile
        profiles = profile_manager.list_profiles()
        if not profiles:
            print("❌ No profiles found")
            return False
        
        profile = profile_manager.load_profile(profiles[0]['profile_name'])
        profile_data = profile_manager.get_profile_for_application(profile.id)
        
        # Initialize browser
        await browser_manager.initialize()
        
        # Test LinkedIn automator
        print("  🔗 Testing LinkedIn automator...")
        linkedin = JobSiteFactory.create_automator("linkedin", browser_manager)
        
        # Test job search (without login)
        search_params = {
            "keywords": "python developer",
            "location": "remote"
        }
        
        await browser_manager.navigate_to("https://www.linkedin.com/jobs/search/")
        jobs = await linkedin.search_jobs(search_params)
        print(f"  ✅ Found {len(jobs)} jobs on LinkedIn")
        
        # Test form detection
        forms = await linkedin.form_handler.detect_forms()
        print(f"  ✅ Detected {len(forms)} forms on page")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        await browser_manager.cleanup()

if __name__ == "__main__":
    success = asyncio.run(test_job_site_automation())
    print("✅ Phase 1.3 ready!" if success else "❌ Tests failed")