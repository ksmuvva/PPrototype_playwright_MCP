"""
Demonstration of the fix for the 'Illegal return statement' error in Page.evaluate

This script demonstrates:
1. The issue - SyntaxError from an illegal return statement 
2. The fix - Properly wrapping return statements in function expressions
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    # Connect to Playwright
    async with async_playwright() as p:
        # Launch a browser
        browser = await p.chromium.launch()
        
        # Create a new page
        page = await browser.new_page()
        
        # Navigate to a sample page
        await page.goto('https://example.com')
        
        print("\n1. REPRODUCING THE ISSUE:")
        print("Running a script with an illegal return statement")
        
        try:
            # This will fail with "SyntaxError: Illegal return statement"
            result = await page.evaluate('return document.title')
            print(f"Result (should not reach here): {result}")
        except Exception as e:
            print(f"❌ Error as expected: {e}")
        
        print("\n2. APPLYING THE FIX:")
        print("Now wrapping the return statement in a function")
        
        # Function to fix scripts that contain return statements but aren't functions
        def fix_script(script):
            if isinstance(script, str) and "return" in script:
                # Check if the script is already a function expression
                is_function = (
                    script.strip().startswith("() =>") or
                    script.strip().startswith("function") or
                    (script.strip().startswith("(") and "=>" in script)
                )
                
                if not is_function:
                    print(f"⚠️ Script '{script}' contains return but is not a function - wrapping it...")
                    # Wrap the script in a function to make the return statement valid
                    return f"() => {{ {script} }}"
            return script
        
        # Fix the script and try again
        fixed_script = fix_script('return document.title')
        print(f"Fixed script: {fixed_script}")
        
        # Now it should work
        try:
            result = await page.evaluate(fixed_script)
            print(f"✅ Success! Result: {result}")
        except Exception as e:
            print(f"❌ Error (shouldn't happen): {e}")
        
        # Close the browser
        await browser.close()
        
        print("\nCONCLUSION:")
        print("""
The fix for the 'Illegal return statement' error is to ensure that any JavaScript with 
a return statement is properly wrapped in a function expression before passing it to 
page.evaluate(). This can be done by detecting return statements in scripts and automatically 
wrapping them in arrow functions when needed.
        """)

# Run the example
asyncio.run(main())
