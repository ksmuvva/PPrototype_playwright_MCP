#!/usr/bin/env python3
"""
MCP Tools - Collection of browser automation tools for the MCP protocol
Includes code generation and browser automation tools used by the MCP agent.
"""
import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, CDPSession, TimeoutError as PlaywrightTimeoutError

# Configure logging
logger = logging.getLogger("mcp_tools")

class CodeGenSession:
    """Represents a code generation session."""
    def __init__(self, session_id: str, name: str, language: str):
        self.session_id = session_id
        self.name = name
        self.language = language
        self.code = ""
        self.created_at = asyncio.get_event_loop().time()
        self.updated_at = self.created_at
    
    def update(self, code: str):
        """Update the code in the session."""
        self.code = code
        self.updated_at = asyncio.get_event_loop().time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a dictionary."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "language": self.language,
            "code": self.code,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class PlaywrightTools:
    """Collection of Playwright browser automation tools."""
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages = []
        self.codegen_sessions = {}  # Map of session_id to CodeGenSession
        self.console_logs = []
        self.browser_initialized = False  # Track if browser is initialized
        
        # Create a screenshots directory if it doesn't exist
        self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        logger.info(f"Screenshots will be saved to: {self.screenshot_dir}")
    
    # === Helper Methods ===
    
    async def initialize(self):
        """Initialize Playwright without launching a browser."""
        try:
            # Launch Playwright but don't create a browser yet
            self.playwright = await async_playwright().start()
            logger.info("Playwright initialized")
            
            # Pre-initialize browser for better reliability
            try:
                print("Pre-initializing browser for better reliability...")
                await self._ensure_browser_initialized()
                print("Browser pre-initialized successfully")
            except Exception as browser_err:
                logger.warning(f"Browser pre-initialization failed (will retry when needed): {browser_err}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            return False
    
    async def _ensure_browser_initialized(self):
        """Ensure browser is initialized before using it."""
        if not self.browser_initialized:
            try:
                # Launch browser when needed
                # Note: user_data_dir is not supported in newer versions of Playwright
                self.browser = await self.playwright.chromium.launch(
                    headless=False
                    # Removed user_data_dir as it's causing an error
                )
                
                # Create context with maximized viewport
                viewport_size = {"width": 1425, "height": 776}  # Updated viewport size
                self.context = await self.browser.new_context(
                    viewport=viewport_size,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                self.browser_initialized = True
                logger.info(f"Browser initialized with viewport size {viewport_size}")
                
                # Create a page if needed
                if len(self.pages) == 0:
                    page = await self.context.new_page()
                    
                    # Set viewport directly on the page as well to ensure it's applied
                    await page.set_viewport_size(viewport_size)
                    
                    self.pages.append(page)
                    logger.info(f"Created new page with viewport size {viewport_size}")
                
                # For truly maximizing the window, use multiple approaches
                try:
                    # 1. Try CDP method first
                    cdp_session = await self.pages[0].context.new_cdp_session(self.pages[0])
                    await cdp_session.send('Browser.setWindowBounds', {
                        'windowId': 1,
                        'bounds': {'windowState': 'maximized'}
                    })
                    logger.info("Browser window maximized via CDP")
                except Exception as e:
                    # Log the error but continue - viewport size should still be large
                    logger.warning(f"Could not maximize window via CDP: {e}")
                    logger.info("Continuing with large viewport size only")
                    
                    # 2. Try JavaScript approach if CDP fails
                    try:
                        # Try to maximize window using JavaScript
                        await self.pages[0].evaluate("""() => {
                            if (window.screen && window.screen.availWidth) {
                                window.resizeTo(window.screen.availWidth, window.screen.availHeight);
                            }
                        }""")
                        logger.info("Attempted window maximization with JavaScript")
                    except Exception:
                        # Just continue if this also fails
                        pass
                        
                    # 3. Try fullscreen as a last resort
                    try:
                        await self.pages[0].evaluate("""() => {
                            if (document.documentElement.requestFullscreen) {
                                document.documentElement.requestFullscreen();
                            }
                        }""")
                        logger.info("Attempted fullscreen mode via JavaScript")
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error initializing browser: {e}")
                # Reset initialization state to allow retry
                self.browser_initialized = False
                raise

    async def _get_page(self, page_index: int) -> Optional[Page]:
        """Get a page by index, creating one if necessary."""
        if page_index < 0:
            return None
        
        # Ensure browser is initialized
        await self._ensure_browser_initialized()
        
        # Create new pages if needed
        while len(self.pages) <= page_index:
            new_page = await self.context.new_page()
            # Set up console log listeners
            new_page.on("console", lambda msg: self.console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
                "time": asyncio.get_event_loop().time()
            }))
            self.pages.append(new_page)
        
        return self.pages[page_index]
    
    async def cleanup(self):
        """Cleanup resources but maintain browser persistence."""
        try:
            # Close pages but keep the browser context and session alive
            for page in self.pages:
                if page and not page.is_closed():
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Error closing page: {e}")
            
            # Clear the pages list but don't close the context or browser
            self.pages = []
                
            if self.browser_initialized:
                logger.info("Keeping browser session alive")
            
            if self.playwright:
                logger.info("Playwright session remains active")
            
            logger.info("Tools cleaned up (browser session remains open for persistence)")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _get_screenshot_path(self, filename: str) -> str:
        """Get the full path for a screenshot file."""
        # If filename doesn't have a path, use the screenshot directory
        if not os.path.dirname(filename):
            return os.path.join(self.screenshot_dir, filename)
        return filename
    
    # === Code Generation Tool Implementations ===

    async def start_codegen_session(self, session_name: str, language: str) -> Dict[str, Any]:
        """Start a new code generation session."""
        session_id = f"session_{len(self.codegen_sessions) + 1}"
        session = CodeGenSession(session_id, session_name, language)
        self.codegen_sessions[session_id] = session
        
        return {
            "status": "success",
            "message": f"Code generation session started: {session_name}",
            "session": session.to_dict()
        }

    async def end_codegen_session(self, session_id: str) -> Dict[str, Any]:
        """End a code generation session."""
        if session_id not in self.codegen_sessions:
            return {
                "status": "error",
                "message": f"Session not found: {session_id}"
            }
        
        session = self.codegen_sessions.pop(session_id)
        
        return {
            "status": "success",
            "message": f"Code generation session ended: {session.name}",
            "session": session.to_dict()
        }

    async def get_codegen_session(self, session_id: str) -> Dict[str, Any]:
        """Get the current state of a code generation session."""
        if session_id not in self.codegen_sessions:
            return {
                "status": "error",
                "message": f"Session not found: {session_id}"
            }
        
        session = self.codegen_sessions[session_id]
        
        return {
            "status": "success",
            "session": session.to_dict()
        }

    async def clear_codegen_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a code generation session."""
        if session_id not in self.codegen_sessions:
            return {
                "status": "error",
                "message": f"Session not found: {session_id}"
            }
        
        session = self.codegen_sessions[session_id]
        session.update("")
        
        return {
            "status": "success",
            "message": f"Code generation session cleared: {session.name}",
            "session": session.to_dict()
        }

    # === Browser Automation Tool Implementations ===

    async def playwright_navigate(self, url: str, wait_for_load: bool = True, 
                                 capture_screenshot: bool = False, page_index: int = 0) -> Dict[str, Any]:
        """Navigate to a URL."""
        try:
            # Make sure the URL has http/https prefix
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # Get or create the page
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            try:
                # Check if page is still valid
                if not page.is_closed():
                    print(f"Navigating to {url}...")
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                        
                    status = response.status if response else None
                    
                    # Get the title and URL after navigation
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url}",
                        "title": title,
                        "url": current_url
                    }
                else:
                    # Page is closed, create a new one
                    print("Page is closed, creating a new one...")
                    page = await self.context.new_page()
                    self.pages[page_index] = page
                    
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                        
                    status = response.status if response else None
                    
                    # Get the title and URL after navigation
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url} with new page",
                        "title": title,
                        "url": current_url
                    }
            except Exception as e:
                # If the page is closed or any other error, create a new one
                print(f"Error navigating with existing page: {e}")
                print("Creating a new page and trying again...")
                
                # Create a new page and try again
                try:
                    page = await self.context.new_page()
                    # Replace the page in the pages list
                    if page_index < len(self.pages):
                        self.pages[page_index] = page
                    else:
                        self.pages.append(page)
                    
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                    
                    status = response.status if response else None
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url} with new page (after error)",
                        "title": title,
                        "url": current_url
                    }
                except Exception as e2:
                    return {"status": "error", "message": f"Error navigating to {url} even with new page: {str(e2)}"}
            
            if capture_screenshot:
                timestamp = int(asyncio.get_event_loop().time())
                screenshot_path = self._get_screenshot_path(f"navigation_{timestamp}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
                
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_screenshot(self, filename: str, selector: str = "", page_index: int = 0, 
                                  full_page: bool = False, omit_background: bool = False, 
                                  max_attempts: int = 3) -> Dict[str, Any]:
        """Take a screenshot with enhanced reliability and error recovery.
        
        Args:
            filename: Name of the file to save the screenshot to
            selector: Optional selector to take screenshot of specific element
            page_index: Index of the page to screenshot
            full_page: Whether to take a screenshot of the full page (not just the viewport)
            omit_background: Whether to hide default white background and allow transparency
            max_attempts: Maximum number of recovery attempts if errors occur
        """
        attempt_count = 0
        debug_screenshots = []
        last_error = None
        
        while attempt_count < max_attempts:
            try:
                attempt_count += 1
                print(f"Screenshot attempt {attempt_count}/{max_attempts} for '{filename}'")
                
                # First ensure playwright and browser are initialized
                if not self.browser_initialized:
                    print("Browser not initialized before screenshot, initializing now...")
                    try:
                        await self._ensure_browser_initialized()
                        print("Browser successfully initialized for screenshot")
                    except Exception as init_error:
                        print(f"Failed to initialize browser for screenshot: {init_error}")
                        last_error = init_error
                        
                        if attempt_count == max_attempts:
                            return {
                                "status": "error", 
                                "message": f"Browser initialization failed after {max_attempts} attempts: {str(init_error)}",
                                "debug_screenshots": debug_screenshots
                            }
                        else:
                            # Wait a bit before retrying
                            await asyncio.sleep(1)
                            continue
                
                # Verify and get a valid page
                try:
                    page = await self._get_page(page_index)
                    if not page:
                        if attempt_count == max_attempts:
                            return {"status": "error", "message": "Invalid page index", "debug_screenshots": debug_screenshots}
                        else:
                            await asyncio.sleep(1)
                            continue
                    
                    # Check if page is closed or in a problematic state
                    if page.is_closed():
                        print(f"Page is closed before screenshot, creating a new page...")
                        
                        # Create a new browser context if needed
                        if not self.context or self.context.is_closed():
                            print("Browser context is closed, creating new context...")
                            try:
                                self.context = await self.browser.new_context(
                                    viewport={"width": 1425, "height": 776},
                                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                )
                                print("Created new browser context")
                            except Exception as ctx_err:
                                print(f"Error creating browser context: {ctx_err}")
                                last_error = ctx_err
                                
                                if attempt_count == max_attempts:
                                    return {
                                        "status": "error", 
                                        "message": f"Browser context creation failed: {str(ctx_err)}",
                                        "debug_screenshots": debug_screenshots
                                    }
                                else:
                                    # Try to recreate the browser itself
                                    try:
                                        print("Attempting to recreate entire browser instance...")
                                        if self.browser:
                                            await self.browser.close()
                                        self.browser = await self.playwright.chromium.launch(headless=False)
                                        self.context = await self.browser.new_context(
                                            viewport={"width": 1425, "height": 776}
                                        )
                                        self.browser_initialized = True
                                        print("Browser instance successfully recreated")
                                    except Exception as browser_err:
                                        print(f"Failed to recreate browser: {browser_err}")
                                    
                                    await asyncio.sleep(1)
                                    continue
                        
                        # Create a new page
                        try:
                            print("Creating new page for screenshot...")
                            page = await self.context.new_page()
                            
                            # Replace or add the page in the pages list
                            if page_index < len(self.pages):
                                self.pages[page_index] = page
                            else:
                                self.pages.append(page)
                            
                            print(f"New page created at index {page_index}")
                            
                            # Navigate to a blank page to ensure the page is ready
                            await page.goto("about:blank")
                            print("Navigated to blank page to initialize page state")
                        except Exception as page_err:
                            print(f"Error creating new page: {page_err}")
                            last_error = page_err
                            
                            if attempt_count == max_attempts:
                                return {
                                    "status": "error", 
                                    "message": f"Error creating page: {str(page_err)}",
                                    "debug_screenshots": debug_screenshots
                                }
                            else:
                                await asyncio.sleep(1)
                                continue
                except Exception as page_err:
                    print(f"Error getting page for screenshot: {page_err}")
                    last_error = page_err
                    
                    if attempt_count == max_attempts:
                        return {
                            "status": "error", 
                            "message": f"Error with page: {str(page_err)}",
                            "debug_screenshots": debug_screenshots
                        }
                    else:
                        # For recovery on last attempt, try complete browser reset
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
                                
                                print("Browser reset successful, retrying screenshot operation...")
                            except Exception as reset_err:
                                print(f"Browser reset failed: {reset_err}")
                        
                        await asyncio.sleep(1)
                        continue
                
                # Ensure filename has .png extension
                if not filename.endswith(".png"):
                    filename += ".png"
                
                # Use full path for screenshot
                full_path = self._get_screenshot_path(filename)
                
                # Configure screenshot options
                screenshot_options = {
                    "path": full_path,
                    "full_page": full_page,
                    "omit_background": omit_background
                }
                
                # Take the screenshot based on whether a selector is provided
                if selector:
                    try:
                        print(f"Taking screenshot of element with selector: {selector}")
                        element = await page.wait_for_selector(selector, state="visible", timeout=5000)
                        if not element:
                            if attempt_count == max_attempts:
                                return {"status": "error", "message": f"Element not found: {selector}", "debug_screenshots": debug_screenshots}
                            else:
                                print(f"Element not found, retrying in next attempt...")
                                await asyncio.sleep(1)
                                continue
                        
                        # Take a full page screenshot first for context
                        debug_path = f"element_screenshot_context_{int(time.time())}.png"
                        await page.screenshot(path=self._get_screenshot_path(debug_path))
                        debug_screenshots.append(debug_path)
                        print(f"Context screenshot saved to: {debug_path}")
                        
                        # Now take screenshot of just the element
                        await element.screenshot(path=full_path)
                        print(f"Element screenshot saved to: {full_path}")
                    except Exception as e:
                        print(f"Error taking element screenshot: {e}")
                        last_error = e
                        
                        # Take a full page screenshot anyway for debugging
                        debug_path = f"debug_failed_selector_{int(time.time())}.png"
                        try:
                            await page.screenshot(path=self._get_screenshot_path(debug_path))
                            debug_screenshots.append(debug_path)
                            print(f"Debug screenshot after element selection failure: {debug_path}")
                        except Exception as debug_error:
                            print(f"Failed to take debug screenshot: {debug_error}")
                        
                        if attempt_count == max_attempts:
                            return {
                                "status": "error", 
                                "message": f"Error taking screenshot of element after {max_attempts} attempts: {str(e)}",
                                "debug_screenshots": debug_screenshots,
                                "selector": selector
                            }
                        else:
                            # Try waiting longer for the element in next attempt
                            await asyncio.sleep(1)
                            continue
                else:
                    try:
                        print(f"Taking screenshot of entire page...")
                        await page.screenshot(**screenshot_options)
                        print(f"Page screenshot saved to: {full_path}")
                    except Exception as e:
                        print(f"Error taking page screenshot: {e}")
                        last_error = e
                        
                        if attempt_count == max_attempts:
                            # Try with minimal options on last attempt
                            try:
                                print("Attempting screenshot with minimal options as last resort...")
                                minimal_path = self._get_screenshot_path(f"minimal_fallback_{int(time.time())}.png")
                                await page.screenshot(path=minimal_path)
                                
                                # If successful, we'll use this as our result
                                print(f"Minimal screenshot succeeded and saved to: {minimal_path}")
                                return {
                                    "status": "success",
                                    "message": f"Screenshot saved to {minimal_path} (using fallback method)",
                                    "filename": minimal_path,
                                    "used_fallback": True
                                }
                            except Exception as minimal_err:
                                print(f"Even minimal screenshot failed: {minimal_err}")
                                return {
                                    "status": "error", 
                                    "message": f"Error taking page screenshot after {max_attempts} attempts: {str(e)}",
                                    "debug_screenshots": debug_screenshots
                                }
                        else:
                            # Try with different options next time
                            if attempt_count == 1:
                                # On first failure, try without full_page
                                full_page = False 
                                print("Will retry without full_page option")
                            elif attempt_count == 2:
                                # On second failure, try without any options
                                omit_background = False
                                print("Will retry with minimal options")
                                
                            await asyncio.sleep(1)
                            continue
                
                # If we reached here, the screenshot was successful
                return {
                    "status": "success",
                    "message": f"Screenshot saved to {full_path}",
                    "filename": full_path,
                    "attempts": attempt_count,
                    "debug_screenshots": debug_screenshots
                }
                
            except Exception as e:
                print(f"Unexpected error in screenshot function: {e}")
                last_error = e
                
                # On final attempt, try emergency screenshot
                if attempt_count == max_attempts:
                    try:
                        # One last desperate attempt
                        emergency_path = self._get_screenshot_path(f"emergency_{int(time.time())}.png")
                        if page and not page.is_closed():
                            await page.screenshot(path=emergency_path)
                            return {
                                "status": "partial_success",
                                "message": f"Screenshot saved with emergency fallback: {emergency_path}",
                                "filename": emergency_path,
                                "original_error": str(e),
                                "debug_screenshots": debug_screenshots
                            }
                    except Exception:
                        pass
                    
                    return {
                        "status": "error", 
                        "message": f"Screenshot failed after {max_attempts} attempts: {str(e)}",
                        "debug_screenshots": debug_screenshots
                    }
                
                await asyncio.sleep(1)
                continue

    async def playwright_click(self, selector: str, page_index: int = 0, 
                              capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Common selectors for cookie accept buttons if the given selector doesn't work
            common_cookie_selectors = [
                selector,  # Try the provided selector first
                "#accept-cookies", 
                ".cookie-accept", 
                "[aria-label='Accept cookies']", 
                "[aria-label='Accept All']",
                "[aria-label='Accept all']",
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('Accept all')",
                "button:has-text('I accept')",
                "button:has-text('Allow all')",
                "button:has-text('Allow cookies')"
            ]
            
            # If this is likely a cookie consent button
            if "cookie" in selector.lower() or "accept" in selector.lower() or "consent" in selector.lower():
                print(f"Looks like a cookie button. Trying various selectors...")
                
                # Try each selector
                for cookie_selector in common_cookie_selectors:
                    try:
                        print(f"Trying selector: {cookie_selector}")
                        # Wait a short time for each selector
                        is_visible = await page.is_visible(cookie_selector, timeout=1000)
                        if is_visible:
                            print(f"Found visible element with selector: {cookie_selector}")
                            await page.click(cookie_selector)
                            
                            result = {
                                "status": "success",
                                "message": f"Clicked on {cookie_selector}"
                            }
                            
                            if capture_screenshot:
                                screenshot_path = self._get_screenshot_path(f"click_{asyncio.get_event_loop().time()}.png")
                                await page.screenshot(path=screenshot_path)
                                result["screenshot"] = screenshot_path
                                print(f"Screenshot saved to: {screenshot_path}")
                                
                            return result
                    except Exception as selector_error:
                        # Continue to the next selector
                        continue
                
                # If we get here, none of the selectors worked
                return {"status": "error", "message": f"Could not find any cookie consent button to click"}
            
            # For non-cookie buttons, just use the provided selector
            print(f"Waiting for selector to be visible: {selector}")
            await page.wait_for_selector(selector, state="visible")
            await page.click(selector)
            
            result = {
                "status": "success",
                "message": f"Clicked on {selector}"
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"click_{asyncio.get_event_loop().time()}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
                
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_click_and_switch_tab(self, selector: str, page_index: int = 0,
                                            capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element that opens a new tab and switch to it."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for the element to be visible
            await page.wait_for_selector(selector, state="visible")
            
            # Get the current number of pages
            initial_pages_count = len(self.pages)
            
            # Start listening for new pages
            async with page.expect_popup() as popup_info:
                await page.click(selector)
            
            # Get the new page
            new_page = await popup_info.value
            self.pages.append(new_page)
            new_page_index = len(self.pages) - 1
            
            # Set up console log listeners for the new page
            new_page.on("console", lambda msg: self.console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
                "time": asyncio.get_event_loop().time()
            }))
            
            # Wait for the new page to load
            await new_page.wait_for_load_state("networkidle")
            
            result = {
                "status": "success",
                "message": f"Clicked on {selector} and switched to new tab",
                "new_page_index": new_page_index,
                "title": await new_page.title(),
                "url": new_page.url
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"new_tab_{asyncio.get_event_loop().time()}.png")
                await new_page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_iframe_click(self, iframe_selector: str, element_selector: str,
                                     page_index: int = 0, capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element inside an iframe."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for iframe
            iframe = await page.wait_for_selector(iframe_selector)
            if not iframe:
                return {"status": "error", "message": f"Iframe not found: {iframe_selector}"}
            
            # Get the content frame
            frame = await iframe.content_frame()
            if not frame:
                return {"status": "error", "message": "Could not access iframe content"}
            
            # Click the element within the iframe
            await frame.wait_for_selector(element_selector, state="visible")
            await frame.click(element_selector)
            
            result = {
                "status": "success",
                "message": f"Clicked on {element_selector} inside iframe {iframe_selector}"
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"iframe_click_{asyncio.get_event_loop().time()}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_hover(self, selector: str, page_index: int = 0,
                              capture_screenshot: bool = False) -> Dict[str, Any]:
        """Hover over an element."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.wait_for_selector(selector, state="visible")
            await page.hover(selector)
            
            result = {
                "status": "success",
                "message": f"Hovered over {selector}"
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"hover_{asyncio.get_event_loop().time()}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_fill(self, selector: str, text: str, page_index: int = 0) -> Dict[str, Any]:
        """Fill a form field."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # First attempt - standard fill approach
            try:
                await page.wait_for_selector(selector, state="visible", timeout=5000)
                await page.fill(selector, text)
                
                return {
                    "status": "success",
                    "message": f"Filled {selector} with text",
                    "strategy_used": "standard_fill"
                }
            except PlaywrightTimeoutError:
                # If standard approach fails, try the next approach
                logger.info(f"Standard fill approach failed for '{selector}', trying with multi-strategy locate")
                
                # Try with multi-strategy locate
                multi_strategy_result = await self.playwright_multi_strategy_locate(
                    description=f"input field {selector.replace('[name=', '').replace(']', '')}",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if multi_strategy_result["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Filled input using multi-strategy approach",
                        "strategy_used": "multi_strategy",
                        "details": multi_strategy_result
                    }
                
                # Try with vision locator 
                logger.info(f"Multi-strategy approach failed, trying with vision locator")
                vision_result = await self.playwright_vision_locator(
                    text="search", 
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if vision_result["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Filled input using vision locator",
                        "strategy_used": "vision_locator",
                        "details": vision_result
                    }
                
                # Try with accessibility tree
                logger.info(f"Vision locator approach failed, trying with accessibility tree")
                a11y_result = await self.playwright_accessibility_locator(
                    description=f"search input field",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if a11y_result["status"] == "success" and a11y_result.get("element_found"):
                    return {
                        "status": "success",
                        "message": f"Filled input using accessibility locator",
                        "strategy_used": "accessibility_locator",
                        "details": a11y_result
                    }
                
                # Try with JavaScript evaluate as last resort
                logger.info(f"All specialized locators failed, trying with JavaScript as last resort")
                js_result = await self.playwright_js_locate(
                    description=f"search input",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if js_result["status"] == "success" and js_result.get("element_found"):
                    return {
                        "status": "success",
                        "message": f"Filled input using JavaScript locator",
                        "strategy_used": "js_locate",
                        "details": js_result
                    }
                
                # If all approaches fail, try some common selectors for search inputs
                common_search_selectors = [
                    "input[type='search']",
                    "input[type='text']",
                    "input.search-box",
                    "input.searchbox",
                    "input.gLFyf",  # Google search class
                    ".search-input",
                    "#search-input",
                    "[aria-label='Search']",
                    "[placeholder*='Search']",
                    "[placeholder*='search']"
                ]
                
                for common_selector in common_search_selectors:
                    try:
                        if await page.is_visible(common_selector, timeout=1000):
                            await page.fill(common_selector, text)
                            return {
                                "status": "success",
                                "message": f"Filled {common_selector} with text using common selector patterns",
                                "strategy_used": "common_selectors"
                            }
                    except Exception:
                        continue
                
                # If we reach here, all approaches failed
                return {
                    "status": "error",
                    "message": f"Failed to fill text. All approaches failed.",
                    "selector_tried": selector,
                    "text": text
                }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_select(self, selector: str, value: str, page_index: int = 0) -> Dict[str, Any]:
        """Select an option from a dropdown."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.wait_for_selector(selector, state="visible")
            await page.select_option(selector, value)
            
            return {
                "status": "success",
                "message": f"Selected value '{value}' in {selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_evaluate(self, script: str, page_index: int = 0) -> Dict[str, Any]:
        """Evaluate JavaScript in the page context."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            result = await page.evaluate(script)
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_console_logs(self, page_index: int = 0, count: int = 10) -> Dict[str, Any]:
        """Get console logs from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Get the most recent logs for this page
            page_logs = [log for log in self.console_logs if log.get("page_index", 0) == page_index]
            recent_logs = page_logs[-count:] if count < len(page_logs) else page_logs
            
            return {
                "status": "success",
                "logs": recent_logs
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_close(self, page_index: int = 0) -> Dict[str, Any]:
        """Close a page."""
        if page_index < 0 or page_index >= len(self.pages):
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Close the page
            await self.pages[page_index].close()
            
            # Remove from list
            self.pages.pop(page_index)
            
            return {
                "status": "success",
                "message": f"Closed page at index {page_index}",
                "remaining_pages": len(self.pages)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_expect_response(self, url_pattern: str, timeout_ms: int = 30000,
                                        page_index: int = 0) -> Dict[str, Any]:
        """Wait for a specific HTTP response."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for response
            async with page.expect_response(url_pattern, timeout=timeout_ms) as response_info:
                response = await response_info.value
            
            # Get response details
            status = response.status
            headers = await response.all_headers()
            
            return {
                "status": "success",
                "message": f"Received response from {response.url}",
                "response_status": status,
                "headers": headers
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_assert_response(self, url_pattern: str, status_code: int = 200,
                                        page_index: int = 0) -> Dict[str, Any]:
        """Assert that a response matches expectations."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create a callback to collect the responses
            matching_responses = []
            
            def handle_response(response):
                if url_pattern in response.url:
                    matching_responses.append(response)
            
            # Start listening for responses
            page.on("response", handle_response)
            
            # Wait a bit to collect responses
            await asyncio.sleep(2)
            
            # Stop listening
            page.remove_listener("response", handle_response)
            
            # Check matches
            if not matching_responses:
                return {
                    "status": "error",
                    "message": f"No responses matching {url_pattern} found"
                }
            
            # Check status codes
            success = all(response.status == status_code for response in matching_responses)
            
            return {
                "status": "success" if success else "error",
                "message": f"Response assertion {'passed' if success else 'failed'}",
                "expected_status": status_code,
                "actual_statuses": [response.status for response in matching_responses],
                "urls": [response.url for response in matching_responses]
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_custom_user_agent(self, user_agent: str, page_index: int = 0) -> Dict[str, Any]:
        """Set a custom user agent."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.set_extra_http_headers({"User-Agent": user_agent})
            
            return {
                "status": "success",
                "message": f"Set custom user agent: {user_agent}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_text(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible text from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            text = await page.text_content(selector)
            
            return {
                "status": "success",
                "text": text
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_html(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible HTML from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            html = await page.inner_html(selector)
            
            return {
                "status": "success",
                "html": html
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_back(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate back in the browser history."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.go_back()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated back",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_forward(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate forward in the browser history."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.go_forward()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated forward",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_drag(self, source_selector: str, target_selector: str,
                             page_index: int = 0) -> Dict[str, Any]:
        """Drag an element to another position."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for elements
            await page.wait_for_selector(source_selector, state="visible")
            await page.wait_for_selector(target_selector, state="visible")
            
            # Perform drag and drop
            await page.drag_and_drop(source_selector, target_selector)
            
            return {
                "status": "success",
                "message": f"Dragged {source_selector} to {target_selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_press_key(self, key: str, page_index: int = 0) -> Dict[str, Any]:
        """Press a key."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.keyboard.press(key)
            
            return {
                "status": "success",
                "message": f"Pressed key: {key}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_save_as_pdf(self, filename: str, page_index: int = 0) -> Dict[str, Any]:
        """Save the page as PDF."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            
            await page.pdf(path=filename)
            
            return {
                "status": "success",
                "message": f"Saved page as PDF: {filename}",
                "filename": filename
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    async def playwright_smart_click(self, text=None, selector=None, element_type: str = 'any', page_index: int = 0,
                                   capture_screenshot: bool = False, max_attempts: int = 3) -> Dict[str, Any]:
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
                
                # Also add the original selector if it was provided
                if selector is not None:
                    selectors.insert(0, selector)  # Try the exact selector first
                
                # Try each selector
                for selector in selectors:
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
                                screenshot_path = self._get_screenshot_path(f"smart_click_{int(asyncio.get_event_loop().time())}.png")
                                await page.screenshot(path=screenshot_path)
                                result["screenshot"] = screenshot_path
                                print(f"Screenshot saved to: {screenshot_path}")
                                
                            return result
                    except Exception:
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
                            failure_screenshot = f"smart_click_failure_{int(asyncio.get_event_loop().time())}.png"
                            await page.screenshot(path=self._get_screenshot_path(failure_screenshot))
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
                                error_screenshot = f"smart_click_error_{int(asyncio.get_event_loop().time())}.png"
                                await page.screenshot(path=self._get_screenshot_path(error_screenshot))
                                error_info["error_screenshot"] = error_screenshot
                        except Exception:
                            pass
                    
                    return error_info
                
                # Otherwise, wait a bit and try again
                await asyncio.sleep(1)
                continue

    async def playwright_navigate(self, url: str, wait_for_load: bool = True, 
                                 capture_screenshot: bool = False, page_index: int = 0) -> Dict[str, Any]:
        """Navigate to a URL."""
        try:
            # Make sure the URL has http/https prefix
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # Get or create the page
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            try:
                # Check if page is still valid
                if not page.is_closed():
                    print(f"Navigating to {url}...")
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                        
                    status = response.status if response else None
                    
                    # Get the title and URL after navigation
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url}",
                        "title": title,
                        "url": current_url
                    }
                else:
                    # Page is closed, create a new one
                    print("Page is closed, creating a new one...")
                    page = await self.context.new_page()
                    self.pages[page_index] = page
                    
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                        
                    status = response.status if response else None
                    
                    # Get the title and URL after navigation
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url} with new page",
                        "title": title,
                        "url": current_url
                    }
            except Exception as e:
                # If the page is closed or any other error, create a new one
                print(f"Error navigating with existing page: {e}")
                print("Creating a new page and trying again...")
                
                # Create a new page and try again
                try:
                    page = await self.context.new_page()
                    # Replace the page in the pages list
                    if page_index < len(self.pages):
                        self.pages[page_index] = page
                    else:
                        self.pages.append(page)
                    
                    if wait_for_load:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    else:
                        response = await page.goto(url)
                    
                    status = response.status if response else None
                    title = await page.title()
                    current_url = page.url
                    
                    result = {
                        "status": "success",
                        "message": f"Navigated to {url} with new page (after error)",
                        "title": title,
                        "url": current_url
                    }
                except Exception as e2:
                    return {"status": "error", "message": f"Error navigating to {url} even with new page: {str(e2)}"}
            
            if capture_screenshot:
                timestamp = int(asyncio.get_event_loop().time())
                screenshot_path = self._get_screenshot_path(f"navigation_{timestamp}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
                
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_screenshot(self, filename: str, selector: str = "", page_index: int = 0, 
                                  full_page: bool = False, omit_background: bool = False, 
                                  max_attempts: int = 3) -> Dict[str, Any]:
        """Take a screenshot with enhanced reliability and error recovery.
        
        Args:
            filename: Name of the file to save the screenshot to
            selector: Optional selector to take screenshot of specific element
            page_index: Index of the page to screenshot
            full_page: Whether to take a screenshot of the full page (not just the viewport)
            omit_background: Whether to hide default white background and allow transparency
            max_attempts: Maximum number of recovery attempts if errors occur
        """
        attempt_count = 0
        debug_screenshots = []
        last_error = None
        
        while attempt_count < max_attempts:
            try:
                attempt_count += 1
                print(f"Screenshot attempt {attempt_count}/{max_attempts} for '{filename}'")
                
                # First ensure playwright and browser are initialized
                if not self.browser_initialized:
                    print("Browser not initialized before screenshot, initializing now...")
                    try:
                        await self._ensure_browser_initialized()
                        print("Browser successfully initialized for screenshot")
                    except Exception as init_error:
                        print(f"Failed to initialize browser for screenshot: {init_error}")
                        last_error = init_error
                        
                        if attempt_count == max_attempts:
                            return {
                                "status": "error", 
                                "message": f"Browser initialization failed after {max_attempts} attempts: {str(init_error)}",
                                "debug_screenshots": debug_screenshots
                            }
                        else:
                            # Wait a bit before retrying
                            await asyncio.sleep(1)
                            continue
                
                # Verify and get a valid page
                try:
                    page = await self._get_page(page_index)
                    if not page:
                        if attempt_count == max_attempts:
                            return {"status": "error", "message": "Invalid page index", "debug_screenshots": debug_screenshots}
                        else:
                            await asyncio.sleep(1)
                            continue
                    
                    # Check if page is closed or in a problematic state
                    if page.is_closed():
                        print(f"Page is closed before screenshot, creating a new page...")
                        
                        # Create a new browser context if needed
                        if not self.context or self.context.is_closed():
                            print("Browser context is closed, creating new context...")
                            try:
                                self.context = await self.browser.new_context(
                                    viewport={"width": 1425, "height": 776},
                                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                )
                                print("Created new browser context")
                            except Exception as ctx_err:
                                print(f"Error creating browser context: {ctx_err}")
                                last_error = ctx_err
                                
                                if attempt_count == max_attempts:
                                    return {
                                        "status": "error", 
                                        "message": f"Browser context creation failed: {str(ctx_err)}",
                                        "debug_screenshots": debug_screenshots
                                    }
                                else:
                                    # Try to recreate the browser itself
                                    try:
                                        print("Attempting to recreate entire browser instance...")
                                        if self.browser:
                                            await self.browser.close()
                                        self.browser = await self.playwright.chromium.launch(headless=False)
                                        self.context = await self.browser.new_context(
                                            viewport={"width": 1425, "height": 776}
                                        )
                                        self.browser_initialized = True
                                        print("Browser instance successfully recreated")
                                    except Exception as browser_err:
                                        print(f"Failed to recreate browser: {browser_err}")
                                    
                                    await asyncio.sleep(1)
                                    continue
                        
                        # Create a new page
                        try:
                            print("Creating new page for screenshot...")
                            page = await self.context.new_page()
                            
                            # Replace or add the page in the pages list
                            if page_index < len(self.pages):
                                self.pages[page_index] = page
                            else:
                                self.pages.append(page)
                            
                            print(f"New page created at index {page_index}")
                            
                            # Navigate to a blank page to ensure the page is ready
                            await page.goto("about:blank")
                            print("Navigated to blank page to initialize page state")
                        except Exception as page_err:
                            print(f"Error creating new page: {page_err}")
                            last_error = page_err
                            
                            if attempt_count == max_attempts:
                                return {
                                    "status": "error", 
                                    "message": f"Error creating page: {str(page_err)}",
                                    "debug_screenshots": debug_screenshots
                                }
                            else:
                                await asyncio.sleep(1)
                                continue
                except Exception as page_err:
                    print(f"Error getting page for screenshot: {page_err}")
                    last_error = page_err
                    
                    if attempt_count == max_attempts:
                        return {
                            "status": "error", 
                            "message": f"Error with page: {str(page_err)}",
                            "debug_screenshots": debug_screenshots
                        }
                    else:
                        # For recovery on last attempt, try complete browser reset
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
                                
                                print("Browser reset successful, retrying screenshot operation...")
                            except Exception as reset_err:
                                print(f"Browser reset failed: {reset_err}")
                        
                        await asyncio.sleep(1)
                        continue
                
                # Ensure filename has .png extension
                if not filename.endswith(".png"):
                    filename += ".png"
                
                # Use full path for screenshot
                full_path = self._get_screenshot_path(filename)
                
                # Configure screenshot options
                screenshot_options = {
                    "path": full_path,
                    "full_page": full_page,
                    "omit_background": omit_background
                }
                
                # Take the screenshot based on whether a selector is provided
                if selector:
                    try:
                        print(f"Taking screenshot of element with selector: {selector}")
                        element = await page.wait_for_selector(selector, state="visible", timeout=5000)
                        if not element:
                            if attempt_count == max_attempts:
                                return {"status": "error", "message": f"Element not found: {selector}", "debug_screenshots": debug_screenshots}
                            else:
                                print(f"Element not found, retrying in next attempt...")
                                await asyncio.sleep(1)
                                continue
                        
                        # Take a full page screenshot first for context
                        debug_path = f"element_screenshot_context_{int(time.time())}.png"
                        await page.screenshot(path=self._get_screenshot_path(debug_path))
                        debug_screenshots.append(debug_path)
                        print(f"Context screenshot saved to: {debug_path}")
                        
                        # Now take screenshot of just the element
                        await element.screenshot(path=full_path)
                        print(f"Element screenshot saved to: {full_path}")
                    except Exception as e:
                        print(f"Error taking element screenshot: {e}")
                        last_error = e
                        
                        # Take a full page screenshot anyway for debugging
                        debug_path = f"debug_failed_selector_{int(time.time())}.png"
                        try:
                            await page.screenshot(path=self._get_screenshot_path(debug_path))
                            debug_screenshots.append(debug_path)
                            print(f"Debug screenshot after element selection failure: {debug_path}")
                        except Exception as debug_error:
                            print(f"Failed to take debug screenshot: {debug_error}")
                        
                        if attempt_count == max_attempts:
                            return {
                                "status": "error", 
                                "message": f"Error taking screenshot of element after {max_attempts} attempts: {str(e)}",
                                "debug_screenshots": debug_screenshots,
                                "selector": selector
                            }
                        else:
                            # Try waiting longer for the element in next attempt
                            await asyncio.sleep(1)
                            continue
                else:
                    try:
                        print(f"Taking screenshot of entire page...")
                        await page.screenshot(**screenshot_options)
                        print(f"Page screenshot saved to: {full_path}")
                    except Exception as e:
                        print(f"Error taking page screenshot: {e}")
                        last_error = e
                        
                        if attempt_count == max_attempts:
                            # Try with minimal options on last attempt
                            try:
                                print("Attempting screenshot with minimal options as last resort...")
                                minimal_path = self._get_screenshot_path(f"minimal_fallback_{int(time.time())}.png")
                                await page.screenshot(path=minimal_path)
                                
                                # If successful, we'll use this as our result
                                print(f"Minimal screenshot succeeded and saved to: {minimal_path}")
                                return {
                                    "status": "success",
                                    "message": f"Screenshot saved to {minimal_path} (using fallback method)",
                                    "filename": minimal_path,
                                    "used_fallback": True
                                }
                            except Exception as minimal_err:
                                print(f"Even minimal screenshot failed: {minimal_err}")
                                return {
                                    "status": "error", 
                                    "message": f"Error taking page screenshot after {max_attempts} attempts: {str(e)}",
                                    "debug_screenshots": debug_screenshots
                                }
                        else:
                            # Try with different options next time
                            if attempt_count == 1:
                                # On first failure, try without full_page
                                full_page = False 
                                print("Will retry without full_page option")
                            elif attempt_count == 2:
                                # On second failure, try without any options
                                omit_background = False
                                print("Will retry with minimal options")
                                
                            await asyncio.sleep(1)
                            continue
                
                # If we reached here, the screenshot was successful
                return {
                    "status": "success",
                    "message": f"Screenshot saved to {full_path}",
                    "filename": full_path,
                    "attempts": attempt_count,
                    "debug_screenshots": debug_screenshots
                }
                
            except Exception as e:
                print(f"Unexpected error in screenshot function: {e}")
                last_error = e
                
                # On final attempt, try emergency screenshot
                if attempt_count == max_attempts:
                    try:
                        # One last desperate attempt
                        emergency_path = self._get_screenshot_path(f"emergency_{int(time.time())}.png")
                        if page and not page.is_closed():
                            await page.screenshot(path=emergency_path)
                            return {
                                "status": "partial_success",
                                "message": f"Screenshot saved with emergency fallback: {emergency_path}",
                                "filename": emergency_path,
                                "original_error": str(e),
                                "debug_screenshots": debug_screenshots
                            }
                    except Exception:
                        pass
                    
                    return {
                        "status": "error", 
                        "message": f"Screenshot failed after {max_attempts} attempts: {str(e)}",
                        "debug_screenshots": debug_screenshots
                    }
                
                await asyncio.sleep(1)
                continue

    async def playwright_click(self, selector: str, page_index: int = 0, 
                              capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Common selectors for cookie accept buttons if the given selector doesn't work
            common_cookie_selectors = [
                selector,  # Try the provided selector first
                "#accept-cookies", 
                ".cookie-accept", 
                "[aria-label='Accept cookies']", 
                "[aria-label='Accept All']",
                "[aria-label='Accept all']",
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('Accept all')",
                "button:has-text('I accept')",
                "button:has-text('Allow all')",
                "button:has-text('Allow cookies')"
            ]
            
            # If this is likely a cookie consent button
            if "cookie" in selector.lower() or "accept" in selector.lower() or "consent" in selector.lower():
                print(f"Looks like a cookie button. Trying various selectors...")
                
                # Try each selector
                for cookie_selector in common_cookie_selectors:
                    try:
                        print(f"Trying selector: {cookie_selector}")
                        # Wait a short time for each selector
                        is_visible = await page.is_visible(cookie_selector, timeout=1000)
                        if is_visible:
                            print(f"Found visible element with selector: {cookie_selector}")
                            await page.click(cookie_selector)
                            
                            result = {
                                "status": "success",
                                "message": f"Clicked on {cookie_selector}"
                            }
                            
                            if capture_screenshot:
                                screenshot_path = self._get_screenshot_path(f"click_{asyncio.get_event_loop().time()}.png")
                                await page.screenshot(path=screenshot_path)
                                result["screenshot"] = screenshot_path
                                print(f"Screenshot saved to: {screenshot_path}")
                                
                            return result
                    except Exception as selector_error:
                        # Continue to the next selector
                        continue
                
                # If we get here, none of the selectors worked
                return {"status": "error", "message": f"Could not find any cookie consent button to click"}
            
            # For non-cookie buttons, just use the provided selector
            print(f"Waiting for selector to be visible: {selector}")
            await page.wait_for_selector(selector, state="visible")
            await page.click(selector)
            
            result = {
                "status": "success",
                "message": f"Clicked on {selector}"
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"click_{asyncio.get_event_loop().time()}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
                
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_click_and_switch_tab(self, selector: str, page_index: int = 0,
                                            capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element that opens a new tab and switch to it."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for the element to be visible
            await page.wait_for_selector(selector, state="visible")
            
            # Get the current number of pages
            initial_pages_count = len(self.pages)
            
            # Start listening for new pages
            async with page.expect_popup() as popup_info:
                await page.click(selector)
            
            # Get the new page
            new_page = await popup_info.value
            self.pages.append(new_page)
            new_page_index = len(self.pages) - 1
            
            # Set up console log listeners for the new page
            new_page.on("console", lambda msg: self.console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
                "time": asyncio.get_event_loop().time()
            }))
            
            # Wait for the new page to load
            await new_page.wait_for_load_state("networkidle")
            
            result = {
                "status": "success",
                "message": f"Clicked on {selector} and switched to new tab",
                "new_page_index": new_page_index,
                "title": await new_page.title(),
                "url": new_page.url
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"new_tab_{asyncio.get_event_loop().time()}.png")
                await new_page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_iframe_click(self, iframe_selector: str, element_selector: str,
                                     page_index: int = 0, capture_screenshot: bool = False) -> Dict[str, Any]:
        """Click on an element inside an iframe."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for iframe
            iframe = await page.wait_for_selector(iframe_selector)
            if not iframe:
                return {"status": "error", "message": f"Iframe not found: {iframe_selector}"}
            
            # Get the content frame
            frame = await iframe.content_frame()
            if not frame:
                return {"status": "error", "message": "Could not access iframe content"}
            
            # Click the element within the iframe
            await frame.wait_for_selector(element_selector, state="visible")
            await frame.click(element_selector)
            
            result = {
                "status": "success",
                "message": f"Clicked on {element_selector} inside iframe {iframe_selector}"
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"iframe_click_{asyncio.get_event_loop().time()}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_hover(self, selector: str, page_index: int = 0,
                              capture_screenshot: bool = False) -> Dict[str, Any]:
        """Hover over an element."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.wait_for_selector(selector, state="visible")
            await page.hover(selector)
            
            result = {
                "status": "success",
                "message": f"Hovered over {selector}"
            }
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path(f"hover_{asyncio.get_event_loop().time()}.png")
                await page.screenshot(path=screenshot_path)
                result["screenshot"] = screenshot_path
                print(f"Screenshot saved to: {screenshot_path}")
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_fill(self, selector: str, text: str, page_index: int = 0) -> Dict[str, Any]:
        """Fill a form field."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # First attempt - standard fill approach
            try:
                await page.wait_for_selector(selector, state="visible", timeout=5000)
                await page.fill(selector, text)
                
                return {
                    "status": "success",
                    "message": f"Filled {selector} with text",
                    "strategy_used": "standard_fill"
                }
            except PlaywrightTimeoutError:
                # If standard approach fails, try the next approach
                logger.info(f"Standard fill approach failed for '{selector}', trying with multi-strategy locate")
                
                # Try with multi-strategy locate
                multi_strategy_result = await self.playwright_multi_strategy_locate(
                    description=f"input field {selector.replace('[name=', '').replace(']', '')}",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if multi_strategy_result["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Filled input using multi-strategy approach",
                        "strategy_used": "multi_strategy",
                        "details": multi_strategy_result
                    }
                
                # Try with vision locator 
                logger.info(f"Multi-strategy approach failed, trying with vision locator")
                vision_result = await self.playwright_vision_locator(
                    text="search", 
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if vision_result["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Filled input using vision locator",
                        "strategy_used": "vision_locator",
                        "details": vision_result
                    }
                
                # Try with accessibility tree
                logger.info(f"Vision locator approach failed, trying with accessibility tree")
                a11y_result = await self.playwright_accessibility_locator(
                    description=f"search input field",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if a11y_result["status"] == "success" and a11y_result.get("element_found"):
                    return {
                        "status": "success",
                        "message": f"Filled input using accessibility locator",
                        "strategy_used": "accessibility_locator",
                        "details": a11y_result
                    }
                
                # Try with JavaScript evaluate as last resort
                logger.info(f"All specialized locators failed, trying with JavaScript as last resort")
                js_result = await self.playwright_js_locate(
                    description=f"search input",
                    action="fill",
                    text_input=text,
                    page_index=page_index
                )
                
                if js_result["status"] == "success" and js_result.get("element_found"):
                    return {
                        "status": "success",
                        "message": f"Filled input using JavaScript locator",
                        "strategy_used": "js_locate",
                        "details": js_result
                    }
                
                # If all approaches fail, try some common selectors for search inputs
                common_search_selectors = [
                    "input[type='search']",
                    "input[type='text']",
                    "input.search-box",
                    "input.searchbox",
                    "input.gLFyf",  # Google search class
                    ".search-input",
                    "#search-input",
                    "[aria-label='Search']",
                    "[placeholder*='Search']",
                    "[placeholder*='search']"
                ]
                
                for common_selector in common_search_selectors:
                    try:
                        if await page.is_visible(common_selector, timeout=1000):
                            await page.fill(common_selector, text)
                            return {
                                "status": "success",
                                "message": f"Filled {common_selector} with text using common selector patterns",
                                "strategy_used": "common_selectors"
                            }
                    except Exception:
                        continue
                
                # If we reach here, all approaches failed
                return {
                    "status": "error",
                    "message": f"Failed to fill text. All approaches failed.",
                    "selector_tried": selector,
                    "text": text
                }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_select(self, selector: str, value: str, page_index: int = 0) -> Dict[str, Any]:
        """Select an option from a dropdown."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.wait_for_selector(selector, state="visible")
            await page.select_option(selector, value)
            
            return {
                "status": "success",
                "message": f"Selected value '{value}' in {selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_evaluate(self, script: str, page_index: int = 0) -> Dict[str, Any]:
        """Evaluate JavaScript in the page context."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            result = await page.evaluate(script)
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_console_logs(self, page_index: int = 0, count: int = 10) -> Dict[str, Any]:
        """Get console logs from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Get the most recent logs for this page
            page_logs = [log for log in self.console_logs if log.get("page_index", 0) == page_index]
            recent_logs = page_logs[-count:] if count < len(page_logs) else page_logs
            
            return {
                "status": "success",
                "logs": recent_logs
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_close(self, page_index: int = 0) -> Dict[str, Any]:
        """Close a page."""
        if page_index < 0 or page_index >= len(self.pages):
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Close the page
            await self.pages[page_index].close()
            
            # Remove from list
            self.pages.pop(page_index)
            
            return {
                "status": "success",
                "message": f"Closed page at index {page_index}",
                "remaining_pages": len(self.pages)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_expect_response(self, url_pattern: str, timeout_ms: int = 30000,
                                        page_index: int = 0) -> Dict[str, Any]:
        """Wait for a specific HTTP response."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for response
            async with page.expect_response(url_pattern, timeout=timeout_ms) as response_info:
                response = await response_info.value
            
            # Get response details
            status = response.status
            headers = await response.all_headers()
            
            return {
                "status": "success",
                "message": f"Received response from {response.url}",
                "response_status": status,
                "headers": headers
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_assert_response(self, url_pattern: str, status_code: int = 200,
                                        page_index: int = 0) -> Dict[str, Any]:
        """Assert that a response matches expectations."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create a callback to collect the responses
            matching_responses = []
            
            def handle_response(response):
                if url_pattern in response.url:
                    matching_responses.append(response)
            
            # Start listening for responses
            page.on("response", handle_response)
            
            # Wait a bit to collect responses
            await asyncio.sleep(2)
            
            # Stop listening
            page.remove_listener("response", handle_response)
            
            # Check matches
            if not matching_responses:
                return {
                    "status": "error",
                    "message": f"No responses matching {url_pattern} found"
                }
            
            # Check status codes
            success = all(response.status == status_code for response in matching_responses)
            
            return {
                "status": "success" if success else "error",
                "message": f"Response assertion {'passed' if success else 'failed'}",
                "expected_status": status_code,
                "actual_statuses": [response.status for response in matching_responses],
                "urls": [response.url for response in matching_responses]
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_custom_user_agent(self, user_agent: str, page_index: int = 0) -> Dict[str, Any]:
        """Set a custom user agent."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.set_extra_http_headers({"User-Agent": user_agent})
            
            return {
                "status": "success",
                "message": f"Set custom user agent: {user_agent}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_text(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible text from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            text = await page.text_content(selector)
            
            return {
                "status": "success",
                "text": text
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_html(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible HTML from the page."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            html = await page.inner_html(selector)
            
            return {
                "status": "success",
                "html": html
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_back(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate back in the browser history."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.go_back()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated back",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_forward(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate forward in the browser history."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.go_forward()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated forward",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_drag(self, source_selector: str, target_selector: str,
                             page_index: int = 0) -> Dict[str, Any]:
        """Drag an element to another position."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Wait for elements
            await page.wait_for_selector(source_selector, state="visible")
            await page.wait_for_selector(target_selector, state="visible")
            
            # Perform drag and drop
            await page.drag_and_drop(source_selector, target_selector)
            
            return {
                "status": "success",
                "message": f"Dragged {source_selector} to {target_selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_press_key(self, key: str, page_index: int = 0) -> Dict[str, Any]:
        """Press a key."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            await page.keyboard.press(key)
            
            return {
                "status": "success",
                "message": f"Pressed key: {key}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_save_as_pdf(self, filename: str, page_index: int = 0) -> Dict[str, Any]:
        """Save the page as PDF."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            
            await page.pdf(path=filename)
            
            return {
                "status": "success",
                "message": f"Saved page as PDF: {filename}",
                "filename": filename
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    async def playwright_smart_click(self, text=None, selector=None, element_type: str = 'any', page_index: int = 0,
                                   capture_screenshot: bool = False, max_attempts: int = 3) -> Dict[str, Any]:
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
                
                # Also add the original selector if it was provided
                if selector is not None:
                    selectors.insert(0, selector)  # Try the exact selector first
                
                # Try each selector
                for selector in selectors:
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
                                screenshot_path = self._get_screenshot_path(f"smart_click_{int(asyncio.get_event_loop().time())}.png")
                                await page.screenshot(path=screenshot_path)
                                result["screenshot"] = screenshot_path
                                print(f"Screenshot saved to: {screenshot_path}")
                                
                            return result
                    except Exception:
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
                            failure_screenshot = f"smart_click_failure_{int(asyncio.get_event_loop().time())}.png"
                            await page.screenshot(path=self._get_screenshot_path(failure_screenshot))
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
                                error_screenshot = f"smart_click_error_{int(asyncio.get_event_loop().time())}.png"
                                await page.screenshot(path=self._get_screenshot_path(error_screenshot))
                                error_info["error_screenshot"] = error_screenshot
                        except Exception:
                            pass
                    
                    return error_info
                
                # Otherwise, wait a bit and try again
                await asyncio.sleep(1)
                continue

    # === Dialog Handling Methods ===
    
    async def playwright_set_dialog_handler(self, action: str = "dismiss", prompt_text: str = "", 
                                           page_index: int = 0) -> Dict[str, Any]:
        """
        Set a persistent dialog handler for the page. This will handle any dialog that appears
        until the handler is removed or changed.
        
        Args:
            action: Action to take ('accept' or 'dismiss')
            prompt_text: Text to enter for prompt dialogs
            page_index: Index of the page to set dialog handler on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Define a reusable dialog handler
            async def handle_dialog(dialog):
                dialog_type = dialog.type
                dialog_message = dialog.message
                
                print(f"Dialog appeared: {dialog_type} - {dialog_message}")
                
                if action.lower() == "accept":
                    if dialog_type == "prompt" and prompt_text:
                        await dialog.accept(prompt_text)
                    else:
                        await dialog.accept()
                else:  # Default to dismiss
                    await dialog.dismiss()
            
            # Remove any existing handlers first to avoid conflicts
            page.remove_listener("dialog", None)
            
            # Set the new handler
            page.on("dialog", handle_dialog)
            
            return {
                "status": "success",
                "message": f"Dialog handler set to {action} all dialogs",
                "action": action,
                "prompt_text": prompt_text if prompt_text else None
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_remove_dialog_handler(self, page_index: int = 0) -> Dict[str, Any]:
        """
        Remove any dialog handlers from the page.
        
        Args:
            page_index: Index of the page to remove dialog handlers from
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Remove all dialog handlers
            page.remove_listener("dialog", None)
            
            return {
                "status": "success",
                "message": "Dialog handlers removed"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_auto_handle_next_dialog(self, action: str = "accept", prompt_text: str = "", 
                                               handle_once: bool = True, page_index: int = 0) -> Dict[str, Any]:
        """
        Set up a handler for the next dialog and optionally remove it after handling.
        
        Args:
            action: Action to take ('accept' or 'dismiss')
            prompt_text: Text to enter for prompt dialogs
            handle_once: Whether to remove the handler after handling one dialog
            page_index: Index of the page to set dialog handler on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create future to track when dialog appears
            dialog_info = {"appeared": False, "type": None, "message": None}
            
            # Define a handler that will self-remove after one dialog if requested
            async def handle_one_dialog(dialog):
                dialog_type = dialog.type
                dialog_message = dialog.message
                
                print(f"Dialog appeared: {dialog_type} - {dialog_message}")
                
                # Update dialog info
                dialog_info["appeared"] = True
                dialog_info["type"] = dialog_type
                dialog_info["message"] = dialog_message
                
                # Handle the dialog
                if action.lower() == "accept":
                    if dialog_type == "prompt" and prompt_text:
                        await dialog.accept(prompt_text)
                        dialog_info["prompt_text"] = prompt_text
                    else:
                        await dialog.accept()
                else:
                    await dialog.dismiss()
                
                dialog_info["action_taken"] = action
                
                # Set the future result
                if not dialog_future.done():
                    dialog_future.set_result(dialog_info)
                
                # Remove the listener
                page.remove_listener("dialog", handle_one_dialog)
            
            # Set the handler
            page.on("dialog", handle_one_dialog)
            
            return {
                "status": "success",
                "message": f"Set up auto-handler for next dialog (will {action})",
                "action": action,
                "handle_once": handle_once,
                "dialog_info": dialog_info
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Additional Locator Methods ===
    
    async def playwright_css_locator(self, selector: str, action: str = "find", 
                                   text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """
        Use CSS selectors to locate elements with Playwright's enhanced CSS support.
        Includes features like :has-text(), :visible, :has(), etc.
        
        Args:
            selector: CSS selector to use
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create locator with CSS
            locator = page.locator(f"css={selector}")
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found matching CSS selector: {selector}"
                }
            
            # Get information about found elements (limit to first 5)
            elements_info = []
            for i in range(min(count, 5)):
                el = locator.nth(i)
                is_visible = await el.is_visible()
                
                try:
                    tag_name = await el.evaluate("el => el.tagName.toLowerCase()")
                    text_content = await el.text_content() or ""
                    text_content = text_content.strip()[:50] + ("..." if len(text_content) > 50 else "")
                    bounding_box = await el.bounding_box()
                except Exception:
                    tag_name = "unknown"
                    text_content = ""
                    bounding_box = None
                
                elements_info.append({
                    "index": i,
                    "tag": tag_name,
                    "text": text_content,
                    "is_visible": is_visible,
                    "bounding_box": bounding_box
                })
            
            # Perform the requested action on the first element
            action_result = None
            if action == "click":
                await locator.first.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await locator.first.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements matching CSS selector: {selector}",
                "elements": elements_info,
                "action_performed": action_result,
                "locator_type": "css"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_nth_element(self, selector: str, index: int, action: str = "find",
                                    text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """
        Target a specific element by its index in a collection of matching elements.
        
        Args:
            selector: Base selector to find elements
            index: Zero-based index of the element to target
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create locator and get nth element
            locator = page.locator(selector)
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found matching selector: {selector}"
                }
            
            if index >= count:
                return {
                    "status": "error",
                    "message": f"Index {index} out of range, only {count} elements found"
                }
            
            # Get the nth element
            element = locator.nth(index)
            is_visible = await element.is_visible()
            
            # Get element info
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            text_content = await element.text_content() or ""
            text_content = text_content.strip()[:50] + ("..." if len(text_content) > 50 else "")
            bounding_box = await element.bounding_box()
            
            element_info = {
                "index": index,
                "tag": tag_name,
                "text": text_content,
                "is_visible": is_visible,
                "bounding_box": bounding_box,
                "total_elements": count
            }
            
            # Perform the requested action
            action_result = None
            if action == "click":
                await element.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await element.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found element at index {index} of {count} matching {selector}",
                "element": element_info,
                "action_performed": action_result,
                "locator_type": "nth"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_parent_element(self, selector: str, action: str = "find", 
                                       text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """
        Target the parent element of a matched element.
        
        Args:
            selector: Selector for the child element
            action: Action to perform on the parent ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Check if child exists
            child = page.locator(selector)
            count = await child.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found matching selector: {selector}"
                }
            
            # Get the parent using JavaScript evaluation
            parent = await child.first.evaluate("""(element) => {
                const parent = element.parentElement;
                if (!parent) return null;
                
                return {
                    tagName: parent.tagName.toLowerCase(),
                    id: parent.id || undefined,
                    className: parent.className || undefined,
                    textContent: parent.textContent?.trim()?.substring(0, 50) || '',
                    hasChildren: parent.children.length > 0,
                    childrenCount: parent.children.length
                };
            }""")
            
            if not parent:
                return {
                    "status": "error",
                    "message": f"Element found, but it has no parent element"
                }
            
            # Perform the requested action on the parent
            action_result = None
            if action == "click":
                # Evaluating JavaScript to click since we don't have a direct locator
                await child.first.evaluate("el => el.parentElement.click()")
                action_result = "Clicked parent element"
            elif action == "fill" and text_input:
                # For fill, we find an input within the parent if possible
                await child.first.evaluate(
                    f"el => {{ const input = el.parentElement.querySelector('input, textarea'); if(input) input.value = '{text_input}'; }}"
                )
                action_result = f"Attempted to fill input within parent with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found parent of element matching {selector}",
                "parent": parent,
                "action_performed": action_result,
                "locator_type": "parent"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_xpath_locator(self, xpath: str, action: str = "find", 
                                     text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """
        Use XPath selector to locate elements.
        
        Args:
            xpath: XPath selector to use
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Create locator with XPath
            locator = page.locator(f"xpath={xpath}")
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found matching XPath: {xpath}"
                }
            
            # Get information about found elements (limit to first 5)
            elements_info = []
            for i in range(min(count, 5)):
                el = locator.nth(i)
                is_visible = await el.is_visible()
                
                try:
                    tag_name = await el.evaluate("el => el.tagName.toLowerCase()")
                    text_content = await el.text_content() or ""
                    text_content = text_content.strip()[:50] + ("..." if len(text_content) > 50 else "")
                    bounding_box = await el.bounding_box()
                except Exception:
                    tag_name = "unknown"
                    text_content = ""
                    bounding_box = None
                
                elements_info.append({
                    "index": i,
                    "tag": tag_name,
                    "text": text_content,
                    "is_visible": is_visible,
                    "bounding_box": bounding_box
                })
            
            # Perform the requested action on the first element
            action_result = None
            if action == "click":
                await locator.first.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await locator.first.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements matching XPath: {xpath}",
                "elements": elements_info,
                "action_performed": action_result,
                "locator_type": "xpath"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_label_to_control(self, label_text: str, action: str = "find", 
                                        text_input: str = "", exact: bool = False, 
                                        page_index: int = 0) -> Dict[str, Any]:
        """
        Find an input element by its associated label text.
        Uses Playwright's automatic label-to-form-control retargeting.
        
        Args:
            label_text: Text of the label to find
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            exact: Whether to match the exact label text
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Use Playwright's getByLabel method
            control = page.get_by_label(label_text, exact=exact)
            
            # Check if control exists
            count = await control.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No form controls found with label: {label_text}"
                }
            
            # Get control info
            tag_name = await control.first.evaluate("el => el.tagName.toLowerCase()")
            input_type = await control.first.evaluate("el => el.type || ''")
            is_visible = await control.first.is_visible()
            is_enabled = await control.first.is_enabled()
            
            control_info = {
                "tag": tag_name,
                "type": input_type,
                "is_visible": is_visible,
                "is_enabled": is_enabled,
                "label_text": label_text
            }
            
            # Perform the requested action
            action_result = None
            if action == "click":
                await control.first.click()
                action_result = "Clicked control"
            elif action == "fill" and text_input:
                await control.first.fill(text_input)
                action_result = f"Filled control with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found form control with label: {label_text}",
                "control": control_info,
                "action_performed": action_result,
                "locator_type": "label"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Accessibility Methods ===
    
    async def playwright_accessibility_snapshot(self, selector: str = "", 
                                              page_index: int = 0) -> Dict[str, Any]:
        """
        Get a snapshot of the accessibility tree for debugging or testing.
        
        Args:
            selector: Optional selector to get snapshot for specific element
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Get the accessibility snapshot
            if selector:
                element = await page.wait_for_selector(selector, timeout=5000)
                if not element:
                    return {
                        "status": "error",
                        "message": f"Element not found: {selector}"
                    }
                snapshot = await page.accessibility.snapshot(root=element)
            else:
                snapshot = await page.accessibility.snapshot()
            
            # Process snapshot to make it more readable/useful
            def process_node(node, depth=0):
                processed = {
                    "role": node.get("role", ""),
                    "name": node.get("name", ""),
                    "depth": depth
                }
                
                # Add optional properties if they exist
                for prop in ["value", "description", "checked", "pressed"]:
                    if prop in node:
                        processed[prop] = node[prop]
                
                # Process children recursively
                if "children" in node and node["children"]:
                    processed["children"] = [
                        process_node(child, depth + 1) 
                        for child in node["children"]
                    ]
                    
                return processed
            
            # Process the snapshot
            processed_snapshot = process_node(snapshot) if snapshot else {}
            
            return {
                "status": "success",
                "message": "Accessibility snapshot captured",
                "snapshot": processed_snapshot
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_find_by_role(self, role: str, name: str = "", exact: bool = False,
                                    action: str = "find", text_input: str = "",
                                    page_index: int = 0) -> Dict[str, Any]:
        """
        Find elements by their ARIA role, making testing more accessible.
        
        Args:
            role: ARIA role to look for (button, link, heading, etc.)
            name: Accessible name to filter by
            exact: Whether to match the name exactly
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Configure options for get_by_role
            options = {}
            if name is not None:
                options["name"] = name
                options["exact"] = exact
            
            # Use the role locator
            locator = page.get_by_role(role, **options)
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                name_part = f" with name '{name}'" if name else ""
                return {
                    "status": "error",
                    "message": f"No elements found with role '{role}'{name_part}"
                }
            
            # Get properties of the first element
            first_element = locator.first
            tag_name = await first_element.evaluate("el => el.tagName.toLowerCase()")
            is_visible = await first_element.is_visible()
            
            # Perform requested action
            action_result = None
            if action == "click":
                await first_element.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await first_element.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            name_part = f" with name '{name}'" if name else ""
            return {
                "status": "success",
                "message": f"Found {count} elements with role '{role}'{name_part}",
                "first_element": {
                    "tag": tag_name,
                    "is_visible": is_visible,
                    "role": role,
                    "name": name
                },
                "action_performed": action_result,
                "total_matches": count
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_locator_by_label(self, text: str, exact: bool = False,
                                        action: str = "find", text_input: str = "",
                                        page_index: int = 0) -> Dict[str, Any]:
        """
        Find form control elements associated with a label.
        
        Args:
            text: Label text to search for
            exact: Whether label text matching should be exact
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Use the label locator
            locator = page.get_by_label(text, exact=exact)
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No form controls found with label: {text}"
                }
            
            # Get properties of the first element
            first_element = locator.first
            tag_name = await first_element.evaluate("el => el.tagName.toLowerCase()")
            input_type = await first_element.evaluate("el => el.type || ''")
            is_visible = await first_element.is_visible()
            
            # Perform requested action
            action_result = None
            if action == "click":
                await first_element.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await first_element.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} form controls with label: {text}",
                "first_element": {
                    "tag": tag_name,
                    "type": input_type,
                    "is_visible": is_visible,
                    "label": text
                },
                "action_performed": action_result,
                "total_matches": count
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_locator_by_placeholder(self, text: str, exact: bool = False,
                                              action: str = "find", text_input: str = "",
                                              page_index: int = 0) -> Dict[str, Any]:
        """
        Find elements by their placeholder text.
        
        Args:
            text: Placeholder text to search for
            exact: Whether placeholder text matching should be exact
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Use the placeholder locator
            locator = page.get_by_placeholder(text, exact=exact)
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with placeholder: {text}"
                }
            
            # Get properties of the first element
            first_element = locator.first
            tag_name = await first_element.evaluate("el => el.tagName.toLowerCase()")
            input_type = await first_element.evaluate("el => el.type || ''")
            is_visible = await first_element.is_visible()
            
            # Perform requested action
            action_result = None
            if action == "click":
                await first_element.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await first_element.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements with placeholder: {text}",
                "first_element": {
                    "tag": tag_name,
                    "type": input_type,
                    "is_visible": is_visible,
                    "placeholder": text
                },
                "action_performed": action_result,
                "total_matches": count
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_locator_by_alt_text(self, text: str, exact: bool = False,
                                           action: str = "find",
                                           page_index: int = 0) -> Dict[str, Any]:
        """
        Find elements like images by their alt text.
        
        Args:
            text: Alt text to search for
            exact: Whether alt text matching should be exact
            action: Action to perform ('find', 'click')
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Use the alt text locator
            locator = page.get_by_alt_text(text, exact=exact)
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with alt text: {text}"
                }
            
            # Get properties of the first element
            first_element = locator.first
            tag_name = await first_element.evaluate("el => el.tagName.toLowerCase()")
            is_visible = await first_element.is_visible()
            
            # Perform requested action
            action_result = None
            if action == "click":
                await first_element.click()
                action_result = "Clicked element"
            
            # Take a screenshot of the element for debugging
            screenshot_path = None
            if is_visible:
                try:
                    # Highlight the element with a red border
                    await page.evaluate("""(selector) => {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            el.style.border = '2px solid red';
                        }
                    }""", first_element.evaluate("el => CSS.escape(el.outerHTML)"))
                    
                    screenshot_path = f"vision_locator_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path)
                    
                    # Remove the highlight
                    await page.evaluate("""(selector) => {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            el.style.border = '';
                        }
                    }""", first_element.evaluate("el => CSS.escape(el.outerHTML)"))
                except Exception:
                    # If highlighting fails, just continue
                    pass
            
            return {
                "status": "success",
                "message": f"Found element with text '{text}' using alt text locator",
                "method_used": "alt_text_locator",
                "element_count": count,
                "is_visible": is_visible,
                "action_performed": action_result,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_locator_by_title(self, text: str, exact: bool = False,
                                        action: str = "find", text_input: str = "",
                                        page_index: int = 0) -> Dict[str, Any]:
        """
        Find elements by their title attribute.
        
        Args:
            text: Title text to search for
            exact: Whether title text matching should be exact
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Use the title locator
            locator = page.get_by_title(text, exact=exact)
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with title: {text}"
                }
            
            # Get properties of the first element
            first_element = locator.first
            tag_name = await first_element.evaluate("el => el.tagName.toLowerCase()")
            is_visible = await first_element.is_visible()
            
            # Perform requested action
            action_result = None
            if action == "click":
                await first_element.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await first_element.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements with title: {text}",
                "first_element": {
                    "tag": tag_name,
                    "is_visible": is_visible,
                    "title": text
                },
                "action_performed": action_result,
                "total_matches": count
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_css_text_selector(self, selector: str, text: str = None, 
                                         has_text: bool = False, text_is: bool = False, 
                                         text_matches: str = None, case_sensitive: bool = False,
                                         action: str = "find", text_input: str = "",
                                         page_index: int = 0) -> Dict[str, Any]:
        """
        Find elements using CSS selectors with text matching capabilities.
        
        Args:
            selector: Base CSS selector
            text: Text to match
            has_text: Whether to use :has-text pseudo-class
            text_is: Whether to use :text-is pseudo-class for exact matching
            text_matches: RegEx pattern for :text-matches pseudo-class
            case_sensitive: Whether text matching should be case sensitive
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Build the CSS selector with text pseudo-classes
            final_selector = selector
            
            if text and has_text:
                final_selector += f":has-text('{text}')"
            elif text and text_is:
                final_selector += f":text-is('{text}')"
            elif text_matches:
                flags = "i" if not case_sensitive else ""
                final_selector += f":text-matches('{text_matches}', '{flags}')"
            elif text:
                final_selector += f":text('{text}')"
            
            # Create locator with the final selector
            locator = page.locator(f"css={final_selector}")
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with selector: {final_selector}"
                }
            
            # Collect info about all elements (up to 5)
            for i in range(min(count, 5)):
                el = locator.nth(i)
                is_visible = await el.is_visible()
                
                try:
                    tag_name = await el.evaluate("el => el.tagName.toLowerCase()")
                    text_content = await el.text_content() or ""
                    text_content = text_content.strip()[:50] + ("..." if len(text_content) > 50 else "")
                except Exception:
                    tag_name = "unknown"
                    text_content = ""
                
                # Log or process each element's info as needed
                print(f"Found element {i}: {tag_name}, visible: {is_visible}, text: {text_content}")
            
            # Perform the requested action on the first element
            action_result = None
            if action == "click":
                await locator.first.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await locator.first.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements matching selector: {final_selector}",
                "action_performed": action_result,
                "selector_used": final_selector
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_css_visibility_selector(self, selector: str, visible_only: bool = True,
                                              action: str = "find", text_input: str = "",
                                              page_index: int = 0) -> Dict[str, Any]:
        """
        Find elements using CSS selectors with visibility filtering.
        
        Args:
            selector: Base CSS selector
            visible_only: Whether to only match visible elements
            action: Action to perform ('find', 'click', 'fill')
            text_input: Text to input if action is 'fill'
            page_index: Index of the page to operate on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Add :visible pseudo-class if requested
            final_selector = selector
            if visible_only:
                if ":" in final_selector and not final_selector.endswith(":"):
                    final_selector += ":visible"
                else:
                    final_selector += ":visible"
            
            # Create locator with the final selector
            locator = page.locator(f"css={final_selector}")
            
            # Check if element exists
            count = await locator.count()
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with selector: {final_selector}"
                }
            
            # Collect info about all elements (up to 5)
            for i in range(min(count, 5)):
                el = locator.nth(i)
                is_visible = await el.is_visible()
                
                try:
                    tag_name = await el.evaluate("el => el.tagName.toLowerCase()")
                    text_content = await el.text_content() or ""
                    text_content = text_content.strip()[:50] + ("..." if len(text_content) > 50 else "")
                except Exception:
                    tag_name = "unknown"
                    text_content = ""
                
                # Log or process each element's info as needed
                print(f"Found element {i}: {tag_name}, visible: {is_visible}, text: {text_content}")
            
            # Perform the requested action on the first element
            action_result = None
            if action == "click":
                await locator.first.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await locator.first.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements matching selector: {final_selector}",
                "action_performed": action_result,
                "selector_used": final_selector
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === ARIA Accessibility Snapshot Methods ===
    
    async def playwright_accessibility_snapshot(self, root_selector: str = None, 
                                              interesting_only: bool = True, 
                                              page_index: int = 0) -> Dict[str, Any]:
        """
        Get a snapshot of the ARIA accessibility tree for the page or specific element.
        
        Args:
            root_selector: Optional selector to get snapshot for specific element subtree
            interesting_only: Whether to include only elements with interesting accessibility properties
            page_index: Index of the page to snapshot
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Configure snapshot options
            options = {
                "interestingOnly": interesting_only
            }
            
            # Get root element if specified
            root = None
            if root_selector:
                root = await page.query_selector(root_selector)
                if not root:
                    return {
                        "status": "error",
                        "message": f"Root element not found: {root_selector}"
                    }
                options["root"] = root
            
            # Capture the accessibility snapshot
            snapshot = await page.accessibility.snapshot(**options)
            
            # Process the snapshot to make it more useful
            def process_node(node, depth=0):
                # Base info all nodes should have
                processed = {
                    "role": node.get("role", ""),
                    "name": node.get("name", ""),
                    "depth": depth
                }
                
                # Add optional properties if they exist
                for prop in ["value", "description", "checked", "pressed", "level", 
                             "selected", "expanded", "focused", "disabled"]:
                    if prop in node:
                        processed[prop] = node[prop]
                
                # Process children recursively
                if "children" in node and node["children"]:
                    processed["children"] = [
                        process_node(child, depth + 1) 
                        for child in node["children"]
                    ]
                
                return processed
            
            processed_snapshot = []
            if snapshot:
                if isinstance(snapshot, list):
                    processed_snapshot = [process_node(node) for node in snapshot]
                else:
                    processed_snapshot = process_node(snapshot)
            
            return {
                "status": "success",
                "message": "Accessibility snapshot captured",
                "snapshot": processed_snapshot,
                "root_selector": root_selector,
                "interesting_only": interesting_only
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_find_by_role_in_accessibility_tree(self, role: str, 
                                                          name: str = None, 
                                                          page_index: int = 0) -> Dict[str, Any]:
        """
        Find elements by their role in the accessibility tree.
        
        Args:
            role: ARIA role to search for (e.g., "button", "link", "heading")
            name: Optional accessible name to filter by
            page_index: Index of the page to search
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Get the accessibility snapshot
            snapshot = await page.accessibility.snapshot()
            
            # Function to find nodes matching criteria
            def find_matching_nodes(node, matches=None, path=None):
                if matches is None:
                    matches = []
                if path is None:
                    path = []
                
                current_path = path + [node.get("name", "")]
                
                # Check if current node matches criteria
                if node.get("role") == role:
                    if name is None or node.get("name") == name:
                        matches.append({
                            "node": node,
                            "path": " > ".join(filter(None, current_path))
                        })
                
                # Recursively check children
                if "children" in node and node["children"]:
                    for child in node["children"]:
                        find_matching_nodes(child, matches, current_path)
            
            # Find all matching nodes
            if isinstance(snapshot, list):
                matches = []
                for root_node in snapshot:
                    matches.extend(find_matching_nodes(root_node))
            else:
                matches = find_matching_nodes(snapshot)
            
            if not matches:
                name_part = f" with name '{name}'" if name else ""
                return {
                    "status": "error",
                    "message": f"No elements found with role '{role}'{name_part} in the accessibility tree"
                }
            
            # Extract detailed info about each match
            match_info = []
            for match in matches:
                node = match["node"]
                info = {
                    "role": node.get("role"),
                    "name": node.get("name"),
                    "path": match["path"]
                }
                
                # Add additional properties if they exist
                for prop in ["value", "description", "checked", "pressed", "level"]:
                    if prop in node:
                        info[prop] = node[prop]
                
                match_info.append(info)
            
            name_part = f" with name '{name}'" if name else ""
            return {
                "status": "success",
                "message": f"Found {len(matches)} elements with role '{role}'{name_part} in the accessibility tree",
                "matches": match_info
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # === Enhanced Navigation Methods ===
    
    async def playwright_navigate_and_wait_for_url(self, url: str, expected_url: str, 
                                                 timeout_ms: int = 30000, 
                                                 page_index: int = 0) -> Dict[str, Any]:
        """
        Navigate to a URL and wait for the page to navigate to an expected URL.
        Useful for handling redirects or multi-step navigation flows.
        
        Args:
            url: Initial URL to navigate to
            expected_url: URL pattern to wait for after navigation
            timeout_ms: Timeout in milliseconds
            page_index: Index of the page to navigate
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Make sure URLs have http/https prefix
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Start navigation and wait for the expected URL
            print(f"Navigating to {url} and waiting for URL pattern: {expected_url}")
            
            # Create a promise that will resolve when the URL changes to the expected one
            async with page.expect_navigation(url=expected_url, timeout=timeout_ms) as navigation_info:
                # Perform the initial navigation
                await page.goto(url)
            
            # Wait for the navigation to complete
            response = await navigation_info.value
            
            # Get page information after navigation
            final_url = page.url
            title = await page.title()
            status = response.status if response else None
            
            return {
                "status": "success",
                "message": f"Navigated to {url} and reached expected URL: {final_url}",
                "initial_url": url,
                "final_url": final_url,
                "title": title,
                "response_status": status
            }
        
        except PlaywrightTimeoutError:
            current_url = page.url
            return {
                "status": "error",
                "message": f"Timeout waiting for URL pattern: {expected_url}",
                "initial_url": url,
                "current_url": current_url,
                "timeout_ms": timeout_ms
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_wait_for_navigation(self, trigger_action: str, selector: str = None,
                                           text_input: str = None, wait_until: str = "load",
                                           timeout_ms: int = 30000, page_index: int = 0) -> Dict[str, Any]:
        """
        Perform an action that triggers navigation and wait for it to complete.
        
        Args:
            trigger_action: Action to perform ('click', 'fill_and_press', 'go_back', 'go_forward')
            selector: Element selector for click or fill actions
            text_input: Text to input for fill_and_press action
            wait_until: When to consider navigation complete ('load', 'domcontentloaded', 'networkidle')
            timeout_ms: Timeout in milliseconds
            page_index: Index of the page to navigate
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Record starting URL
            start_url = page.url
            
            # Configure navigation options
            navigation_options = {
                "waitUntil": wait_until,
                "timeout": timeout_ms
            }
            
            print(f"Waiting for navigation after {trigger_action} action")
            
            # Set up navigation waiter
            async with page.expect_navigation(**navigation_options) as navigation_info:
                # Perform the requested action to trigger navigation
                if trigger_action == "click" and selector:
                    await page.click(selector)
                    print(f"Clicked on {selector}")
                elif trigger_action == "fill_and_press" and selector and text_input:
                    await page.fill(selector, text_input)
                    await page.press(selector, "Enter")
                    print(f"Filled {selector} with '{text_input}' and pressed Enter")
                elif trigger_action == "go_back":
                    await page.go_back()
                    print("Navigated back")
                elif trigger_action == "go_forward":
                    await page.go_forward()
                    print("Navigated forward")
                else:
                    return {
                        "status": "error",
                        "message": f"Unsupported trigger_action: {trigger_action}"
                    }
            
            # Wait for navigation to complete
            response = await navigation_info.value
            
            # Get page information after navigation
            end_url = page.url
            title = await page.title()
            status = response.status if response else None
            
            return {
                "status": "success",
                "message": f"Navigation completed after {trigger_action} action",
                "start_url": start_url,
                "end_url": end_url,
                "title": title,
                "response_status": status,
                "trigger_action": trigger_action
            }
            
        except PlaywrightTimeoutError:
            current_url = page.url
            return {
                "status": "error",
                "message": f"Timeout waiting for navigation after {trigger_action} action",
                "start_url": start_url,
                "current_url": current_url,
                "timeout_ms": timeout_ms
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_wait_for_load_state_multiple(self, states: List[str], 
                                                    timeout_ms: int = 30000, 
                                                    page_index: int = 0) -> Dict[str, Any]:
        """
        Wait for multiple load states on the page in sequence.
        
        Args:
            states: List of load states to wait for in sequence ('load', 'domcontentloaded', 'networkidle')
            timeout_ms: Timeout in milliseconds
            page_index: Index of the page to wait on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        # Default states if none provided
        if not states:
            states = ["domcontentloaded", "load", "networkidle"]
        
        # Track timings for each state
        timings = {}
        errors = {}
        
        try:
            start_time = time.time()
            
            # Wait for each state in sequence
            for state in states:
                try:
                    print(f"Waiting for load state: {state}")
                    await page.wait_for_load_state(state, timeout=timeout_ms)
                    timings[state] = time.time() - start_time
                except Exception as e:
                    errors[state] = str(e)
            
            # Get timing information from browser
            perf_timing = await page.evaluate("""() => {
                const nav = performance.getEntriesByType('navigation')[0];
                return nav ? {
                    navigationStart: 0,
                    fetchStart: nav.fetchStart,
                    domContentLoaded: nav.domContentLoadedEventEnd,
                    loadEvent: nav.loadEventEnd,
                    networkIdle: performance.now()  // Estimate
                } : null;
            }""")
            
            return {
                "status": "success" if not errors else "partial_success",
                "message": f"Waited for load states: {', '.join(states)}",
                "url": page.url,
                "timings": timings,
                "errors": errors,
                "performance_timing": perf_timing
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_intercept_requests(self, url_pattern: str, action: str = "abort",
                                          page_index: int = 0) -> Dict[str, Any]:
        """
        Intercept network requests for advanced navigation control.
        
        Args:
            url_pattern: URL pattern to intercept (string, regex, or predicate)
            action: Action to take ('abort', 'continue', 'fulfill')
            page_index: Index of the page to intercept requests on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Set up the route
            async def route_handler(route, request):
                if action == "abort":
                    await route.abort()
                elif action == "continue":
                    await route.continue_()
                elif action == "fulfill":
                    await route.fulfill(
                        status=200,
                        body="Intercepted by Playwright Tools",
                        headers={"content-type": "text/plain"}
                    )
            
            # Register the route handler
            await page.route(url_pattern, route_handler)
            
            return {
                "status": "success",
                "message": f"Set up request interception for URL pattern: {url_pattern}",
                "action": action
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def playwright_stop_intercepting_requests(self, url_pattern: str = "**/*",
                                                  page_index: int = 0) -> Dict[str, Any]:
        """
        Stop intercepting network requests.
        
        Args:
            url_pattern: URL pattern to stop intercepting (default is all requests)
            page_index: Index of the page to stop interception on
        """
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            # Unregister all routes matching the pattern
            await page.unroute(url_pattern)
            
            return {
                "status": "success",
                "message": f"Stopped request interception for URL pattern: {url_pattern}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

