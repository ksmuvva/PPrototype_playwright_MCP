#!/usr/bin/env python3
"""
Simple script to check if all tools are discovered and registered correctly
"""
import asyncio
import logging
import os
import inspect
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_tools")

# Import the PlaywrightTools class directly
from exp_tools import PlaywrightTools

class SimpleToolRegistry:
    """A simple class to mimic tool registration behavior"""
    def __init__(self):
        self.registered_tools = []
    
    def register_tool(self, name, description, function, parameters=None):
        self.registered_tools.append({
            "name": name,
            "description": description,
            "function": function.__name__ if function else "None",
            "parameters": parameters or {}
        })
        return function  # Return the function as create_tool would

async def main():
    print("\n🔍 CHECKING TOOL DISCOVERY AND REGISTRATION")
    
    # Create PlaywrightTools instance
    print("\n1. Creating PlaywrightTools instance...")
    tools = PlaywrightTools()
    
    # Initialize the tools
    print("\n2. Initializing tools...")
    try:
        success = await tools.initialize()
        print(f"Initialization {'successful' if success else 'failed'}")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
    
    # Get all tool methods
    print("\n3. Finding all potential tool methods...")
    
    # Method 1: Using startswith('playwright_')
    playwright_methods1 = [name for name in dir(tools) 
                         if callable(getattr(tools, name)) 
                         and name.startswith('playwright_')]
    
    print(f"Found {len(playwright_methods1)} methods using startswith('playwright_'):")
    for method in sorted(playwright_methods1):
        print(f"  - {method}")
    
    # Create a tool registry and simulate tool creation
    print("\n4. Simulating tool registration...")
    registry = SimpleToolRegistry()
    
    # Register all methods as tools (similar to what happens in PlaywrightMCPServer._create_tools)
    for method_name in dir(tools):
        if callable(getattr(tools, method_name)) and method_name.startswith('playwright_'):
            method = getattr(tools, method_name)
            
            # Get parameter info from type hints and docstring
            parameters = {}
            try:
                sig = inspect.signature(method)
                
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                        
                    param_type = "string"  # Default type
                    
                    # Try to determine parameter type from annotation
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == str:
                            param_type = "string"
                        elif param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == bool:
                            param_type = "boolean"
                        elif param.annotation == dict or "Dict" in str(param.annotation):
                            param_type = "object"
                        elif param.annotation == list or "List" in str(param.annotation):
                            param_type = "array"
                    
                    # Add parameter definition
                    parameters[param_name] = {
                        "type": param_type,
                        "description": f"Parameter for {method_name}"
                    }
                
                # Extract description from docstring
                description = method.__doc__ or f"Tool for {method_name}"
                if description:
                    description = description.strip().split("\n")[0]  # Get first line
                else:
                    description = f"Tool for {method_name}"
                
                # Register the tool
                registry.register_tool(
                    name=method_name,
                    description=description,
                    function=method,
                    parameters=parameters
                )
                
                print(f"  ✅ Registered tool: {method_name}")
            except Exception as e:
                print(f"  ❌ Failed to register tool {method_name}: {e}")
    
    print(f"\nSuccessfully registered {len(registry.registered_tools)} tools")
    
    # Cleanup
    print("\n5. Cleaning up...")
    await tools.cleanup()
    print("Cleanup complete")
    
    print("\n🔍 INVESTIGATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())
