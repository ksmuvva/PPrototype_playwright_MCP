#!/usr/bin/env python3
"""
Simple test to verify the playwright tools discovery fix works correctly.
"""
import asyncio
import sys
import traceback
from exp_tools import PlaywrightTools

async def simple_test():
    """Run a simple test to verify the tools discovery fix."""
    print("\n🔍 VERIFICATION OF PLAYWRIGHT TOOLS DISCOVERY FIX")
    print("=" * 60)
    
    print("\nStep 1: Creating PlaywrightTools instance...")
    tools = PlaywrightTools()
    print("✅ PlaywrightTools instance created")
    
    # Check for available playwright_* methods
    print("\nStep 2: Checking available playwright_* methods...")
    methods = [name for name in dir(tools) 
              if callable(getattr(tools, name)) 
              and name.startswith('playwright_')]
    
    print(f"✅ Found {len(methods)} methods starting with 'playwright_'")
    
    # Print the first 10 methods
    print("\nFirst 10 methods:")
    for i, method_name in enumerate(sorted(methods)[:10]):
        print(f"  {i+1}. {method_name}")
    
    # Verify the fix worked
    if len(methods) > 4:
        print(f"\n✅ FIX SUCCESSFUL! Found {len(methods)} methods (more than the original 4)")
    else:
        print(f"\n❌ FIX FAILED - Only found {len(methods)} methods (expected more than 4)")
        
    try:
        print("\nStep 3: Testing function patches import...")
        from playwright_function_patches import apply_patches
        print("✅ Successfully imported apply_patches from playwright_function_patches")
        
        # Try applying patches
        apply_patches(tools)
        print("✅ Successfully applied patches to PlaywrightTools instance")
          # Test a basic function to confirm it works
        print("\nStep 4: Testing basic functions after patches...")
        
        # Initialize the browser if needed
        if not tools.browser_initialized:
            print("Initializing browser...")
            await tools.initialize()
            print("✅ Browser initialized")
        
        # Test navigation 
        print("Testing navigation...")
        nav_result = await tools.playwright_navigate("https://example.com")
        print(f"✅ Navigation test completed: {nav_result.get('status', 'unknown')}")
            capture_screenshot=True
        )
        print(f"Smart click result: {smart_click_result}")
        
        # Check if we're now on the IANA page
        if tools.pages[0]:
            current_url = tools.pages[0].url
            print(f"Current URL after clicking: {current_url}")
            if "iana" in current_url.lower():
                print("✅ SUCCESS! Clicked and navigated to the IANA page")
            else:
                print("❌ FAILURE: Page navigation not as expected")
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up resources...")
        await tools.cleanup()
        print("Test complete!")

if __name__ == "__main__":
    print("=== Testing Fixed playwright_smart_click Function ===")
    try:
        asyncio.run(simple_test())
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    print("=== Test completed ===")
