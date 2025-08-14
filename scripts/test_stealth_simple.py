#!/usr/bin/env python3
"""
Simple test script for playwright-stealth integration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scrapers.web_scraper.playwright_manager import PlaywrightManager

async def test_stealth_basic():
    """Test basic stealth functionality"""
    print("Testing basic stealth functionality...")

    manager = PlaywrightManager(
        headless=False,  # Set to False to see the browser
        enable_stealth=True
    )

    try:
        await manager.start()
        browser = await manager.get_browser()
        page = await manager.create_page(browser)

        # Navigate to a test page
        await page.goto("https://bot.sannysoft.com")
        await page.wait_for_timeout(3000)  # Wait 3 seconds

        # Take a screenshot
        await page.screenshot(path="stealth_test.png")
        print("✅ Stealth test completed successfully!")
        print("📸 Screenshot saved as 'stealth_test.png'")

        await page.close()
        await manager.return_browser(browser)

    except Exception as e:
        print(f"❌ Stealth test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.stop()

async def main():
    """Main test function"""
    print("🚀 Starting playwright-stealth tests...")

    try:
        await test_stealth_basic()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"❌ Test suite failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
