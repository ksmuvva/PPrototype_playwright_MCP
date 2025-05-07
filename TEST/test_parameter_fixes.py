"""
Verification script for the parameter mismatch fixes.

This script tests both the playwright_smart_click function with a selector parameter
and the playwright_screenshot function without a filename parameter.
"""
import asyncio
import os

from exp_tools import PlaywrightTools
from playwright_function_patches import apply_patches

async def test_parameter_fixes():
    """Test the parameter mismatch fixes."""
    # Initialize the tools
    print("Initializing PlaywrightTools...")
    tools = PlaywrightTools()
    await tools.initialize()
    
    # Apply our function patches
    print("Applying function patches...")
    apply_patches(tools)
    
    # Test 1: Navigate to a test website
    print("\n=== Test 1: Navigation ===")
    navigation_result = await tools.playwright_navigate("https://example.com")
    print(f"Navigation result: {navigation_result['status']}")
    
    # Test 2: Use playwright_smart_click with selector parameter
    print("\n=== Test 2: Smart Click with selector parameter ===")
    click_result = await tools.playwright_smart_click(selector="a:has-text('More information')")
    print(f"Smart click result: {click_result['status']}")
    print(f"Message: {click_result.get('message', 'No message')}")
    
    # Test 3: Use playwright_screenshot without filename
    print("\n=== Test 3: Screenshot without filename parameter ===")
    screenshot_result = await tools.playwright_screenshot()
    print(f"Screenshot result: {screenshot_result['status']}")
    print(f"Message: {screenshot_result.get('message', 'No message')}")
    if 'filename' in screenshot_result:
        print(f"Screenshot saved to: {screenshot_result['filename']}")
    
    # Clean up
    print("\nCleaning up...")
    await tools.cleanup()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    print("=== Testing Parameter Mismatch Fixes ===")
    asyncio.run(test_parameter_fixes())
