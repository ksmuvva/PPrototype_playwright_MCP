#!/usr/bin/env python3
"""
Quick verification of fixed tool discovery in the PlaywrightTools class
"""
import os
import sys
from pprint import pprint

print("\n🔍 Checking PlaywrightTools Tool Discovery After Fix")
print("================================================")

try:
    # Import the tools
    from exp_tools import PlaywrightTools
    print("✅ Successfully imported PlaywrightTools from exp_tools.py")
    
    # Create an instance
    tools = PlaywrightTools()
    print("✅ Successfully created PlaywrightTools instance")
    
    # Find all tools directly
    playwright_methods = [name for name in dir(tools) 
                        if callable(getattr(tools, name)) 
                        and name.startswith('playwright_')]
    
    print(f"\nFound {len(playwright_methods)} playwright methods in total")
    print("\nFirst 10 methods:")
    for i, method in enumerate(sorted(playwright_methods)[:10]):
        print(f"  {i+1}. {method}")
    
    # Check if our fix solved the problem
    print("\n✅ Fix verification complete!")
    if len(playwright_methods) > 4:
        print(f"SUCCESS: Found {len(playwright_methods)} methods (more than the original 4)")
    else:
        print(f"FAILED: Still only found {len(playwright_methods)} methods")
    
except Exception as e:
    print(f"❌ Error: {e}")
