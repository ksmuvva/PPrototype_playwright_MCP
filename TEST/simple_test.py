#!/usr/bin/env python3
import asyncio
from exp_tools import PlaywrightTools

async def main():
    tools = PlaywrightTools()
    try:
        # Initialize
        print("Initializing...")
        await tools.initialize()
        print("Initialization complete")
        
        # Test the smart_click function with a simple example
        print("Testing playwright_smart_click...")
        result = await tools.playwright_navigate("https://example.com")
        print(f"Navigation result: {result}")
        
        result = await tools.playwright_smart_click("More information")
        print(f"Smart click result: {result}")
        
        print("Test complete")
    finally:
        # Cleanup
        print("Cleaning up...")
        await tools.cleanup()
        print("Cleanup complete")

if __name__ == "__main__":
    asyncio.run(main())
