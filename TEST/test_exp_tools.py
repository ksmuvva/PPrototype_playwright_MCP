#!/usr/bin/env python3
import asyncio
import logging
from exp_tools import PlaywrightTools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_exp_tools")

async def test_playwright_tools():
    logger.info("Initializing PlaywrightTools")
    tools = PlaywrightTools()
    
    try:
        # Initialize Playwright
        logger.info("Initializing Playwright")
        init_result = await tools.initialize()
        if not init_result:
            logger.error("Failed to initialize Playwright")
            return False
        
        # First, try to navigate to a website
        logger.info("Testing playwright_navigate")
        navigate_result = await tools.playwright_navigate(
            url="https://example.com",
            wait_for_load=True,
            capture_screenshot=True
        )
        
        logger.info(f"Navigation result: {navigate_result}")
        
        if navigate_result.get("status") != "success":
            logger.error("Navigation failed")
            return False
        
        # Try to take a screenshot
        logger.info("Testing playwright_screenshot")
        screenshot_result = await tools.playwright_screenshot(
            filename="test_screenshot.png"
        )
        
        logger.info(f"Screenshot result: {screenshot_result}")
        
        # Try to get page text
        logger.info("Testing playwright_get_visible_text")
        text_result = await tools.playwright_get_visible_text()
        
        logger.info(f"Got page text: {text_result.get('text', '')[:100]}...")
        
        # Try smart click on a link
        logger.info("Testing playwright_smart_click")
        click_result = await tools.playwright_smart_click(
            text="More information",
            element_type="link",
            capture_screenshot=True
        )
        
        logger.info(f"Smart click result: {click_result}")
        
        # Finally, clean up
        logger.info("Cleaning up")
        await tools.cleanup()
        
        logger.info("All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        # Try to clean up even if there was an error
        try:
            await tools.cleanup()
        except Exception:
            pass
        return False

if __name__ == "__main__":
    logger.info("Starting exp_tools test")
    success = asyncio.run(test_playwright_tools())
    logger.info(f"Test {'passed' if success else 'failed'}") 