"""
Updated implementation of the playwright_smart_click function.

This implementation properly handles both text and selector parameters.
"""

async def playwright_smart_click(self, text=None, selector=None, element_type: str = 'any', page_index: int = 0,
                               capture_screenshot: bool = False, max_attempts: int = 3) -> dict:
    """
    Smart click that tries multiple selector strategies based on fuzzy text matching.
    Especially useful for common UI patterns with varied terminology.
    
    Args:
        text: The text to look for (e.g., "Place Order", "Continue", "Submit")
        selector: Alternative to text - CSS selector to click (for compatibility with LLM output)
        element_type: Type of element to target ('button', 'link', 'any')
        page_index: Index of the page to operate on
        capture_screenshot: Whether to capture a screenshot after clicking
        max_attempts: Maximum number of attempts to try different strategies
    """
    # Handle cases where selector is provided instead of text (for compatibility with LLM output)
    original_selector = selector
    if selector is not None and text is None:
        # Try to extract text from the selector
        import re
        
        # Common patterns for selector with text
        has_text_match = re.search(r":has-text\('([^']+)'\)", selector)
        if has_text_match:
            text = has_text_match.group(1)
            print(f"Extracted text '{text}' from selector '{selector}'")
        elif ":text(" in selector:
            text_match = re.search(r":text\(['\"]([^'\"]+)['\"]\)", selector)
            if text_match:
                text = text_match.group(1)
                print(f"Extracted text '{text}' from selector '{selector}'")
        elif "aria-label" in selector:
            label_match = re.search(r"\[aria-label=['\"]([^'\"]+)['\"]\]", selector)
            if label_match:
                text = label_match.group(1)
                print(f"Extracted text '{text}' from selector '{selector}'")
        else:
            # If we couldn't extract text, use the selector as the text
            text = selector
            print(f"Using selector '{selector}' as text")
    
    # Ensure we have text to click
    if text is None:
        return {"status": "error", "message": "Either text or selector must be provided"}
        
    # Track where we are in the recovery process
    attempt_count = 0
    last_error = None
    debug_screenshots = []
    page = None
    
    while attempt_count < max_attempts:
        attempt_count += 1
        print(f"Smart click attempt {attempt_count}/{max_attempts} for text: '{text}'")
        
        try:
            # Ensure browser is initialized
            if not self.browser_initialized:
                print(f"Browser not initialized before smart_click, initializing now...")
                await self._ensure_browser_initialized()
                print(f"Browser initialized successfully for smart_click")
            
            # Get the page
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            # Extra validation for the page object
            if page.is_closed():
                print("Page is closed, creating a new page...")
                page = await self.context.new_page()
                self.pages[page_index] = page
                print(f"Created new page at index {page_index}")
            
            print(f"Smart click looking for element with text: {text}")
            
            # Create variations of the text for fuzzy matching
            text_variations = [
                text,
                text.lower(),
                text.upper(),
                text.title(),
            ]
            
            # Generate selectors based on element type
            selectors = []
            
            # Start with original selector if provided
            if original_selector is not None:
                selectors.append(original_selector)
                
            if element_type == "button" or element_type == "any":
                # Button selectors
                for variation in text_variations:
                    selectors.extend([
                        f"button:has-text('{variation}')",
                        f"button[value='{variation}']",
                        f"input[type='submit'][value='{variation}']",
                        f"[role='button']:has-text('{variation}')",
                    ])
            
            if element_type == "link" or element_type == "any":
                # Link selectors
                for variation in text_variations:
                    selectors.extend([
                        f"a:has-text('{variation}')",
                        f"[role='link']:has-text('{variation}')"
                    ])
            
            if element_type == "any":
                # General selectors for any clickable element
                for variation in text_variations:
                    selectors.extend([
                        f":has-text('{variation}'):visible",
                        f"[aria-label='{variation}']",
                        f"[title='{variation}']",
                    ])
                    
            # Try each selector
            for idx, selector in enumerate(selectors):
                try:
                    if await page.is_visible(selector, timeout=1000):
                        print(f"Smart click found element with selector: {selector}")
                        await page.click(selector)
                        
                        result = {
                            "status": "success",
                            "message": f"Smart click succeeded with selector: {selector}",
                            "matched_text": text,
                            "selector_used": selector
                        }
                        
                        if capture_screenshot:
                            import os
                            import asyncio
                            
                            # Ensure screenshot directory exists
                            if hasattr(self, "screenshot_dir"):
                                os.makedirs(self.screenshot_dir, exist_ok=True)
                                screenshot_path = os.path.join(self.screenshot_dir, 
                                                              f"smart_click_{int(asyncio.get_event_loop().time())}.png")
                            else:
                                screenshot_path = f"smart_click_{int(asyncio.get_event_loop().time())}.png"
                                
                            await page.screenshot(path=screenshot_path)
                            result["screenshot"] = screenshot_path
                            print(f"Screenshot saved to: {screenshot_path}")
                            
                        return result
                except Exception as selector_error:
                    # Continue to next selector if this one fails
                    continue
            
            # If we reached this point and haven't returned, none of the selectors worked
            if attempt_count == max_attempts:
                error_result = {
                    "status": "error", 
                    "message": f"Smart click failed: Could not find clickable element matching '{text}'",
                    "tried_selectors": selectors[:5]  # Return first few selectors tried (limit result size)
                }
                
                # Take a screenshot of the failure state for debugging
                if capture_screenshot:
                    try:
                        import os
                        import asyncio
                        
                        failure_screenshot = f"smart_click_failure_{int(asyncio.get_event_loop().time())}.png"
                        
                        if hasattr(self, "screenshot_dir"):
                            failure_screenshot_path = os.path.join(self.screenshot_dir, failure_screenshot)
                        else:
                            failure_screenshot_path = failure_screenshot
                            
                        await page.screenshot(path=failure_screenshot_path)
                        error_result["failure_screenshot"] = failure_screenshot
                        print(f"Failure screenshot saved to: {failure_screenshot}")
                    except Exception:
                        pass
                    
                return error_result
        
        except Exception as e:
            print(f"Error in playwright_smart_click attempt {attempt_count}: {str(e)}")
            last_error = e
            
            # If this is the last attempt, return an error
            if attempt_count == max_attempts:
                error_info = {
                    "status": "error", 
                    "message": f"Smart click failed after {max_attempts} attempts: {str(e)}",
                    "tried_text": text,
                    "tried_element_type": element_type
                }
                
                # Try to include page info and screenshot for debugging
                if page and not page.is_closed():
                    try:
                        error_info["page_url"] = page.url
                        error_info["page_title"] = await page.title()
                        
                        if capture_screenshot:
                            import os
                            import asyncio
                            
                            error_screenshot = f"smart_click_error_{int(asyncio.get_event_loop().time())}.png"
                            
                            if hasattr(self, "screenshot_dir"):
                                error_screenshot_path = os.path.join(self.screenshot_dir, error_screenshot)
                            else:
                                error_screenshot_path = error_screenshot
                                
                            await page.screenshot(path=error_screenshot_path)
                            error_info["error_screenshot"] = error_screenshot
                            print(f"Error screenshot saved to: {error_screenshot}")
                    except Exception as ss_err:
                        print(f"Could not capture error screenshot: {ss_err}")
                
                return error_info
