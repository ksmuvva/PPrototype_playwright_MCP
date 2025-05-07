#!/usr/bin/env python3
"""
Modified test script to check all available tools in the MCP Server
"""
import asyncio
import os
import json
import inspect
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_all_tools")

# Import the required classes directly to avoid module import issues
import sys
import os

# Add the current directory to path so we can import from expiremental-new.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now we need to directly load the classes from expiremental-new.py
script_path = os.path.join(current_dir, "expiremental-new.py")

# Load the script content and execute it in the current namespace
with open(script_path, 'r', encoding='utf-8') as f:
    exec(f.read())

# PlaywrightMCPServer and MCPClient classes should now be available

async def main():
    print("\n🔍 TESTING ALL AVAILABLE TOOLS IN PLAYWRIGHT MCP SERVER")
    
    # Create and start server
    print("\n1. Starting server...")
    server = PlaywrightMCPServer()
    success = await server.start()
    
    if not success:
        print("❌ Failed to start server")
        return
        
    print("✅ Server started successfully")
    
    # Get all available tool methods from PlaywrightTools
    print("\n2. Available methods in PlaywrightTools instance:")
    tools_instance = server.tools_instance
    playwright_methods = [name for name in dir(tools_instance) 
                          if callable(getattr(tools_instance, name)) 
                          and name.startswith('playwright_')]
    
    print(f"Found {len(playwright_methods)} playwright_* methods in PlaywrightTools instance:")
    for method in sorted(playwright_methods):
        print(f"  - {method}")
    
    # Get all tools registered in the server
    print("\n3. Tools registered with MCP Server:")
    if server.server and hasattr(server.server, 'tools'):
        server_tools = server.server.tools
        print(f"Found {len(server_tools)} tools registered in MCP Server:")
        for tool in server_tools:
            print(f"  - {tool.name}")
    else:
        print("❌ No tools found in MCP Server")
    
    # Cleanup
    print("\n4. Stopping server...")
    await server.stop()
    print("✅ Server stopped")
    
    print("\n🔍 TESTING COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())
