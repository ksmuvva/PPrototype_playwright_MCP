#!/usr/bin/env python3
"""
Testing fix for PlaywrightTools discovery
This script verifies that the indentation fix in playwright_function_patches.py
has resolved the issue with tool discovery in expiremental-new.py
"""

import os
import sys
import inspect

print("\n🔍 VERIFYING PLAYWRIGHT TOOLS FIX")
print("=" * 50)

def count_methods():
    """Count the number of playwright_ methods available."""
    # Try importing the PlaywrightTools class
    try:
        from exp_tools import PlaywrightTools
        print("✅ Successfully imported PlaywrightTools from exp_tools")
        
        # Create an instance and count methods
        tools = PlaywrightTools()
        playwright_methods = [name for name in dir(tools) 
                             if name.startswith('playwright_') and callable(getattr(tools, name))]
        
        print(f"Found {len(playwright_methods)} callable 'playwright_' methods")
        
        # Print first few methods as evidence
        if len(playwright_methods) > 0:
            print("\nSample of available methods:")
            for i, method in enumerate(sorted(playwright_methods)[:7]):
                doc = getattr(tools, method).__doc__
                short_desc = doc.strip().split('\n')[0] if doc else "No description"
                print(f"  {i+1}. {method} - {short_desc}")
        
        # Check if the patch module can be imported
        try:
            from playwright_function_patches import apply_patches
            print("\n✅ Successfully imported apply_patches from playwright_function_patches")
            # The indentation fix worked!
        except Exception as patch_error:
            print(f"\n❌ Error importing apply_patches: {patch_error}")
            print("The indentation fix did not resolve the import issue")
        
        # Check if fix worked
        if len(playwright_methods) > 4:
            print("\n✅ FIX SUCCESSFUL - Found more than 4 tools!")
            print(f"The fix has resolved the tool discovery issue. {len(playwright_methods)} tools available.")
            return len(playwright_methods)
        else:
            print("\n❌ FIX FAILED - Still only found {len(playwright_methods)} tools")
            print("The fix did not resolve the tool discovery issue")
            return len(playwright_methods)
            
    except Exception as e:
        print(f"\n❌ Error importing PlaywrightTools: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    num_tools = count_methods()
    print("\n📋 SUMMARY")
    print("=" * 50)
    print(f"Total playwright tools available: {num_tools}")
    if num_tools > 4:
        print("✅ FIX VERIFIED: The indentation fix has successfully resolved the tool discovery issue!")
        sys.exit(0)
    else:
        print("❌ FIX FAILED: The tool discovery issue persists")
        sys.exit(1)
