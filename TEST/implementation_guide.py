"""
Implementation Guide for Parameter Mismatch Fixes

This script demonstrates how to implement the fixes for parameter mismatches in 
playwright_smart_click and playwright_screenshot functions.

There are three ways to apply these fixes:

1. Quick Fix: Add this code directly to expiremental-new.py where tools are initialized
2. Clean Implementation: Use the param_adapter.py module for a modular approach
3. Direct Fix: Update the function implementations directly

Choose the approach that best fits your project structure and requirements.
"""
import asyncio
import os
import sys
from typing import Dict, Any

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# -----------------------------------------------------------------------------
# OPTION 1: Quick Fix (Inline Implementation)
# -----------------------------------------------------------------------------

def apply_quick_fix(tools_instance):
    """
    Apply quick fixes directly to the tools instance.
    """
    print("Applying quick fixes...")
    
    # Store original methods
    original_smart_click = tools_instance.playwright_smart_click
    original_screenshot = tools_instance.playwright_screenshot
    
    # Create adapter for playwright_smart_click
    async def fixed_smart_click(text=None, selector=None, **kwargs):
        # Handle selector parameter
        if selector is not None and text is None:
            # Extract text from common selector patterns
            import re
            extracted_text = None
            
            # Common patterns: :has-text('Text'), :text("Text"), [aria-label="Text"]
            has_text_match = re.search(r":has-text\('([^']+)'\)", selector)
            if has_text_match:
                extracted_text = has_text_match.group(1)
            elif ":text(" in selector:
                text_match = re.search(r":text\(['\"]([^'\"]+)['\"]\)", selector)
                if text_match:
                    extracted_text = text_match.group(1)
            elif "aria-label" in selector:
                label_match = re.search(r"\[aria-label=['\"]([^'\"]+)['\"]\]", selector)
                if label_match:
                    extracted_text = label_match.group(1)
            
            # Use extracted text or the selector itself
            if extracted_text:
                text = extracted_text
                print(f"Extracted text '{text}' from selector '{selector}'")
            else:
                text = selector
                print(f"Using selector '{selector}' as text")
        
        # Call original method with fixed parameters
        return await original_smart_click(text=text, **kwargs)
    
    # Create adapter for playwright_screenshot
    async def fixed_screenshot(filename=None, **kwargs):
        # Generate default filename if not provided
        if filename is None:
            import time
            filename = f"screenshot_{int(time.time())}.png"
            print(f"No filename provided, using default: {filename}")
        
        # Ensure filename has .png extension
        if not filename.endswith('.png'):
            filename += '.png'
        
        # Call original method
        return await original_screenshot(filename=filename, **kwargs)
    
    # Replace methods with fixed versions
    tools_instance.playwright_smart_click = fixed_smart_click
    tools_instance.playwright_screenshot = fixed_screenshot
    
    print("✅ Quick fixes applied successfully")

# -----------------------------------------------------------------------------
# OPTION 2: Clean Implementation (Using param_adapter.py)
# -----------------------------------------------------------------------------

def apply_clean_implementation(tools_instance):
    """
    Apply clean implementation using the param_adapter module.
    """
    try:
        from param_adapter import apply_adapters
        apply_adapters(tools_instance)
        print("✅ Parameter adapters applied from param_adapter.py")
    except ImportError:
        print("❌ param_adapter.py not found, skipping clean implementation")

# -----------------------------------------------------------------------------
# OPTION 3: Direct Fix (Update Function Implementations)
# -----------------------------------------------------------------------------

def apply_direct_fix():
    """
    Instructions for directly fixing the function implementations.
    """
    print("To directly fix the function implementations:")
    print("\n1. For playwright_smart_click in exp_tools.py:")
    print("   - Ensure the function handles both text and selector parameters")
    print("   - Extract text from selector patterns when text is not provided")
    print("   - Avoid returning error when parameters are properly adapted")
    
    print("\n2. For playwright_screenshot in exp_tools.py:")
    print("   - Ensure the filename parameter has a default value")
    print("   - Generate a timestamp-based filename when none is provided")
    print("   - Make sure the filename ends with .png")

# -----------------------------------------------------------------------------
# Usage Example
# -----------------------------------------------------------------------------

async def main():
    """
    Example usage of the parameter mismatch fixes.
    """
    print("=== Parameter Mismatch Fixes Usage Example ===")
    
    # Try to import the real PlaywrightTools
    try:
        from exp_tools import PlaywrightTools
        tools = PlaywrightTools()
        await tools.initialize()
        
        # Choose one of the implementation approaches
        apply_quick_fix(tools)
        # OR
        # apply_clean_implementation(tools)
        
        print("\nTesting the fixes...")
        
        # Test playwright_smart_click with selector parameter
        result1 = await tools.playwright_smart_click(selector="a:has-text('More information')")
        print(f"Smart click with selector result: {result1.get('status', 'unknown')}")
        
        # Test playwright_screenshot without filename
        result2 = await tools.playwright_screenshot()
        print(f"Screenshot without filename result: {result2.get('status', 'unknown')}")
        
        await tools.cleanup()
        
    except ImportError:
        print("Real PlaywrightTools not available, showing direct fix instructions")
        apply_direct_fix()
    
    print("\n=== Implementation Guide Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
