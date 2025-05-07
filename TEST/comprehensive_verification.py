#!/usr/bin/env python3
"""
Comprehensive verification of the fix for the PlaywrightTools discovery issue
"""
import os
import sys
import traceback
import importlib.util
import inspect

def check_indentation():
    """Check if the indentation in playwright_function_patches.py is correct"""
    file_path = 'playwright_function_patches.py'
    print(f"\n🔍 CHECKING INDENTATION IN {file_path}")
    print("=" * 60)
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Check line 257 (1-based) and surrounding lines
        target_line = 257 - 1  # Convert to 0-based index
        print(f"Checking line {target_line+1} (if statement) and surrounding context:")
        
        for i in range(max(0, target_line - 4), min(len(lines), target_line + 4)):
            line = lines[i].rstrip()
            indentation = len(line) - len(line.lstrip())
            print(f"Line {i+1:3d}: {' ' * indentation}{line.lstrip()} (indent: {indentation})")
            
            if i == target_line:
                if indentation == 12:
                    print(f"✅ Line {i+1} has correct indentation ({indentation} spaces)")
                    return True
                else:
                    print(f"❌ Line {i+1} has incorrect indentation ({indentation} spaces)")
                    return False
                    
    except Exception as e:
        print(f"❌ Error checking indentation: {e}")
        return False

def test_module_import():
    """Test if the playwright_function_patches module can be imported"""
    print("\n🔍 TESTING MODULE IMPORT")
    print("=" * 60)
    
    try:
        # Try to import the module
        import playwright_function_patches
        print("✅ Successfully imported playwright_function_patches module")
        
        # Check if apply_patches function exists
        if hasattr(playwright_function_patches, 'apply_patches'):
            print("✅ apply_patches function exists in the module")
            return True
        else:
            print("❌ apply_patches function not found in the module")
            return False
            
    except Exception as e:
        print(f"❌ Error importing module: {e}")
        traceback.print_exc()
        return False

def test_tools_discovery():
    """Test if all playwright tools can be discovered"""
    print("\n🔍 TESTING TOOLS DISCOVERY")
    print("=" * 60)
    
    try:
        # Import PlaywrightTools directly
        from exp_tools import PlaywrightTools
        tools = PlaywrightTools()
        
        # Count playwright_* methods
        playwright_methods = [name for name in dir(tools) 
                            if callable(getattr(tools, name)) 
                            and name.startswith('playwright_')]
        
        print(f"Found {len(playwright_methods)} playwright methods in PlaywrightTools")
        
        if len(playwright_methods) > 4:
            print("✅ More than 4 tools discovered - FIX IS WORKING!")
            print(f"First 5 methods: {sorted(playwright_methods)[:5]}")
            return True
        else:
            print(f"❌ Only found {len(playwright_methods)} tools - fix not working")
            print(f"Methods found: {sorted(playwright_methods)}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing tools discovery: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function to run all verification tests"""
    print("\n📋 COMPREHENSIVE VERIFICATION OF PLAYWRIGHT TOOLS DISCOVERY FIX")
    print("=" * 80)
    
    # Step 1: Check indentation
    indentation_ok = check_indentation()
    
    # Step 2: Test module import
    import_ok = test_module_import()
    
    # Step 3: Test tools discovery
    discovery_ok = test_tools_discovery()
    
    # Summary
    print("\n📝 VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"1. Indentation check: {'✅ PASSED' if indentation_ok else '❌ FAILED'}")
    print(f"2. Module import test: {'✅ PASSED' if import_ok else '❌ FAILED'}")
    print(f"3. Tools discovery test: {'✅ PASSED' if discovery_ok else '❌ FAILED'}")
    
    if indentation_ok and import_ok and discovery_ok:
        print("\n✅ ALL TESTS PASSED - FIX HAS BEEN SUCCESSFULLY APPLIED!")
    else:
        print("\n❌ SOME TESTS FAILED - FIX IS NOT FULLY WORKING")

if __name__ == "__main__":
    main()
