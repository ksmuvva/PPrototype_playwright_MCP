#!/usr/bin/env python3
import asyncio
import logging
from exp_tools import PlaywrightTools

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_new_features")

async def test_dialog_features():
    """Test dialog handling features."""
    logger.info("Testing dialog handling features")
    tools = PlaywrightTools()
    
    try:
        # Initialize Playwright
        logger.info("Initializing Playwright")
        await tools.initialize()
        
        # Navigate to a test page
        logger.info("Navigating to a page with dialogs")
        await tools.playwright_navigate(
            url="https://the-internet.herokuapp.com/javascript_alerts",
            wait_for_load=True
        )
        
        # Setting up dialog handler to accept alerts
        logger.info("Setting up dialog handler")
        await tools.playwright_handle_dialog(action="accept")
        
        # Click on the alert button and handle dialog
        logger.info("Testing alert dialog")
        alert_result = await tools.playwright_click(
            selector="button:has-text('Click for JS Alert')"
        )
        logger.info(f"Alert dialog handler result: {alert_result}")
        
        # Test prompt dialog
        logger.info("Testing prompt dialog with text input")
        await tools.playwright_handle_dialog(action="accept", prompt_text="Hello from Playwright!")
        prompt_result = await tools.playwright_click(
            selector="button:has-text('Click for JS Prompt')"
        )
        logger.info(f"Prompt dialog handler result: {prompt_result}")
        
        return "Dialog handling tests passed"
        
    except Exception as e:
        logger.error(f"Error testing dialog features: {e}")
        return f"Dialog handling tests failed: {e}"
    finally:
        await tools.cleanup()

async def test_accessibility_features():
    """Test accessibility features."""
    logger.info("Testing accessibility features")
    tools = PlaywrightTools()
    
    try:
        # Initialize Playwright
        logger.info("Initializing Playwright")
        await tools.initialize()
        
        # Navigate to a test page
        logger.info("Navigating to a page with various accessibility elements")
        await tools.playwright_navigate(
            url="https://dequeuniversity.com/demo/mars",
            wait_for_load=True
        )
        
        # Get accessibility snapshot
        logger.info("Getting accessibility snapshot")
        snapshot_result = await tools.playwright_accessibility_snapshot()
        
        if snapshot_result["status"] == "success":
            logger.info("Accessibility snapshot captured successfully")
            # Count number of elements in snapshot to verify it worked
            node_count = count_nodes(snapshot_result["snapshot"])
            logger.info(f"Accessibility tree contains {node_count} nodes")
        else:
            logger.error(f"Failed to capture accessibility snapshot: {snapshot_result}")
        
        # Find elements by role
        logger.info("Finding elements by role")
        buttons = await tools.playwright_find_by_role("button")
        logger.info(f"Found {len(buttons.get('elements', []))} buttons on the page")
        
        return "Accessibility tests passed"
        
    except Exception as e:
        logger.error(f"Error testing accessibility features: {e}")
        return f"Accessibility tests failed: {e}"
    finally:
        await tools.cleanup()

async def test_enhanced_navigation():
    """Test enhanced navigation features."""
    logger.info("Testing enhanced navigation features")
    tools = PlaywrightTools()
    
    try:
        # Initialize Playwright
        logger.info("Initializing Playwright")
        await tools.initialize()
        
        # Test navigate and wait
        logger.info("Testing navigate_and_wait with networkidle")
        nav_result = await tools.playwright_navigate_and_wait(
            url="https://example.com",
            wait_until="networkidle"
        )
        logger.info(f"Navigation result: {nav_result['status']}")
        
        # Test reload page
        logger.info("Testing page reload")
        reload_result = await tools.playwright_reload_page(
            wait_until="networkidle"
        )
        logger.info(f"Reload result: {reload_result['status']}")
        
        # Test wait for load state
        logger.info("Testing wait for load state")
        load_result = await tools.playwright_wait_for_load_state(
            state="networkidle"
        )
        logger.info(f"Load state result: {load_result['status']}")
        
        # Test CSS locator for heading
        logger.info("Testing CSS locator")
        heading = await tools.playwright_css_locator(
            selector="h1",
            action="find"
        )
        
        if heading["status"] == "success" and heading.get("elements"):
            logger.info(f"Found heading: {heading['elements'][0]['text']}")
        
        return "Enhanced navigation tests passed"
        
    except Exception as e:
        logger.error(f"Error testing enhanced navigation features: {e}")
        return f"Enhanced navigation tests failed: {e}"
    finally:
        await tools.cleanup()

def count_nodes(node, count=0):
    """Helper function to count nodes in accessibility tree."""
    count += 1
    if "children" in node and node["children"]:
        for child in node["children"]:
            count = count_nodes(child, count)
    return count

async def main():
    """Run all tests."""
    logger.info("Starting tests for new features")
    
    # Test dialog features
    dialog_result = await test_dialog_features()
    logger.info(f"Dialog tests result: {dialog_result}")
    
    # Test accessibility features
    accessibility_result = await test_accessibility_features()
    logger.info(f"Accessibility tests result: {accessibility_result}")
    
    # Test enhanced navigation
    navigation_result = await test_enhanced_navigation()
    logger.info(f"Navigation tests result: {navigation_result}")
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 