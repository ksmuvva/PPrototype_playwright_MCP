import asyncio
from exp_tools import PlaywrightTools
from playwright_function_patches import apply_patches

async def test():
    tools = PlaywrightTools()
    await tools.initialize()
    
    # Apply our patches
    apply_patches(tools)
    
    # Navigate to a simple page
    await tools.playwright_navigate('https://example.com')
    
    # Test with a script that would cause an illegal return statement
    result = await tools.playwright_evaluate('return document.title')
    print(f'Result: {result}')
    
    # Cleanup
    await tools.cleanup()

# Run the test
asyncio.run(test())
