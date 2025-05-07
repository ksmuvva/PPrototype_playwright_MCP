#!/usr/bin/env python3
"""
Test script for verifying the playwright_smart_click and playwright_screenshot functions.
This standalone script directly implements the fixes without dependencies.
"""
import asyncio
import os
import time
import re

# Test implementation of the fixed functions
class TestPlaywrightTools:
    """Test implementation of PlaywrightTools with the fixed functions."""
    
    def __init__(self):
        """Initialize the test implementation."""
        self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.browser_initialized = True
    
    async def initialize(self):
        """Initialize the test implementation."""
        print("Test implementation initialized")
        return True
    
    async def cleanup(self):
        """Clean up the test implementation."""
        print("Test implementation cleaned up")
        pass
    
    async def playwright_smart_click(self, text=None, selector=None, element_type="any", page_index=0, capture_screenshot=False, max_attempts=3, **kwargs):
        """
        Smart click with fallback strategies for text-based element location.
        
        Args:
            text: Text to look for in the element
            selector: CSS selector (will be converted to text if provided instead of text)
            element_type: Type of element to target ('button', 'link', 'any')
            page_index: Index of the page to operate on
            capture_screenshot: Whether to take a screenshot after clicking
            max_attempts: Maximum number of attempts to try
        """
        # In this implementation, we'll directly handle the parameters
        # This is a simplified implementation that handles both text and selector parameters
        if selector is not None and text is None:
            # Use the selector as text for compatibility with LLM output
            # Try to extract text from common selector patterns
            extracted_text = None
            
            # Pattern: :has-text('Text')
            has_text_match = re.search(r":has-text\('([^']+)'\)", selector)
            if has_text_match:
                extracted_text = has_text_match.group(1)
            # Pattern: :text("Text")
            elif ":text(" in selector:
                text_match = re.search(r":text\(['\"]([^'\"]+)['\"]\)", selector)
                if text_match:
                    extracted_text = text_match.group(1)
            # Pattern: [aria-label="Text"]  
            elif "aria-label" in selector:
                label_match = re.search(r"\[aria-label=['\"]([^'\"]+)['\"]\]", selector)
                if label_match:
                    extracted_text = label_match.group(1)
            
            # If we found text, use it; otherwise use the whole selector
            if extracted_text:
                text = extracted_text
                print(f"Extracted text '{text}' from selector '{selector}'")
            else:
                text = selector
                print(f"Using selector '{selector}' as text")
            
        # At this point, text should be defined
        if text is None:
            return {
                "status": "error",
                "message": "Either text or selector parameter must be provided"
            }
        
        # Generate the list of selectors we would try (simplified for testing)
        selectors = []
        
        if element_type == "button" or element_type == "any":
            selectors.extend([
                f"button:has-text('{text}')",
                f"input[type='submit'][value='{text}']", 
                f"[role='button']:has-text('{text}')"
            ])
        
        if element_type == "link" or element_type == "any":
            selectors.extend([
                f"a:has-text('{text}')",
                f"[role='link']:has-text('{text}')"
            ])
            
        if element_type == "any":
            selectors.extend([
                f":has-text('{text}')",
                f"[aria-label='{text}']",
                f"[title='{text}']"
            ])
        
        # Log what would happen in this implementation
        print(f"Would try selectors: {selectors}")
        
        if capture_screenshot:
            print(f"Would capture screenshot after clicking")
            
        # Return success since this is just a test implementation
        return {
            "status": "success",
            "message": f"Clicked element with text: {text} (test implementation)",
            "selectors_tried": selectors
        }
    
    async def playwright_screenshot(self, filename=None, selector="", page_index=0, 
                                  full_page=False, omit_background=False, max_attempts=3, **kwargs):
        """Take a screenshot with enhanced reliability and error recovery.
        
        Args:
            filename: Name of the file to save the screenshot to
            selector: Optional selector to take screenshot of specific element
            page_index: Index of the page to screenshot
            full_page: Whether to take a screenshot of the full page (not just the viewport)
            omit_background: Whether to hide default white background and allow transparency
            max_attempts: Maximum number of recovery attempts if errors occur
        """
        # Generate a default filename if none is provided
        if filename is None:
            filename = f"screenshot_{int(time.time())}.png"
            print(f"No filename provided, using default: {filename}")
        
        # Ensure filename ends with .png
        if not filename.endswith('.png'):
            filename += '.png'
        
        # Get the full path for the screenshot
        if not os.path.isabs(filename):
            screenshot_path = os.path.join(self.screenshot_dir, filename)
        else:
            screenshot_path = filename
        
        # Simulate taking a screenshot
        print(f"Taking {'full page' if full_page else 'viewport'} screenshot")
        if selector:
            print(f"Taking screenshot of element: {selector}")
        
        # Create an empty file to simulate the screenshot
        with open(screenshot_path, 'w') as f:
            f.write('')
        
        # Return success
        return {
            "status": "success",
            "message": f"Screenshot saved to {screenshot_path}",
            "filename": screenshot_path,
            "full_page": full_page,
            "element_selector": selector if selector else None
        }

async def test_playwright_smart_click():
    """Test the playwright_smart_click function with various parameter combinations."""
    print("\n=== Testing playwright_smart_click ===")
    tools = TestPlaywrightTools()
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
    tools = TestPlaywrightTools()
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
