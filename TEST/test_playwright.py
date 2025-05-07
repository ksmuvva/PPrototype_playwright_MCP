#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Testing Playwright installation...")
    try:
        async with async_playwright() as playwright:
            print("Playwright initialized successfully")
            
            # Try to launch browser
            print("Launching chromium browser...")
            browser = await playwright.chromium.launch(headless=True)
            
            # Create a page
            print("Creating new page...")
            page = await browser.new_page()
            
            # Navigate to a site
            print("Navigating to example.com...")
            await page.goto("https://example.com")
            
            # Get page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Take a screenshot
            print("Taking screenshot...")
            await page.screenshot(path="example.png")
            
            # Close browser
            print("Closing browser...")
            await browser.close()
            
            print("Playwright test completed successfully!")
            return True
            
    except Exception as e:
        print(f"Error testing Playwright: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"Test {'passed' if success else 'failed'}") 