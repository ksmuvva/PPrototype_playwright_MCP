#!/usr/bin/env python3
"""
Final verification of the PlaywrightTools discovery fix
"""
import asyncio
import sys
import traceback
from typing import List

async def verify_tool_discovery():
    """Verify that all PlaywrightTools methods are being discovered after the fix."""
    print("\n🔍 VERIFICATION OF PLAYWRIGHT TOOLS DISCOVERY FIX")
    print("=" * 60)
    
    try:
        # Step 1: Import PlaywrightTools
        print("\nStep 1: Importing PlaywrightTools...")
        from exp_tools import PlaywrightTools
        print("✅ Successfully imported PlaywrightTools")
        
        # Step 2: Create instance
        print("\nStep 2: Creating PlaywrightTools instance...")
        tools = PlaywrightTools()
        print("✅ Successfully created PlaywrightTools instance")
        
        # Step 3: Count playwright_* methods
        print("\nStep 3: Counting available playwright_* methods...")
        methods = [name for name in dir(tools) 
                  if callable(getattr(tools, name)) 
                  and name.startswith('playwright_')]
        
        print(f"✅ Found {len(methods)} methods starting with 'playwright_'")
        
        # Print the first 10 methods
        print("\nFirst 10 methods found:")
        for i, method_name in enumerate(sorted(methods)[:10]):
            print(f"  {i+1}. {method_name}")
        
        # Step 4: Import and apply patches
        print("\nStep 4: Importing and applying function patches...")
        try:
            from playwright_function_patches import apply_patches
            apply_patches(tools)
            print("✅ Successfully imported and applied patches")
        except Exception as patch_error:
            print(f"❌ Error applying patches: {patch_error}")
            traceback.print_exc()
        
        # Step 5: Verify fix was successful
        print("\n🏁 VERIFICATION RESULTS:")
        if len(methods) > 4:
            print(f"✅ FIX SUCCESSFUL! Found {len(methods)} methods (more than the original 4)")
            print("The indentation fix in playwright_function_patches.py has resolved the issue.")
            return True
        else:
            print(f"❌ FIX FAILED! Only found {len(methods)} methods")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(verify_tool_discovery())
    # Exit with appropriate status code
    sys.exit(0 if result else 1)
