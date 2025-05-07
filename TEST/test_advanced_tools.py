#!/usr/bin/env python3
import asyncio
import logging
import os
from exp_tools import PlaywrightTools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_advanced_tools")

async def test_advanced_tools():
    logger.info("Initializing PlaywrightTools")
    tools = PlaywrightTools()
    
    try:
        # Initialize Playwright
        logger.info("Initializing Playwright")
        init_result = await tools.initialize()
        if not init_result:
            logger.error("Failed to initialize Playwright")
            return False
            
        # Test navigation to a more complex site
        logger.info("Testing navigation to a more complex site")
        navigate_result = await tools.playwright_navigate(
            url="https://playwright.dev",
            wait_for_load=True,
            capture_screenshot=True
        )
        
        logger.info(f"Navigation result: {navigate_result.get('status')}")
        
        # Test multi-strategy locate
        logger.info("Testing multi-strategy locate")
        locate_result = await tools.playwright_multi_strategy_locate(
            description="documentation",
            action="click",
            capture_screenshot=True
        )
        
        logger.info(f"Multi-strategy locate result: {locate_result}")
        
        # Test get visible text
        logger.info("Testing get visible text")
        text_result = await tools.playwright_get_visible_text(selector="h1")
        logger.info(f"H1 text: {text_result.get('text', '')}")
        
        # Test finding elements with description
        logger.info("Testing find_element")
        find_result = await tools.playwright_find_element(
            description="button or link containing get started",
            max_results=3
        )
        
        if find_result.get("status") == "success":
            elements = find_result.get("elements", [])
            logger.info(f"Found {len(elements)} elements:")
            for i, element in enumerate(elements):
                logger.info(f"  {i+1}. {element.get('tag')}: {element.get('text')}")
                
            # Try clicking the first element if found
            if elements:
                logger.info("Trying to click the first found element")
                selector = elements[0].get("unique_selector")
                if selector:
                    click_result = await tools.playwright_click(selector=selector)
                    logger.info(f"Click result: {click_result}")
        
        # Test JavaScript evaluation
        logger.info("Testing JavaScript evaluation")
        js_result = await tools.playwright_evaluate(
            script="""() => {
                return { 
                    title: document.title,
                    url: window.location.href,
                    links: Array.from(document.querySelectorAll('a')).length
                }
            }"""
        )
        
        logger.info(f"JavaScript evaluation result: {js_result}")
        
        # Test accessibility locator
        logger.info("Testing accessibility locator")
        a11y_result = await tools.playwright_accessibility_locator(
            description="search",
            action="find"
        )
        
        logger.info(f"Accessibility locator result: {a11y_result}")
        
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
    logger.info("Starting advanced tools test")
    success = asyncio.run(test_advanced_tools())
    logger.info(f"Test {'passed' if success else 'failed'}") 