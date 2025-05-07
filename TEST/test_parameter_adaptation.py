#!/usr/bin/env python3
"""
Test script to verify that the parameter adaptation for playwright_smart_click works correctly.
This simulates how the MCP server would adapt parameters coming from the LLM.
"""
import asyncio
from exp_tools import PlaywrightTools

async def test_parameter_adaptation():
    """Test the parameter adaptation for playwright_smart_click."""
    print("=== Testing Parameter Adaptation ===")
    tools = PlaywrightTools()
    
    try:
        # Initialize tools
        print("Initializing tools...")
        await tools.initialize()
        print("✅ Tools initialized")
        
        # Navigate to example.com
        print("\nNavigating to example.com...")
        await tools.playwright_navigate("https://example.com")
        print("✅ Navigation successful")
        
        # Test 1: Call with the correct 'text' parameter (should work)
        print("\nTest 1: Using correct 'text' parameter")
        result1 = await tools.playwright_smart_click(text="More information")
        print(f"Result 1: {result1}")
        
        # Navigate back
        await asyncio.sleep(1)
        await tools.playwright_navigate("https://example.com")
        print("Navigated back to example.com")
        
        # Test 2: Simulate the adapter for a selector parameter
        print("\nTest 2: Simulating adaptation from 'selector' to 'text'")
        
        # This is what the adapter would do
        selector = "a:has-text('More information')"
        
        # Extract text from selector
        import re
        text = None
        has_text_match = re.search(r":has-text\('([^']+)'\)", selector)
        if has_text_match:
            text = has_text_match.group(1)
        else:
            text = selector
        
        print(f"Extracted text from selector: '{text}'")
        
        # Now call with the extracted text
        result2 = await tools.playwright_smart_click(text=text)
        print(f"Result 2: {result2}")
        
        print("\n✅ Tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        # Clean up
        print("\nCleaning up...")
        await tools.cleanup()

if __name__ == "__main__":
    asyncio.run(test_parameter_adaptation())
