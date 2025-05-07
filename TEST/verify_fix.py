#!/usr/bin/env python3
"""
Verification script for the fixed playwright_smart_click function in exp_tools.py.
This script demonstrates that the fixed function works correctly.
"""
import asyncio
import time
from exp_tools import PlaywrightTools

async def test_smart_click():
    """Test the fixed playwright_smart_click function with several different scenarios."""
    tools = PlaywrightTools()
    
    try:
        # Initialize the browser
        print("Initializing PlaywrightTools...")
        await tools.initialize()
        print("✅ Browser initialized")
        
        # First test: Navigate to Example.com and click "More information"
        print("\nTest 1: Navigate to example.com and click 'More information'")
        nav_result = await tools.playwright_navigate("https://example.com")
        print(f"Navigation status: {nav_result['status']}")
        
        # Take a screenshot for reference
        screenshot_result = await tools.playwright_screenshot("before_click.png")
        print(f"Screenshot saved to: {screenshot_result.get('filename')}")
        
        # Use smart_click to click the "More information" link
        print("Clicking 'More information' with smart_click...")
        click_result = await tools.playwright_smart_click("More information", element_type="link", capture_screenshot=True)
        print(f"Smart click result: {click_result}")
        
        # Verify we're on the IANA page
        if "iana" in tools.pages[0].url.lower():
            print("✅ Successfully clicked and navigated to IANA page")
        else:
            print("❌ Navigation failed or went to unexpected page")
            
        # Take another screenshot to verify
        await tools.playwright_screenshot("after_click.png")
        
        # Second test: Try a click on text that doesn't exist
        print("\nTest 2: Try to click non-existent text")
        nonexistent_result = await tools.playwright_smart_click("This text does not exist", max_attempts=2)
        print(f"Expected error result: {nonexistent_result}")
        if nonexistent_result["status"] == "error":
            print("✅ Correctly handled non-existent element")
        
        # Return to example.com for the third test
        print("\nReturning to example.com...")
        await tools.playwright_navigate("https://example.com")
        
        # Third test: Test with different element types
        print("\nTest 3: Test with different element types")
        # Try with "any" element type (default)
        any_result = await tools.playwright_smart_click("More information")
        print(f"'any' element type result: {any_result['status']}")
        
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Cleanup
        print("\nCleaning up resources...")
        await tools.cleanup()
        print("Cleanup complete")

if __name__ == "__main__":
    print("=== Testing Fixed playwright_smart_click Function ===")
    asyncio.run(test_smart_click())
    print("=== Testing Complete ===")
