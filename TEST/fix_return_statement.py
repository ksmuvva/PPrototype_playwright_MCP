#!/usr/bin/env python3
"""
Fixed implementation to handle illegal return statements in the playwright_evaluate function.
This script shows how to fix the issue where JavaScript with return statements fails 
when passed directly to the evaluate method.
"""
import asyncio
from typing import Dict, Any

class ReturnStatementFixer:
    """Demonstration of how to fix return statement issues in evaluate() calls."""
    
    def fix_script(self, script: str) -> str:
        """
        Check if the script contains a return statement and wrap it in a function if needed.
        
        Args:
            script: The JavaScript script to check and potentially modify
            
        Returns:
            The fixed script with proper function wrapping if needed
        """
        if script is None:
            return None
            
        # Trim whitespace for checking
        trimmed_script = script.strip()
        
        # Check if the script is already a function expression (arrow function or regular function)
        is_function = (
            trimmed_script.startswith("() =>") or
            trimmed_script.startswith("function") or
            (trimmed_script.startswith("(") and "=>" in trimmed_script)
        )
        
        # If it's not a function but contains a return statement, wrap it
        if not is_function and "return" in trimmed_script:
            print("⚠️ Script contains return statement but is not a function, wrapping it...")
            # Wrap the script in an arrow function to make the return statement valid
            fixed_script = f"() => {{ {script} }}"
            print(f"✅ Fixed script: {fixed_script}")
            return fixed_script
            
        # Script is already a function or doesn't need wrapping
        return script


async def test_return_statement_fix():
    """Test the return statement fix with various script scenarios."""
    fixer = ReturnStatementFixer()
    
    # Test cases
    scripts = [
        # Script with illegal return statement
        "return document.title",
        
        # Already wrapped function (arrow function)
        "() => { return document.title }",
        
        # Already wrapped function (traditional)
        "function() { return document.title }",
        
        # No return statement
        "document.querySelector('h1').textContent",
        
        # Multi-line script with return
        """
        const elements = document.querySelectorAll('a');
        const hrefs = Array.from(elements).map(el => el.href);
        return hrefs;
        """
    ]
    
    for i, script in enumerate(scripts):
        print(f"\nTest case {i+1}:")
        print(f"Original: {script}")
        
        fixed = fixer.fix_script(script)
        if fixed != script:
            print(f"Fixed:    {fixed}")
        else:
            print("No fix needed")
    
    print("\nAll test cases processed!")


if __name__ == "__main__":
    print("\n=== Testing Return Statement Fix for playwright_evaluate ===\n")
    asyncio.run(test_return_statement_fix())
    print("\n=== Test Complete ===")
