#!/usr/bin/env python3
"""
This script fixes the tool discovery issue in the expiremental-new.py file.
It ensures that all available Playwright tools are properly registered.
"""
import logging
import os
import asyncio
import traceback
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

def main():
    print("\n🚀 Starting AI-powered browser automation with improved tool discovery...")
    
    try:
        from exp_tools import PlaywrightTools
        print("✅ Successfully imported PlaywrightTools class")
        
        # Create AsyncIO event loop and run the async main function
        asyncio.run(run_with_all_tools())
        
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")
        traceback.print_exc()

async def run_with_all_tools():
    from exp_tools import PlaywrightTools

    # 1. Create and initialize PlaywrightTools
    tools = PlaywrightTools()
    await tools.initialize()
    
    # 2. List all available methods
    playwright_methods = [name for name in dir(tools) 
                         if callable(getattr(tools, name)) 
                         and name.startswith('playwright_')]
    
    print(f"\nFound {len(playwright_methods)} playwright methods in tools:")
    for method in sorted(playwright_methods):
        print(f"  - {method}")
    
    # 3. Make sure you're not using the placeholder implementation
    if len(playwright_methods) <= 6:
        print("\n⚠️ WARNING: You appear to be using the placeholder implementation with limited tools")
        print("Check for import errors with the exp_tools.py file")
    else:
        print(f"\n✅ Using full PlaywrightTools implementation with {len(playwright_methods)} tools")
    
    # 4. Generate a fixed version of the MpcServer class that registers all tools
    from expiremental-new import PlaywrightMCPServer
    
    # Create a server with the tools
    server = PlaywrightMCPServer()
    
    # Override the _create_tools method to ensure all tools are registered
    original_create_tools = server._create_tools
    
    def improved_create_tools(self):
        """Enhanced version of _create_tools that ensures all tools are registered."""
        tools_created = original_create_tools()
        
        if len(tools_created) < 10:
            print(f"\n⚠️ Only {len(tools_created)} tools were registered by the original method.")
            print("Switching to improved tool discovery...")
            
            import inspect
            
            # Get all available tool methods from tools_instance
            all_tools = []
            
            for method_name in dir(self.tools_instance):
                if callable(getattr(self.tools_instance, method_name)) and method_name.startswith('playwright_'):
                    try:
                        # Get the method object
                        method = getattr(self.tools_instance, method_name)
                        
                        # Create parameter dictionary from signature
                        parameters = {}
                        sig = inspect.signature(method)
                        
                        for param_name, param in sig.parameters.items():
                            if param_name == 'self':
                                continue
                                
                            # Determine parameter type
                            param_type = "string"
                            if param.annotation != inspect.Parameter.empty:
                                if param.annotation == int:
                                    param_type = "integer"
                                elif param.annotation == bool:
                                    param_type = "boolean"
                                elif "Dict" in str(param.annotation):
                                    param_type = "object"
                                elif "List" in str(param.annotation):
                                    param_type = "array"
                            
                            # Add parameter definition
                            parameters[param_name] = {
                                "type": param_type,
                                "description": f"Parameter for {method_name}"
                            }
                        
                        # Get description from docstring
                        description = method.__doc__ or f"Tool for {method_name}"
                        description = description.strip().split("\n")[0]  # Get first line
                        
                        # Create tool
                        from mcp.server import create_tool, Tool
                        tool = create_tool(
                            name=method_name,
                            description=description,
                            function=method,
                            parameters=parameters
                        )
                        
                        all_tools.append(tool)
                        print(f"  + Added tool: {method_name}")
                        
                    except Exception as e:
                        print(f"  ❌ Error creating tool for {method_name}: {str(e)}")
            
            print(f"\n✅ Enhanced tool discovery registered {len(all_tools)} tools")
            return all_tools
        else:
            print(f"\n✅ Original method registered {len(tools_created)} tools, which is sufficient")
            return tools_created
    
    # Patch the method
    server._create_tools = improved_create_tools.__get__(server)
    
    # Start the server with the enhanced tool discovery
    await server.start()
    
    print("\n✅ Server started with enhanced tool discovery")
    
    # Wait for user input
    input("\nPress Enter to exit...")
    
    # Cleanup
    await server.stop()
    await tools.cleanup()
    
    print("\n✅ Successfully stopped server and cleaned up resources")

if __name__ == "__main__":
    main()
