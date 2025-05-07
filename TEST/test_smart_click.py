#!/usr/bin/env python3
"""
Test script for the playwright_smart_click function.
"""
import asyncio
from exp_tools import PlaywrightTools

async def test_smart_click():
    """Test the playwright_smart_click function."""
    tools = PlaywrightTools()
    try:
        print("Initializing PlaywrightTools...")
        await tools.initialize()
        
        # First navigate to a test page
        print("Navigating to a test page...")
        await tools.playwright_navigate("https://example.com")
        
        # Try to click on "More information" link
        print("Attempting smart click on 'More information'...")
        result = await tools.playwright_smart_click("More information")
        print(f"Smart click result: {result}")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        print("Cleaning up...")
        await tools.cleanup()

if __name__ == "__main__":
    asyncio.run(test_smart_click())
