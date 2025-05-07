#!/usr/bin/env python3
"""
Test script to verify that the playwright_fill function can now handle both 'text' and 'value' parameters.
"""
import asyncio
import sys
import traceback
from typing import Dict, Any

async def test_fill_parameter_handling():
    """Test that the playwright_fill function handles both 'text' and 'value' parameters."""
    print("\n🔍 TESTING PLAYWRIGHT_FILL PARAMETER HANDLING")
    print("=" * 60)
    
    try:
        # Import the PlaywrightTools class
        print("\nStep 1: Importing PlaywrightTools...")
        from exp_tools import PlaywrightTools
        print("✅ Successfully imported PlaywrightTools")
        
        # Create an instance
        print("\nStep 2: Creating PlaywrightTools instance...")
        tools = PlaywrightTools()
        print("✅ Successfully created PlaywrightTools instance")
        
        # Import and apply patches
        print("\nStep 3: Importing and applying function patches...")
        try:
            from playwright_function_patches import apply_patches
            apply_patches(tools)
            print("✅ Successfully applied parameter patches")
        except Exception as e:
            print(f"❌ Error applying patches: {e}")
            traceback.print_exc()
            return False
        
        # Initialize browser
        print("\nStep 4: Initializing browser...")
        await tools.initialize()
        print("✅ Browser initialized")
        
        # Test with text parameter
        print("\nStep 5: Testing fill with 'text' parameter...")
        result_text = await tools.playwright_fill(
            selector="#search", 
            text="test search",
            page_index=0
        )
        print(f"Result with 'text' parameter: {result_text}")
        
        # Test with value parameter
        print("\nStep 6: Testing fill with 'value' parameter...")
        result_value = await tools.playwright_fill(
            selector="#username", 
            value="test_user",
            page_index=0
        )
        print(f"Result with 'value' parameter: {result_value}")
        
        # Verify results
        success = ("error" not in str(result_text)) and ("error" not in str(result_value))
        if success:
            print("\n✅ TEST PASSED - Both 'text' and 'value' parameters work with playwright_fill")
        else:
            print("\n❌ TEST FAILED - There were errors using the parameters")
        
        return success
    
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        if 'tools' in locals():
            print("\nCleaning up...")
            await tools.cleanup()

if __name__ == "__main__":
    success = asyncio.run(test_fill_parameter_handling())
    sys.exit(0 if success else 1)
