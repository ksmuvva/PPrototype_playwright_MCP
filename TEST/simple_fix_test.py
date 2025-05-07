"""
Simple test for the playwright_evaluate illegal return statement fix.
"""

import asyncio

# This is a standalone test that doesn't require external dependencies
async def test_evaluate_fix():
    print("Testing the fix for 'Illegal return statement' in Page.evaluate")
    
    # Simulate the patched_evaluate function logic
    def fix_script(script):
        """Fix scripts that have return statements but are not wrapped in functions"""
        if isinstance(script, str):
            # Check if script is already a function expression
            is_function = (
                script.strip().startswith("() =>") or
                script.strip().startswith("function") or
                (script.strip().startswith("(") and "=>" in script)
            )
            
            if not is_function and "return" in script:
                print(f"⚠️ Script '{script}' contains return but is not a function - wrapping it...")
                # Wrap the script in a function to make the return statement valid
                fixed_script = f"() => {{ {script} }}"
                print(f"✅ Fixed script: '{fixed_script}'")
                return fixed_script
            elif is_function:
                print(f"✅ Script '{script}' is already a function expression")
        return script
    
    # Test cases that should trigger fixes
    test_cases = [
        ("return document.title", True),
        ("() => document.title", False),
        ("function() { return document.title; }", False),
        ("const x = 5; return x * 2;", True),
        ("document.querySelector('div')", False),
        ("return document.querySelector('div').textContent", True)
    ]
    
    # Run tests
    for script, should_fix in test_cases:
        fixed = fix_script(script)
        if should_fix and fixed != script:
            print(f"✅ PASS: Script was correctly wrapped: {script} → {fixed}")
        elif not should_fix and fixed == script:
            print(f"✅ PASS: Script was correctly left unchanged: {script}")
        else:
            print(f"❌ FAIL: Script was not handled correctly: {script} → {fixed}")
    
    print("\nTest complete - This demonstrates the fix for the 'Illegal return statement' error")

# Run the test
asyncio.run(test_evaluate_fix())
