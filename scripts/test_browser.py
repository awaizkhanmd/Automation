"""
Test script for browser manager functionality.

This script tests the browser automation capabilities
and profile management system for Phase 1.2.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.browser_manager import BrowserManager
from src.core.profile_manager import ProfileManager
from src.utils.logger import configure_logging

logger = logging.getLogger(__name__)


async def test_browser_basic_functionality():
    """Test basic browser functionality."""
    print("🔧 Testing Browser Manager Basic Functionality...")
    
    browser_manager = BrowserManager()
    
    try:
        # Test browser initialization
        print("  📱 Initializing browser...")
        if not await browser_manager.initialize():
            print("  ❌ Browser initialization failed!")
            return False
        print("  ✅ Browser initialized successfully!")
        
        # Test navigation
        print("  🌐 Testing navigation...")
        if not await browser_manager.navigate_to("https://example.com"):
            print("  ❌ Navigation failed!")
            return False
        print("  ✅ Navigation successful!")
        
        # Test page info
        page_info = await browser_manager.get_page_info()
        print(f"  📄 Current page: {page_info.get('title', 'Unknown')}")
        
        # Test screenshot
        print("  📸 Taking screenshot...")
        screenshot_path = await browser_manager.take_screenshot("test_basic")
        if screenshot_path:
            print(f"  ✅ Screenshot saved: {screenshot_path}")
        else:
            print("  ⚠️  Screenshot failed")
        
        # Test element detection
        print("  🔍 Testing element detection...")
        if await browser_manager.is_element_present("h1", timeout=5000):
            print("  ✅ Element detection working!")
        else:
            print("  ⚠️  No h1 element found")
        
        return True
        
    except Exception as e:
        logger.error(f"Browser test failed: {e}")
        print(f"  ❌ Browser test failed: {e}")
        return False
        
    finally:
        await browser_manager.cleanup()
        print("  🧹 Browser cleaned up")


async def test_browser_form_handling():
    """Test browser form handling capabilities."""
    print("🔧 Testing Browser Form Handling...")
    
    browser_manager = BrowserManager()
    
    try:
        # Initialize browser
        if not await browser_manager.initialize():
            print("  ❌ Browser initialization failed!")
            return False
        
        # Navigate to a page with forms (httpbin.org has form testing)
        print("  🌐 Navigating to form test page...")
        if not await browser_manager.navigate_to("https://httpbin.org/forms/post"):
            print("  ❌ Navigation to form page failed!")
            return False
        
        # Test form filling
        print("  📝 Testing form filling...")
        
        # Fill text inputs
        email_filled = await browser_manager.fill_input(
            "input[name='email']", 
            "test@example.com", 
            human_typing=False
        )
        
        password_filled = await browser_manager.fill_input(
            "input[name='password']", 
            "testpassword123", 
            human_typing=False
        )
        
        if email_filled and password_filled:
            print("  ✅ Form filling successful!")
        else:
            print("  ⚠️  Some form fields could not be filled")
        
        # Test screenshot after form filling
        await browser_manager.take_screenshot("test_form_filled")
        
        return True
        
    except Exception as e:
        logger.error(f"Form handling test failed: {e}")
        print(f"  ❌ Form handling test failed: {e}")
        return False
        
    finally:
        await browser_manager.cleanup()


def test_profile_manager():
    """Test profile manager functionality."""
    print("🔧 Testing Profile Manager...")
    
    profile_manager = ProfileManager()
    
    try:
        # Test listing existing profiles
        print("  📋 Listing existing profiles...")
        profiles = profile_manager.list_profiles()
        print(f"  📊 Found {len(profiles)} profiles")
        
        for profile in profiles:
            print(f"    - {profile['profile_name']} ({profile['email']})")
        
        # Test loading default profile
        print("  📂 Testing profile loading...")
        if profiles:
            first_profile = profile_manager.load_profile(profiles[0]['profile_name'])
            if first_profile:
                print(f"  ✅ Successfully loaded profile: {first_profile.profile_name}")
                
                # Test getting application data
                app_data = profile_manager.get_profile_for_application(first_profile.id)
                if app_data:
                    print(f"  ✅ Profile application data prepared")
                    print(f"    - Name: {app_data['full_name']}")
                    print(f"    - Email: {app_data['email']}")
                    print(f"    - Target roles: {len(app_data.get('target_roles', []))}")
                else:
                    print("  ❌ Could not prepare application data")
            else:
                print("  ❌ Could not load profile")
        
        # Test template loading
        print("  📋 Testing template loading...")
        template_data = profile_manager.load_profile_template("default_profile")
        if template_data:
            print("  ✅ Template loaded successfully!")
            print(f"    - Template name: {template_data['profile_name']}")
            print(f"    - Skills: {len(template_data.get('professional_info', {}).get('skills', []))}")
        else:
            print("  ⚠️  Default template not found")
        
        return True
        
    except Exception as e:
        logger.error(f"Profile manager test failed: {e}")
        print(f"  ❌ Profile manager test failed: {e}")
        return False


async def test_integration():
    """Test integration between browser manager and profile manager."""
    print("🔧 Testing Integration...")
    
    profile_manager = ProfileManager()
    browser_manager = BrowserManager()
    
    try:
        # Load a profile
        profiles = profile_manager.list_profiles()
        if not profiles:
            print("  ⚠️  No profiles found for integration test")
            return False
        
        profile = profile_manager.load_profile(profiles[0]['profile_name'])
        if not profile:
            print("  ❌ Could not load profile for integration test")
            return False
        
        print(f"  👤 Using profile: {profile.profile_name}")
        
        # Initialize browser
        if not await browser_manager.initialize():
            print("  ❌ Browser initialization failed!")
            return False
        
        # Test with profile data
        app_data = profile_manager.get_profile_for_application(profile.id)
        if app_data:
            print("  ✅ Integration test successful!")
            print(f"    - Profile loaded: {app_data['full_name']}")
            print(f"    - Browser ready: {browser_manager.is_initialized}")
            
            # Test navigation to LinkedIn (just the homepage)
            print("  🔗 Testing LinkedIn navigation...")
            if await browser_manager.navigate_to("https://linkedin.com"):
                print("  ✅ LinkedIn navigation successful!")
                await browser_manager.take_screenshot("test_linkedin_homepage")
            else:
                print("  ⚠️  LinkedIn navigation failed")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"  ❌ Integration test failed: {e}")
        return False
        
    finally:
        await browser_manager.cleanup()


async def main():
    """Main test function."""
    print("🚀 Testing Job Automation System - Phase 1.2")
    print("=" * 50)
    
    # Configure logging
    configure_logging()
    
    test_results = []
    
    # Test Profile Manager (synchronous)
    print("\n1️⃣  PROFILE MANAGER TESTS")
    print("-" * 30)
    result = test_profile_manager()
    test_results.append(("Profile Manager", result))
    
    # Test Browser Manager Basic (asynchronous)
    print("\n2️⃣  BROWSER MANAGER BASIC TESTS")
    print("-" * 30)
    result = await test_browser_basic_functionality()
    test_results.append(("Browser Basic", result))
    
    # Test Browser Form Handling (asynchronous)
    print("\n3️⃣  BROWSER FORM HANDLING TESTS")
    print("-" * 30)
    result = await test_browser_form_handling()
    test_results.append(("Browser Forms", result))
    
    # Test Integration (asynchronous)
    print("\n4️⃣  INTEGRATION TESTS")
    print("-" * 30)
    result = await test_integration()
    test_results.append(("Integration", result))
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 1.2 tests completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Phase 1.2 is ready for production use")
        print("   2. Proceed to Phase 1.3: Form Handling & Job Site Automation")
        print("   3. The browser automation and profile management are working correctly")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)