#!/usr/bin/env python3
"""
Debug script to check imports and tool availability
"""
import sys
import traceback

print("Python version:", sys.version)

try:
    # Try importing the PlaywrightTools class
    from exp_tools import PlaywrightTools
    print("✅ Successfully imported PlaywrightTools from exp_tools")
    
    # Create an instance
    tools = PlaywrightTools()
    print("✅ Successfully created PlaywrightTools instance")
    
    # List available playwright methods
    playwright_methods = [m for m in dir(tools) if callable(getattr(tools, m)) and m.startswith('playwright_')]
    print(f"Found {len(playwright_methods)} playwright methods:")
    for method in sorted(playwright_methods):
        print(f"  - {method}")
    
    # Check if initialize method works
    import asyncio
    print("\nTrying to initialize PlaywrightTools...")
    
    async def test_init():
        success = await tools.initialize()
        if success:
            print("✅ Successfully initialized PlaywrightTools")
        else:
            print("❌ Failed to initialize PlaywrightTools")
    
    asyncio.run(test_init())
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
