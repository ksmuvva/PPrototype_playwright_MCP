#!/usr/bin/env python3
import asyncio
import logging
from exp_tools import PlaywrightTools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_simplified")

async def test_simplified():
    """A simplified test of the PlaywrightTools that handles potential timing issues"""
    logger.info("Initializing PlaywrightTools")
    tools = PlaywrightTools()
    
    try:
        # Initialize Playwright
        logger.info("Initializing Playwright")
        await tools.initialize()
        
        # First test basic navigation
        logger.info("Testing navigation to example.com")
        await tools.playwright_navigate(
            url="https://example.com",
            wait_for_load=True
        )
        
        # Wait a moment to ensure page is fully loaded
        await asyncio.sleep(1)
        
        # Get page title to verify page loaded correctly
        logger.info("Getting page title")
        js_result = await tools.playwright_evaluate("() => document.title")
        logger.info(f"Page title: {js_result.get('result', 'Unknown')}")
        
        # Test taking a screenshot
        logger.info("Taking screenshot")
        screenshot_result = await tools.playwright_screenshot(
            filename="example_screenshot.png", 
            page_index=0,
            full_page=False
        )
        logger.info(f"Screenshot result: {screenshot_result.get('status')}")
        if screenshot_result.get('status') == 'success':
            logger.info(f"Screenshot saved to: {screenshot_result.get('filename')}")
        else:
            logger.error(f"Screenshot error: {screenshot_result.get('message')}")
        
        # Test getting text content
        logger.info("Getting page text")
        text_result = await tools.playwright_get_visible_text("body")
        if text_result.get("status") == "success":
            text = text_result.get("text", "")
            logger.info(f"Page text snippet: {text[:50]}...")
        else:
            logger.warning(f"Failed to get text: {text_result}")
        
        # Test simple code generation session
        logger.info("Testing code generation session")
        session_result = await tools.start_codegen_session(
            session_name="test_session",
            language="python"
        )
        logger.info(f"Session created: {session_result.get('status')}")
        
        # Clean up
        logger.info("Cleaning up resources")
        await tools.cleanup()
        
        return True
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        # Try to clean up even if there was an error
        try:
            await tools.cleanup()
        except Exception as cleanup_error:
            logger.error(f"Cleanup error: {cleanup_error}")
        return False

if __name__ == "__main__":
    logger.info("Starting simplified test")
    success = asyncio.run(test_simplified())
    logger.info(f"Test {'passed' if success else 'failed'}") 