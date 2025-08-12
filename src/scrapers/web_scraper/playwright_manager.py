from playwright.async_api import async_playwright, Browser, Page
import asyncio
import logging
from typing import Optional, Dict, Any, List
import random
from datetime import datetime

class PlaywrightManager:
    """
    Manages Playwright browser instances with pooling and configuration
    """

    def __init__(self, headless: bool = True, proxy: Optional[str] = None, max_browsers: int = 5):
        self.headless = headless
        self.proxy = proxy
        self.max_browsers = max_browsers
        self.logger = logging.getLogger(__name__)
        self.browser_pool: List[Browser] = []
        self.playwright = None
        self._lock = asyncio.Lock()

        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]

        self.logger.info(f"PlaywrightManager initialized with max_browsers={max_browsers}, headless={headless}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self):
        """Start the Playwright instance"""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            self.logger.info("Playwright started")

    async def stop(self):
        """Stop all browsers and Playwright instance"""
        async with self._lock:
            # Close all browsers in pool
            for browser in self.browser_pool:
                try:
                    await browser.close()
                except Exception as e:
                    self.logger.warning(f"Error closing browser: {e}")

            self.browser_pool.clear()

            # Stop Playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                self.logger.info("Playwright stopped")

    async def get_browser(self) -> Browser:
        """Get a browser from the pool or create a new one"""
        async with self._lock:
            if self.browser_pool:
                browser = self.browser_pool.pop()
                self.logger.debug("Reusing browser from pool")
                return browser

            # Create new browser
            await self.start()

            browser_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection"
            ]

            browser = await self.playwright.chromium.launch(
                headless=self.headless,
                proxy={
                    "server": self.proxy
                } if self.proxy else None,
                args=browser_args
            )

            self.logger.debug("Created new browser")
            return browser

    async def return_browser(self, browser: Browser):
        """Return browser to the pool"""
        async with self._lock:
            if len(self.browser_pool) < self.max_browsers:
                try:
                    # Check if browser is still responsive
                    pages = browser.pages
                    if pages:
                        # Close all pages except one
                        for page in pages[1:]:
                            await page.close()

                    self.browser_pool.append(browser)
                    self.logger.debug("Returned browser to pool")
                except Exception as e:
                    self.logger.warning(f"Error returning browser to pool: {e}")
                    await browser.close()
            else:
                await browser.close()
                self.logger.debug("Closed browser (pool full)")

    async def create_page(self, browser: Browser) -> Page:
        """Create a new page with configured settings"""
        page = await browser.new_page()

        # Set random user agent
        user_agent = random.choice(self.user_agents)
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
        page.set_default_timeout(30000)

        # Block unnecessary resources
        await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}", lambda route: route.abort())

        self.logger.debug(f"Created page with user agent: {user_agent[:50]}...")
        return page

    async def take_screenshot(self, page: Page, path: Optional[str] = None) -> Optional[str]:
        """Take a screenshot of the current page"""
        try:
            if path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"screenshots/screenshot_{timestamp}.png"

            await page.screenshot(path=path, full_page=True)
            self.logger.debug(f"Screenshot saved to {path}")
            return path
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None

    async def get_page_content(self, page: Page) -> Dict[str, Any]:
        """Get comprehensive page content and metadata"""
        try:
            # Get basic page info
            title = await page.title()
            url = page.url

            # Get page content
            content = await page.content()

            # Get page metrics
            metrics = await page.evaluate("""
                () => {
                    return {
                        width: window.innerWidth,
                        height: window.innerHeight,
                        scrollHeight: document.documentElement.scrollHeight,
                        scrollWidth: document.documentElement.scrollWidth,
                        loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart
                    }
                }
            """)

            return {
                "title": title,
                "url": url,
                "content": content,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get page content: {e}")
            return {}

    async def wait_for_load(self, page: Page, timeout: int = 30000):
        """Wait for page to load completely"""
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception as e:
            self.logger.warning(f"Timeout waiting for page load: {e}")

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status"""
        return {
            "pool_size": len(self.browser_pool),
            "max_browsers": self.max_browsers,
            "headless": self.headless,
            "proxy": self.proxy,
            "timestamp": datetime.utcnow().isoformat()
        }
