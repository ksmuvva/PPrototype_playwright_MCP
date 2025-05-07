#!/usr/bin/env python3
"""
Verify that the fixes to playwright_function_patches.py have resolved the tool discovery issue
"""
import asyncio
import sys
import os

async def main():
    print("\n🔍 Verifying PlaywrightTools Tool Discovery Fix")
    print("==============================================")
    
    # Fix relative imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import from expiremental-new.py
    from expiremental_new import PlaywrightMCPServer
    
    # Create server instance
    server = PlaywrightMCPServer()
    
    # Start the server (this will initialize the tools and apply patches)
    print("\n1. Starting server to initialize and apply patches...")
    await server.start()
    
    # Check how many tools were discovered
    print("\n2. Checking tool discovery results...")
    tools = server._create_tools()
    
    print(f"\nTool discovery complete! Found {len(tools)} tools.")
    print("\nFirst 10 discovered tools:")
    for i, tool in enumerate(tools[:10]):
        print(f"  {i+1}. {tool.name}")
    
    print("\n✅ Verification complete. If more than 4 tools were found, the fix was successful!")

if __name__ == "__main__":
    asyncio.run(main())
