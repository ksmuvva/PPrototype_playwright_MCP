#!/usr/bin/env python3
"""
Test script to verify that our parameter adaptation logic works correctly.
"""
import asyncio
import re
from exp_tools import PlaywrightTools

async def test_adapter():
    """Test the parameter adaptation logic."""
    print("=== Testing Parameter Adaptation Logic ===")
    
    # Create PlaywrightTools instance
    tools = PlaywrightTools()
    
    try:
        # Initialize
        print("Initializing browser...")
        await tools.initialize()
        print("Browser initialized")
        
        # Navigate to example.com
        print("Navigating to example.com...")
        await tools.playwright_navigate("https://example.com")
        
        # Test the original function directly
        print("\nTest 1: Direct call with text parameter (should work)")
        result1 = await tools.playwright_smart_click(text="More information")
        print(f"Result 1: {result1}")
        
        # Navigate back
        await tools.playwright_navigate("https://example.com")
        
        # Test with selector parameter - this would normally fail but our adapter will fix it
        print("\nTest 2: Call with selector parameter (would fail without adapter)")
        
        # This is what would come from the LLM
        arguments = {"selector": "a:has-text('More information')", "capture_screenshot": True}
        print(f"Original arguments: {arguments}")
        
        try:
            # This would fail without adaptation
            result2 = await tools.playwright_smart_click(**arguments)
            print("ERROR: No exception was raised, this should have failed!")
        except TypeError as e:
            print(f"✅ Expected error received: {e}")
            
            # Now apply the adaptation logic
            print("\nApplying parameter adaptation...")
            if "selector" in arguments and "text" not in arguments:
                selector = arguments.pop("selector")
                
                # Extract text from selector
                text = None
                has_text_match = re.search(r":has-text\('([^']+)'\)", selector)
                if has_text_match:
                    text = has_text_match.group(1)
                    print(f"✅ Successfully extracted text '{text}' from selector")
                else:
                    text = selector
                    print(f"Using selector as text: '{text}'")
                
                arguments["text"] = text
            
            print(f"Adapted arguments: {arguments}")
            
            # Try again with adapted parameters
            result2 = await tools.playwright_smart_click(**arguments)
            print(f"Result after adaptation: {result2}")
            print("✅ Call succeeded after parameter adaptation")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Clean up
        print("\nCleaning up...")
        await tools.cleanup()
        print("Test complete")

if __name__ == "__main__":
    asyncio.run(test_adapter())
