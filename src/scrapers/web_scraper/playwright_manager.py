"""
Playwright browser management for web scraping.
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, Playwright
from .config import WebScraperSettings


class PlaywrightManager:
    """Manages Playwright browser instances and pages."""
    
    def __init__(self, settings: WebScraperSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.browser_pool: List[Browser] = []
        self.playwright: Optional[Playwright] = None
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Start the Playwright manager."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            self.logger.info("Playwright manager started")
    
    async def stop(self):
        """Stop the Playwright manager and close all browsers."""
        # Close all browsers in pool
        for browser in self.browser_pool:
            try:
                await browser.close()
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")
        
        self.browser_pool.clear()
        
        # Stop playwright
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            self.logger.info("Playwright manager stopped")
    
    async def get_browser(self) -> Browser:
        """Get a browser from the pool or create a new one."""
        if self.browser_pool:
            browser = self.browser_pool.pop()
            self.logger.debug("Reusing browser from pool")
            return browser
        
        if self.playwright is None:
            await self.start()
        
        # Configure browser launch options
        launch_options: Dict[str, Any] = {
            "headless": self.settings.headless,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
        }
        
        # Add proxy if configured
        if self.settings.use_proxy and self.settings.proxy_url:
            launch_options["proxy"] = {"server": self.settings.proxy_url}
        
        browser = await self.playwright.chromium.launch(**launch_options)
        self.logger.debug("Created new browser instance")
        return browser
    
    async def return_browser(self, browser: Browser):
        """Return browser to the pool or close it."""
        try:
            # Check if browser is still usable
            context = browser.contexts[0] if browser.contexts else None
            if context and not context.pages:
                # Browser is empty, can be reused
                if len(self.browser_pool) < self.settings.max_browsers:
                    self.browser_pool.append(browser)
                    self.logger.debug("Returned browser to pool")
                    return
        except Exception as e:
            self.logger.warning(f"Error checking browser state: {e}")
        
        # Close browser if can't be reused
        try:
            await browser.close()
            self.logger.debug("Closed browser instance")
        except Exception as e:
            self.logger.warning(f"Error closing browser: {e}")
    
    async def create_page(self, browser: Browser) -> Page:
        """Create a new page with configured settings."""
        page = await browser.new_page()
        
        # Set user agent
        if self.settings.custom_user_agent:
            user_agent = self.settings.custom_user_agent
        elif self.settings.rotate_user_agents:
            user_agent = random.choice(self._user_agents)
        else:
            user_agent = self._user_agents[0]
        
        await page.set_extra_http_headers({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        # Set viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Enable JavaScript
        await page.set_java_script_enabled(True)
        
        # Set timeout
        page.set_default_timeout(self.settings.page_timeout)
        
        self.logger.debug(f"Created new page with user agent: {user_agent[:50]}...")
        return page
    
    async def take_screenshot(self, page: Page, path: str) -> bool:
        """Take a screenshot of the current page."""
        try:
            await page.screenshot(path=path, full_page=True)
            self.logger.debug(f"Screenshot saved to {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return False
    
    async def get_page_content(self, page: Page) -> Dict[str, Any]:
        """Get comprehensive page content including HTML, text, and metadata."""
        try:
            # Get HTML content
            html_content = await page.content()
            
            # Get page title
            title = await page.title()
            
            # Get page URL
            url = page.url
            
            # Get text content
            text_content = await page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    
                    // Get text content
                    return document.body ? document.body.innerText : document.documentElement.innerText;
                }
            """)
            
            # Get meta tags
            meta_tags = await page.evaluate("""
                () => {
                    const metas = document.querySelectorAll('meta');
                    const metaData = {};
                    metas.forEach(meta => {
                        const name = meta.getAttribute('name') || meta.getAttribute('property');
                        const content = meta.getAttribute('content');
                        if (name && content) {
                            metaData[name] = content;
                        }
                    });
                    return metaData;
                }
            """)
            
            return {
                "url": url,
                "title": title,
                "html": html_content,
                "text": text_content,
                "meta_tags": meta_tags,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get page content: {e}")
            return {}
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get the current status of the browser pool."""
        return {
            "pool_size": len(self.browser_pool),
            "max_browsers": self.settings.max_browsers,
            "headless": self.settings.headless,
            "timeout": self.settings.page_timeout
        }
