#!/usr/bin/env python3
"""
Test script for playwright-stealth integration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up environment
os.environ.setdefault("PYTHONPATH", str(Path(__file__).parent.parent / "src"))

from scrapers.web_scraper.playwright_manager import PlaywrightManager

async def test_stealth_basic():
    """Test basic stealth functionality"""
    print("Testing basic stealth functionality...")

    async with PlaywrightManager(
        headless=False,  # Set to False to see the browser
        enable_stealth=True
    ) as manager:
        browser = await manager.get_browser()
        page = await manager.create_page(browser)

        try:
            # Navigate to a test page
            await page.goto("https://bot.sannysoft.com", wait_until="networkidle")
            await manager.wait_for_load(page)

            # Verify stealth measures
            stealth_status = await manager.verify_stealth(page)

            print("\n=== Stealth Status ===")
            for key, value in stealth_status.items():
                if key not in ['timestamp', 'stealth_enabled']:
                    print(f"{key}: {value}")

            # Check if webdriver is hidden (should be False or None)
            webdriver_status = stealth_status.get('webdriver')
            print(f"\nWebDriver Status: {webdriver_status}")

            if webdriver_status in [False, None]:
                print("✅ Stealth is working - WebDriver is hidden")
            else:
                print("❌ Stealth may not be working - WebDriver is visible")

            # Take screenshot
            screenshot_path = await manager.take_screenshot(page)
            if screenshot_path:
                print(f"Screenshot saved to: {screenshot_path}")

            return stealth_status

        finally:
            await page.close()
            await manager.return_browser(browser)

async def test_stealth_comparison():
    """Compare stealth vs non-stealth modes"""
    print("\n" + "="*50)
    print("Testing stealth vs non-stealth comparison...")

    # Test with stealth enabled
    print("\n--- With Stealth Enabled ---")
    async with PlaywrightManager(headless=True, enable_stealth=True) as manager:
        browser = await manager.get_browser()
        page = await manager.create_page(browser)

        try:
            await page.goto("https://bot.sannysoft.com", wait_until="networkidle")
            stealth_status = await manager.verify_stealth(page)
            print(f"WebDriver with stealth: {stealth_status.get('webdriver')}")
        finally:
            await page.close()
            await manager.return_browser(browser)

    # Test with stealth disabled
    print("\n--- With Stealth Disabled ---")
    async with PlaywrightManager(headless=True, enable_stealth=False) as manager:
        browser = await manager.get_browser()
        page = await manager.create_page(browser)

        try:
            await page.goto("https://bot.sannysoft.com", wait_until="networkidle")
            stealth_status = await manager.verify_stealth(page)
            print(f"WebDriver without stealth: {stealth_status.get('webdriver')}")
        finally:
            await page.close()
            await manager.return_browser(browser)

async def test_configuration():
    """Test configuration settings"""
    print("\n" + "="*50)
    print("Testing configuration...")

    print(f"Stealth enabled in config: {web_scraper_settings.enable_stealth}")
    print(f"Headless mode: {web_scraper_settings.headless}")
    print(f"Max browsers: {web_scraper_settings.max_browsers}")
    print(f"Proxy: {web_scraper_settings.proxy}")

async def main():
    """Main test function"""
    print("Playwright Stealth Integration Test")
    print("="*50)

    try:
        # Test configuration
        await test_configuration()

        # Test basic stealth
        await test_stealth_basic()

        # Test comparison
        await test_stealth_comparison()

        print("\n" + "="*50)
        print("✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
