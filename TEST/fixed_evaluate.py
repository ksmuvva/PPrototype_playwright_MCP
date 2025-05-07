"""
Fixed version of playwright_evaluate to solve the 'Illegal return statement' error
This will be included in the main playwright_function_patches.py file
"""

async def fixed_evaluate(self, script: str = None, page_index: int = 0, pageFunction: str = None, **kwargs) -> Dict[str, Any]:
    """
    Fixed version of playwright_evaluate that handles both script and pageFunction parameters,
    and properly wraps standalone return statements in functions to avoid SyntaxError.
    
    Args:
        script: JavaScript code to evaluate (our API format)
        pageFunction: JavaScript code to evaluate (Playwright API format)
        page_index: Index of the page to operate on
        **kwargs: Additional parameters
    """
    try:
        print(f"fixed_evaluate called with script={script}, pageFunction={pageFunction}")
        
        # Enhanced parameter adaptation with detailed logging
        actual_script = script or pageFunction
        param_source = "script" if script is not None else "pageFunction" if pageFunction is not None else "none"
        
        if actual_script is None:
            print("❌ Error: Neither 'script' nor 'pageFunction' parameter provided")
            return {
                "status": "error",
                "message": "Either 'script' or 'pageFunction' parameter must be provided"
            }
        
        print(f"✅ Using parameter from source: '{param_source}'")
        
        # Process script content to ensure it's a valid function for evaluation
        if isinstance(actual_script, str):
            # Check if the script is already a function expression (arrow function or regular function)
            is_function = (
                actual_script.strip().startswith("() =>") or
                actual_script.strip().startswith("function") or
                (actual_script.strip().startswith("(") and "=>" in actual_script)
            )
            
            if not is_function and "return" in actual_script:
                print("⚠️ Script contains return statement but is not a function, wrapping it...")
                # Wrap the script in a function to make the return statement valid
                actual_script = f"() => {{ {actual_script} }}"
                print(f"✅ Fixed script: {actual_script}")
            elif is_function:
                print("✅ Script is already a function expression")
        
        # Get the page
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            print(f"🔄 Evaluating script: {actual_script[:100]}...")
            result = await page.evaluate(actual_script)
            print(f"✅ Evaluation succeeded with result: {str(result)[:100]}...")
            
            return {
                "status": "success",
                "result": result,
                "fixed": True
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Evaluation failed: {error_msg}")
            
            # If still getting syntax error, try different approaches
            if "SyntaxError" in error_msg and "return" in error_msg:
                print("🔄 Further fixing attempts for return statement...")
                try:
                    # Add an explicit return if not present
                    if "return" not in actual_script and not is_function:
                        wrapped_script = f"() => {{ return {actual_script}; }}"
                        print(f"🔄 Trying with explicit return: {wrapped_script}")
                        result = await page.evaluate(wrapped_script)
                        return {
                            "status": "success",
                            "result": result,
                            "fixed": True
                        }
                except Exception as retry_e:
                    print(f"❌ Additional fix attempts failed: {str(retry_e)}")
            
            # Return error status
            return {"status": "error", "message": error_msg}
            
    except Exception as e:
        print(f"❌ Exception in fixed_evaluate: {str(e)}")
        return {"status": "error", "message": str(e)}
