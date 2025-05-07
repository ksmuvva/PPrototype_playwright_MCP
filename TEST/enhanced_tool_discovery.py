#!/usr/bin/env python3
"""
Enhanced PlaywrightTools Discovery Script

This script demonstrates how to properly discover and use all tools available in the 
PlaywrightTools class from exp_tools.py.

Usage:
    python enhanced_tool_discovery.py
"""
import asyncio
import os
import inspect
from typing import Dict, Any, List

# Import the Playwright tools
from exp_tools import PlaywrightTools

def print_highlighted(message):
    """Print a highlighted message."""
    print("\n" + "="*80)
    print(f"{message}")
    print("="*80)

async def main():
    """Main entry point."""
    print_highlighted("🚀 Enhanced Playwright Tools Discovery")
    
    # 1. Create an instance of PlaywrightTools
    tools = PlaywrightTools()
    
    # 2. Initialize the tools
    print("\nInitializing Playwright Tools...")
    try:
        await tools.initialize()
        print("✅ Successfully initialized PlaywrightTools")
    except Exception as e:
        print(f"❌ Failed to initialize PlaywrightTools: {e}")
        return
    
    # 3. Discover all available tools with playwright_ prefix
    print("\nDiscovering all available playwright_ tools:")
    playwright_methods = [name for name in dir(tools) 
                         if callable(getattr(tools, name)) 
                         and name.startswith('playwright_')]
    
    print(f"Found {len(playwright_methods)} methods:")
    for i, method_name in enumerate(sorted(playwright_methods)):
        method = getattr(tools, method_name)
        doc = method.__doc__
        description = doc.strip().split("\n")[0] if doc else "No description available"
        print(f"{i+1}. {method_name} - {description}")
    
    # 4. Show how to fix the tool discovery in PlaywrightMCPServer._create_tools
    print_highlighted("How to fix the tool discovery issue in expiremental-new.py")
    
    print("""
To fix the tool discovery issue in PlaywrightMCPServer._create_tools method:

1. Change this line:
   tool_methods = [name for name in dir(self.tools_instance) 
                  if callable(getattr(self.tools_instance, name)) 
                  and not name.startswith('_')]

   To this:
   tool_methods = [name for name in dir(self.tools_instance) 
                  if callable(getattr(self.tools_instance, name)) 
                  and name.startswith('playwright_')]

2. Remove this check inside the loop:
   if method_name.startswith("playwright_"):
   
   Since we're already filtering for playwright_ methods in the list comprehension.

This fix ensures that:
- We're directly looking for methods that start with 'playwright_' instead of just filtering out those with '_'
- We'll find all available tools in the PlaywrightTools class
- The output will show all available tools, not just a subset

You can apply this fix by editing the `expiremental-new.py` file.
""")
    
    print_highlighted("Test Connection Example")
    print("\nExample of using discovered tools:")
    
    try:
        # Attempt a navigation as an example
        print("\nAttempting to navigate to example.com...")
        result = await tools.playwright_navigate("https://example.com")
        print(f"Navigation result: {result}")
        
        # Take a screenshot as an example
        print("\nTaking a screenshot...")
        screenshot_result = await tools.playwright_screenshot("example.png")
        print(f"Screenshot result: {screenshot_result}")
    except Exception as e:
        print(f"Error during test: {e}")
    
    # Cleanup
    print("\nCleaning up...")
    await tools.cleanup()
    print("✅ Resources cleaned up")
    
    print_highlighted("Script Complete")

if __name__ == "__main__":
    asyncio.run(main())
