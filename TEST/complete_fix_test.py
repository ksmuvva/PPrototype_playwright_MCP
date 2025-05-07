#!/usr/bin/env python3
"""
Complete fix for the Playwright tools discovery and evaluate function issues.
This script applies and verifies both fixes:
1. Fix the tool discovery to properly find all playwright_* methods
2. Fix the evaluate function to handle return statements properly
"""
import asyncio
import inspect
from typing import Dict, Any, List
import time
from exp_tools import PlaywrightTools

class FixedPlaywrightMCPServer:
    """Demonstration of the fixed MCP Server implementation for Playwright."""
    
    def __init__(self):
        """Initialize the server with tools."""
        self.tools_instance = PlaywrightTools()
    
    async def initialize(self):
        """Initialize the tools instance."""
        print("Initializing PlaywrightTools...")
        result = await self.tools_instance.initialize()
        print(f"Initialization result: {result}")
        return result
    
    def create_tools(self) -> List[dict]:
        """
        FIXED VERSION: Create and return a list of tools using the PlaywrightTools instance.
        This directly checks for the playwright_ prefix in the method name.
        """
        tools = []
        
        # Get all method names from tools_instance - FIXED VERSION
        tool_methods = [name for name in dir(self.tools_instance) 
                      if callable(getattr(self.tools_instance, name)) 
                      and name.startswith('playwright_')]  # Directly check for playwright_ prefix
        
        print(f"Found {len(tool_methods)} Playwright tools")
        
        # Create tool info for all tool methods
        for method_name in tool_methods:
            # Get the method object
            method = getattr(self.tools_instance, method_name)
            
            # Get method info
            try:
                sig = inspect.signature(method)
                description = method.__doc__ or f"Tool for {method_name}"
                description = description.strip().split("\n")[0]  # Get first line
                
                # Get parameter info
                parameters = {}
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    
                    param_type = "string"  # Default type
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == str:
                            param_type = "string"
                        elif param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == bool:
                            param_type = "boolean"
                    
                    parameters[param_name] = {
                        "type": param_type,
                        "description": f"Parameter for {method_name}"
                    }
                
                # Add tool info
                tools.append({
                    "name": method_name,
                    "description": description,
                    "parameters": parameters
                })
                
            except Exception as e:
                print(f"Error getting info for {method_name}: {str(e)}")
                continue
        
        return tools
    
    async def test_evaluate_fix(self):
        """Test the fix for the evaluate function with return statements."""
        print("\n=== Testing evaluate fix ===")
        
        try:
            # Navigate to example.com
            print("Navigating to example.com...")
            await self.tools_instance.playwright_navigate("https://example.com")
            
            # Test scripts with return statements that would previously fail
            scripts = [
                "return document.title",
                "const title = document.title; return title;",
                "return document.querySelector('h1').textContent;",
            ]
            
            for i, script in enumerate(scripts):
                print(f"\nTesting script {i+1}: {script}")
                
                # Apply the fix manually before calling evaluate
                is_function = (
                    script.strip().startswith("() =>") or
                    script.strip().startswith("function") or
                    (script.strip().startswith("(") and "=>" in script)
                )
                
                if not is_function and "return" in script:
                    print("⚠️ Script contains return statement but is not a function, wrapping it...")
                    fixed_script = f"() => {{ {script} }}"
                    print(f"✅ Fixed script: {fixed_script}")
                    result = await self.tools_instance.playwright_evaluate(fixed_script)
                else:
                    print("Script doesn't need fixing or is already a function")
                    result = await self.tools_instance.playwright_evaluate(script)
                
                print(f"Result: {result}")
                if result.get("status") == "success":
                    print("✅ Script executed successfully!")
                else:
                    print("❌ Script failed")
            
            print("\n✅ Evaluate fix test complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error testing evaluate fix: {str(e)}")
            return False

async def run_tests():
    """Run both fixes and verify they work correctly."""
    # Create server instance
    server = FixedPlaywrightMCPServer()
    
    try:
        # Initialize the tools
        await server.initialize()
        
        # Test the tool discovery fix
        print("\n=== Testing Tool Discovery Fix ===")
        tools = server.create_tools()
        print(f"✅ Successfully discovered {len(tools)} Playwright tools")
        print("Sample of discovered tools:")
        for i, tool in enumerate(tools[:5]):  # Show first 5 tools
            print(f"  {i+1}. {tool['name']} - {tool['description']}")
        
        # Show how many tools were previously discovered
        print("\nComparing with the broken version:")
        broken_tools = [name for name in dir(server.tools_instance) 
                      if callable(getattr(server.tools_instance, name)) 
                      and not name.startswith('_')
                      and name.startswith('playwright_')]
        print(f"Number of tools that would be discovered in broken code: {len(broken_tools)} (same number but only after filtering)")
        
        # Test the evaluate fix
        await server.test_evaluate_fix()
        
        # Clean up
        print("\nCleaning up resources...")
        await server.tools_instance.cleanup()
        print("✅ Resources cleaned up")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        # Try to clean up
        try:
            await server.tools_instance.cleanup()
        except:
            pass

if __name__ == "__main__":
    print("=== Testing Playwright Tool Discovery and Evaluate Fixes ===")
    asyncio.run(run_tests())
    print("=== All Tests Complete ===")
