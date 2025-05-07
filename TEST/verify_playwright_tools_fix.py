#!/usr/bin/env python3
"""
Verification script for the fixed playwright_smart_click and playwright_screenshot functions.
This script tests both the parameter adaptation and the actual function calls.
"""
import os
import asyncio
import sys
from pprint import pprint

# Try to import the tools
# Import our fallback implementation from expiremental-new.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the PlaywrightTools class from expiremental-new.py
try:
    # Create a placeholder class to test our fallback implementation
    class PlaywrightToolsFallback:
        def __init__(self):
            self.browser_initialized = False
            self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(self.screenshot_dir, exist_ok=True)
            
        async def initialize(self):
            print("Using test implementation")
            return True
            
        async def cleanup(self):
            print("Cleaning up test implementation")
            pass
            
        # Import our fixed functions from expiremental-new.py
        from expiremental_new import PlaywrightTools
        # Copy the fixed methods into our test class
        playwright_smart_click = PlaywrightTools.playwright_smart_click
        playwright_screenshot = PlaywrightTools.playwright_screenshot
            
    print("✅ Created test implementation with the fixed functions")
except ImportError:
    print("❌ Failed to import fixed implementation")
    sys.exit(1)

async def test_playwright_smart_click():
    """Test the playwright_smart_click function with various parameter combinations."""
    print("\n=== Testing playwright_smart_click ===")
    tools = PlaywrightTools()
    await tools.initialize()
    
    print("\nTest 1: Using text parameter (expected: success)")
    result1 = await tools.playwright_smart_click(text="Click me")
    print(f"Status: {result1.get('status')}")
    print(f"Message: {result1.get('message')}")
    
    print("\nTest 2: Using selector parameter instead of text (expected: success, should adapt)")
    result2 = await tools.playwright_smart_click(selector="a:has-text('More information')")
    print(f"Status: {result2.get('status')}")
    print(f"Message: {result2.get('message')}")
    
    print("\nTest 3: Using selector with complex pattern (expected: success, should extract text)")
    result3 = await tools.playwright_smart_click(selector="[aria-label='Close dialog']")
    print(f"Status: {result3.get('status')}")
    print(f"Message: {result3.get('message')}")
    
    print("\nTest 4: Using no parameters (expected: error)")
    result4 = await tools.playwright_smart_click()
    print(f"Status: {result4.get('status')}")
    print(f"Message: {result4.get('message')}")
    
    await tools.cleanup()

async def test_playwright_screenshot():
    """Test the playwright_screenshot function with and without a filename parameter."""
    print("\n=== Testing playwright_screenshot ===")
    tools = PlaywrightTools()
    await tools.initialize()
    
    print("\nTest 1: Using filename parameter (expected: success)")
    result1 = await tools.playwright_screenshot(filename="test_screenshot.png")
    print(f"Status: {result1.get('status')}")
    print(f"Message: {result1.get('message')}")
    if 'filename' in result1:
        print(f"Filename: {result1['filename']}")
    
    print("\nTest 2: Without filename parameter (expected: success with default name)")
    result2 = await tools.playwright_screenshot()
    print(f"Status: {result2.get('status')}")
    print(f"Message: {result2.get('message')}")
    if 'filename' in result2:
        print(f"Generated filename: {result2['filename']}")
    
    await tools.cleanup()

async def main():
    """Run all tests."""
    print("=== Playwright Tools Parameter Fix Verification ===")
    
    print("\nTesting playwright_smart_click function...")
    await test_playwright_smart_click()
    
    print("\nTesting playwright_screenshot function...")
    await test_playwright_screenshot()
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    asyncio.run(main())
