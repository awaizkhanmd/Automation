"""
Browser management and automation using Playwright.

This module provides centralized browser management with human-like behavior,
error handling, and screenshot capabilities for debugging.
"""

import asyncio
import logging
import time
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from config.settings import get_settings
from src.utils.helpers import ensure_directory_exists, get_timestamp_string

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Browser manager for handling Playwright browser instances.
    
    Provides centralized browser management with human-like behavior,
    error handling, and debugging capabilities.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._is_initialized = False
        
        # Browser configuration
        self.browser_config = {
            "headless": self.settings.browser_headless,
            "slow_mo": 100,  # Slow down actions for human-like behavior
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ]
        }
        
        # Screenshots directory
        self.screenshots_dir = ensure_directory_exists("data/screenshots")
    
    async def initialize(self) -> bool:
        """
        Initialize browser and create context.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Initializing browser manager...")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser (Chrome/Chromium)
            self.browser = await self.playwright.chromium.launch(**self.browser_config)
            
            # Create browser context with realistic settings
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                }
            )
            
            # Create new page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.settings.browser_timeout)
            
            # Add stealth settings to avoid detection
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {},
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            self._is_initialized = True
            logger.info("Browser manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser manager: {e}")
            await self.cleanup()
            return False
    
    async def navigate_to(self, url: str, wait_for_load: bool = True) -> bool:
        """
        Navigate to a specific URL with human-like behavior.
        
        Args:
            url: Target URL
            wait_for_load: Whether to wait for page load
            
        Returns:
            bool: True if navigation successful
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        try:
            logger.info(f"Navigating to: {url}")
            
            # Navigate to URL
            response = await self.page.goto(url, wait_until="domcontentloaded")
            
            if wait_for_load:
                # Wait for network to be idle
                await self.page.wait_for_load_state("networkidle", timeout=30000)
            
            # Add human-like delay
            await self.human_delay(1, 3)
            
            # Check if navigation was successful
            if response and response.status < 400:
                logger.info(f"Successfully navigated to: {self.page.url}")
                return True
            else:
                logger.warning(f"Navigation returned status: {response.status if response else 'None'}")
                return False
                
        except PlaywrightTimeoutError:
            logger.error(f"Timeout while navigating to: {url}")
            await self.take_screenshot("navigation_timeout")
            return False
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            await self.take_screenshot("navigation_error")
            return False
    
    async def wait_for_element(self, selector: str, timeout: int = 10000, state: str = "visible") -> bool:
        """
        Wait for element to appear with specified state.
        
        Args:
            selector: CSS selector or XPath
            timeout: Timeout in milliseconds
            state: Element state (visible, attached, detached, hidden)
            
        Returns:
            bool: True if element found
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            logger.debug(f"Element found: {selector}")
            return True
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout waiting for element: {selector}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for element {selector}: {e}")
            return False
    
    async def click_element(self, selector: str, timeout: int = 10000, human_like: bool = True) -> bool:
        """
        Click element with human-like behavior.
        
        Args:
            selector: CSS selector or XPath
            timeout: Timeout in milliseconds
            human_like: Add human-like delays and movements
            
        Returns:
            bool: True if click successful
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        try:
            # Wait for element to be clickable
            await self.page.wait_for_selector(selector, timeout=timeout, state="visible")
            
            # Scroll element into view
            await self.page.locator(selector).scroll_into_view_if_needed()
            
            if human_like:
                # Add human-like delay before clicking
                await self.human_delay(0.5, 1.5)
                
                # Hover before clicking (human-like behavior)
                await self.page.hover(selector)
                await self.human_delay(0.2, 0.8)
            
            # Click the element
            await self.page.click(selector)
            logger.debug(f"Clicked element: {selector}")
            
            if human_like:
                # Add delay after clicking
                await self.human_delay(0.5, 2.0)
            
            return True
            
        except PlaywrightTimeoutError:
            logger.error(f"Timeout clicking element: {selector}")
            await self.take_screenshot("click_timeout")
            return False
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {e}")
            await self.take_screenshot("click_error")
            return False
    
    async def fill_input(self, selector: str, value: str, clear_first: bool = True, human_typing: bool = True) -> bool:
        """
        Fill input field with human-like typing.
        
        Args:
            selector: CSS selector for input field
            value: Value to type
            clear_first: Clear field before typing
            human_typing: Use human-like typing speed
            
        Returns:
            bool: True if fill successful
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        try:
            # Wait for input field
            await self.page.wait_for_selector(selector, timeout=10000, state="visible")
            
            # Focus on the input field
            await self.page.focus(selector)
            await self.human_delay(0.2, 0.5)
            
            if clear_first:
                # Clear existing content
                await self.page.fill(selector, "")
                await self.human_delay(0.1, 0.3)
            
            if human_typing:
                # Type with human-like speed
                await self.page.type(selector, value, delay=random.randint(50, 150))
            else:
                # Fast fill
                await self.page.fill(selector, value)
            
            logger.debug(f"Filled input {selector} with value: {value[:20]}...")
            
            # Add delay after typing
            await self.human_delay(0.3, 0.8)
            return True
            
        except PlaywrightTimeoutError:
            logger.error(f"Timeout filling input: {selector}")
            await self.take_screenshot("fill_timeout")
            return False
        except Exception as e:
            logger.error(f"Error filling input {selector}: {e}")
            await self.take_screenshot("fill_error")
            return False
    
    async def select_dropdown_option(self, selector: str, value: str, by_value: bool = True) -> bool:
        """
        Select option from dropdown.
        
        Args:
            selector: CSS selector for select element
            value: Option value or text
            by_value: Select by value (True) or by text (False)
            
        Returns:
            bool: True if selection successful
        """
        if not self.page:
            logger.error("Browser not initialized")
            return False
        
        try:
            # Wait for select element
            await self.page.wait_for_selector(selector, timeout=10000, state="visible")
            
            if by_value:
                await self.page.select_option(selector, value=value)
            else:
                await self.page.select_option(selector, label=value)
            
            logger.debug(f"Selected option {value} in dropdown {selector}")
            await self.human_delay(0.3, 0.8)
            return True
            
        except Exception as e:
            logger.error(f"Error selecting dropdown option {selector}: {e}")
            await self.take_screenshot("dropdown_error")
            return False
    
    async def get_element_text(self, selector: str, timeout: int = 10000) -> Optional[str]:
        """
        Get text content of element.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            Element text or None if not found
        """
        if not self.page:
            logger.error("Browser not initialized")
            return None
        
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout, state="visible")
            text = await element.text_content()
            return text.strip() if text else None
        except Exception as e:
            logger.warning(f"Could not get text for element {selector}: {e}")
            return None
    
    async def get_element_attribute(self, selector: str, attribute: str, timeout: int = 10000) -> Optional[str]:
        """
        Get attribute value of element.
        
        Args:
            selector: CSS selector
            attribute: Attribute name
            timeout: Timeout in milliseconds
            
        Returns:
            Attribute value or None if not found
        """
        if not self.page:
            logger.error("Browser not initialized")
            return None
        
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout, state="attached")
            value = await element.get_attribute(attribute)
            return value
        except Exception as e:
            logger.warning(f"Could not get attribute {attribute} for element {selector}: {e}")
            return None
    
    async def is_element_present(self, selector: str, timeout: int = 5000) -> bool:
        """
        Check if element is present on page.
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            bool: True if element is present
        """
        if not self.page:
            return False
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state="attached")
            return True
        except:
            return False
    
    async def scroll_to_element(self, selector: str) -> bool:
        """
        Scroll element into view.
        
        Args:
            selector: CSS selector
            
        Returns:
            bool: True if scroll successful
        """
        if not self.page:
            return False
        
        try:
            await self.page.locator(selector).scroll_into_view_if_needed()
            await self.human_delay(0.5, 1.0)
            return True
        except Exception as e:
            logger.warning(f"Could not scroll to element {selector}: {e}")
            return False
    
    async def scroll_page(self, direction: str = "down", pixels: int = 500) -> bool:
        """
        Scroll page in specified direction.
        
        Args:
            direction: Scroll direction (up, down)
            pixels: Number of pixels to scroll
            
        Returns:
            bool: True if scroll successful
        """
        if not self.page:
            return False
        
        try:
            if direction.lower() == "down":
                await self.page.evaluate(f"window.scrollBy(0, {pixels})")
            else:
                await self.page.evaluate(f"window.scrollBy(0, -{pixels})")
            
            await self.human_delay(0.5, 1.5)
            return True
        except Exception as e:
            logger.error(f"Error scrolling page: {e}")
            return False
    
    async def human_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """
        Add human-like delay between actions.
        
        Args:
            min_seconds: Minimum delay
            max_seconds: Maximum delay
        """
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def take_screenshot(self, name: str = "screenshot", full_page: bool = False) -> Optional[str]:
        """
        Take screenshot for debugging.
        
        Args:
            name: Screenshot name
            full_page: Capture full page
            
        Returns:
            Screenshot file path or None
        """
        if not self.page:
            return None
        
        try:
            timestamp = get_timestamp_string()
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            await self.page.screenshot(
                path=str(filepath),
                full_page=full_page
            )
            
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    async def get_page_info(self) -> Dict[str, Any]:
        """
        Get current page information.
        
        Returns:
            Dict with page information
        """
        if not self.page:
            return {}
        
        try:
            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "viewport": self.page.viewport_size,
            }
        except Exception as e:
            logger.error(f"Error getting page info: {e}")
            return {}
    
    async def execute_javascript(self, script: str) -> Any:
        """
        Execute JavaScript on the page.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Script result
        """
        if not self.page:
            return None
        
        try:
            result = await self.page.evaluate(script)
            return result
        except Exception as e:
            logger.error(f"Error executing JavaScript: {e}")
            return None
    
    async def wait_for_navigation(self, timeout: int = 30000) -> bool:
        """
        Wait for page navigation to complete.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            bool: True if navigation completed
        """
        if not self.page:
            return False
        
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            logger.warning("Timeout waiting for navigation")
            return False
        except Exception as e:
            logger.error(f"Error waiting for navigation: {e}")
            return False
    
    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            self._is_initialized = False
            logger.info("Browser manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if browser manager is initialized."""
        return self._is_initialized and self.page is not None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.cleanup())