    async def playwright_smart_click(self, text: str, element_type: str = "any", page_index: int = 0,
                                   capture_screenshot: bool = False, max_attempts: int = 3) -> Dict[str, Any]:
        """
        Smart click that tries multiple selector strategies based on fuzzy text matching.
        Especially useful for common UI patterns with varied terminology.
        
        Args:
            text: The text to look for (e.g., "Place Order", "Continue", "Submit")
            element_type: Type of element to target ('button', 'link', 'any')
            page_index: Index of the page to operate on
            capture_screenshot: Whether to capture a screenshot after clicking
            max_attempts: Maximum number of attempts to try different strategies
        """
        # Track where we are in the recovery process
        attempt_count = 0
        last_error = None
        debug_screenshots = []
        page = None
        
        while attempt_count < max_attempts:
            attempt_count += 1
            print(f"Smart click attempt {attempt_count}/{max_attempts} for text: '{text}'")
            
            # Ensure browser is initialized
            if not self.browser_initialized:
                print(f"Browser not initialized before smart_click, initializing now...")
                try:
                    await self._ensure_browser_initialized()
                    print(f"Browser initialized successfully for smart_click")
                except Exception as init_err:
                    print(f"Failed to initialize browser for smart_click: {init_err}")
                    if attempt_count == max_attempts:
                        return {
                            "status": "error",
                            "message": f"Browser initialization failed after {max_attempts} attempts: {str(init_err)}",
                            "error_type": "initialization_error",
                            "debug_screenshots": debug_screenshots
                        }
                    else:
                        # Wait a bit and retry browser initialization
                        await asyncio.sleep(1)
                        continue
            
            # Get page with additional error information and validation
            try:
                page = await self._get_page(page_index)
                if not page:
                    if attempt_count == max_attempts:
                        return {"status": "error", "message": "Invalid page index", "debug_screenshots": debug_screenshots}
                    else:
                        await asyncio.sleep(1)
                        continue
                
                # Extra validation for the page object
                if page.is_closed():
                    print("Page is closed, creating a new page...")
                    try:
                        page = await self.context.new_page()
                        self.pages[page_index] = page
                        print(f"Created new page at index {page_index}")
                        
                        # Take debug screenshot of the new page
                        debug_path = f"smart_click_debug_newpage_{int(time.time())}.png"
                        await page.goto("about:blank")
                        await page.screenshot(path=self._get_screenshot_path(debug_path))
                        debug_screenshots.append(debug_path)
                        print(f"Debug screenshot of new page saved to: {debug_path}")
                    except Exception as ss_err:
                        print(f"Error taking debug screenshot: {ss_err}")
                
                # Take a debug screenshot before attempting click
                debug_path = f"smart_click_before_{int(time.time())}.png"
                try:
                    await page.screenshot(path=self._get_screenshot_path(debug_path))
                    debug_screenshots.append(debug_path)
                    print(f"Pre-click screenshot saved to: {debug_path}")
                except Exception as ss_err:
                    print(f"Error taking pre-click screenshot: {ss_err}")
                    
            except Exception as page_err:
                print(f"Error accessing or creating page for smart_click: {page_err}")
                last_error = page_err
                
                if attempt_count == max_attempts:
                    return {
                        "status": "error", 
                        "message": f"Error with page after {max_attempts} attempts: {str(page_err)}",
                        "error_type": "page_error",
                        "debug_screenshots": debug_screenshots
                    }
                else:
                    # For recovery, try to create a completely new browser session
                    if attempt_count == max_attempts - 1:
                        print("Attempting full browser reset as last resort...")
                        try:
                            # Close everything and start fresh
                            if self.browser:
                                await self.browser.close()
                            if self.playwright:
                                await self.playwright.stop()
                            
                            # Reinitialize playwright
                            self.playwright = await async_playwright().start()
                            self.browser = await self.playwright.chromium.launch(headless=False)
                            self.context = await self.browser.new_context(
                                viewport={"width": 1425, "height": 776}
                            )
                            self.browser_initialized = True
                            
                            # Create a new page
                            page = await self.context.new_page()
                            self.pages = [page]
                            
                            print("Browser reset successful, retrying operation...")
                        except Exception as reset_err:
                            print(f"Browser reset failed: {reset_err}")
                    
                    await asyncio.sleep(1)
                    continue
            
            # If we got to this point, we have a valid page object
            try:
                # Create variations of the text for fuzzy matching
                text_variations = [
                    text,
                    text.lower(),
                    text.upper(),
                    text.title(),
                    # Common variations for buttons
                    f"Submit {text}",
                    f"Confirm {text}",
                    f"Place {text}",
                    f"Complete {text}",
                    # Common action variations
                    "Submit",
                    "Continue",
                    "Proceed",
                    "Next",
                    "Confirm",
                    "OK",
                    "Checkout",
                    "Place Order"
                ]
                
                # Generate selectors based on element type
                selectors = []
                
                if element_type == "button" or element_type == "any":
                    # Button selectors
                    for variation in text_variations:
                        selectors.extend([
                            f"button:has-text('{variation}')",
                            f"button:text-is('{variation}')",
                            f"button[value='{variation}']",
                            f"input[type='submit'][value='{variation}']",
                            f"[role='button']:has-text('{variation}')",
                            f".btn:has-text('{variation}')",
                            f".button:has-text('{variation}')"
                        ])
                
                if element_type == "link" or element_type == "any":
                    # Link selectors
                    for variation in text_variations:
                        selectors.extend([
                            f"a:has-text('{variation}')",
                            f"a:text-is('{variation}')",
                            f"[role='link']:has-text('{variation}')"
                        ])
                
                if element_type == "any":
                    # General selectors for any clickable element
                    for variation in text_variations:
                        selectors.extend([
                            f":has-text('{variation}'):visible",
                            f"[aria-label='{variation}']",
                            f"[title='{variation}']",
                            f"[name='{variation}']",
                            f"[data-test='{variation}']"
                        ])
                
                # Try each selector until one works
                for selector in selectors:
                    try:
                        # Check if element exists and is visible
                        is_visible = await page.is_visible(selector, timeout=1000)
                        if is_visible:
                            print(f"Smart click found element with selector: {selector}")
                            await page.click(selector)
                            
                            result = {
                                "status": "success",
                                "message": f"Smart click succeeded with selector: {selector}",
                                "matched_text": text,
                                "selector_used": selector
                            }
                            
                            if capture_screenshot:
                                screenshot_path = self._get_screenshot_path(f"smart_click_{asyncio.get_event_loop().time()}.png")
                                await page.screenshot(path=screenshot_path)
                                result["screenshot"] = screenshot_path
                                print(f"Screenshot saved to: {screenshot_path}")
                                
                            return result
                    except Exception:
                        # Continue to next selector if this one fails
                        continue
                
                # If we get here, none of the selectors worked
                error_result = {
                    "status": "error", 
                    "message": f"Smart click failed: Could not find clickable element matching '{text}'",
                    "tried_selectors": selectors[:5]  # Return first few selectors tried (limit result size)
                }
                
                # Take a screenshot of the failure state for debugging
                try:
                    failure_screenshot = f"smart_click_failure_{asyncio.get_event_loop().time()}.png"
                    await page.screenshot(path=self._get_screenshot_path(failure_screenshot))
                    error_result["failure_screenshot"] = failure_screenshot
                    print(f"Failure screenshot saved to: {failure_screenshot}")
                except Exception:
                    pass
                    
                return error_result
                
            except Exception as e:
                print(f"Smart click failed with error: {str(e)}")
                # Add more detailed debugging information
                error_info = {
                    "status": "error", 
                    "message": str(e),
                    "tried_text": text,
                    "tried_element_type": element_type
                }
                
                # Try to get page information for debugging
                try:
                    if page:
                        error_info["page_url"] = page.url
                        error_info["page_title"] = await page.title()
                        # Take a screenshot on failure for debugging
                        failure_screenshot = f"smart_click_error_{asyncio.get_event_loop().time()}.png"
                        await page.screenshot(path=self._get_screenshot_path(failure_screenshot))
                        error_info["failure_screenshot"] = failure_screenshot
                        print(f"Error screenshot saved to: {failure_screenshot}")
                except Exception:
                    pass
                    
                return error_info
