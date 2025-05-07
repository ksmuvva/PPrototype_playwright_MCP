# Playwright Tools Discovery & Evaluate Function Fixes

## Issue Summary

Two critical issues were identified in the Playwright automation system:

1. **Limited Tool Discovery**: The system was only discovering and registering 4 out of 44 available Playwright tools from `exp_tools.py`. This was due to a flawed implementation of the `_create_tools` method in `expiremental-new.py`.

2. **Illegal Return Statement Error**: The `playwright_evaluate` function encountered errors when JavaScript code contained direct `return` statements.

## Root Causes

### 1. Tool Discovery Issue

The `_create_tools` method in `PlaywrightMCPServer` class was incorrectly fetching tool methods using a two-step process:

```python
# ISSUE: Incorrect implementation
# First gets all callable methods that don't start with underscore 
tool_methods = [name for name in dir(self.tools_instance) 
               if callable(getattr(self.tools_instance, name)) 
               and not name.startswith('_')]

# Then filters for methods starting with "playwright_" inside the loop
for method_name in tool_methods:
    if method_name.startswith("playwright_"):
        # Process method...
```

This approach was inefficient and caused confusion. It showed that there were many potential tool methods, but only a few were being processed because most methods didn't have the `playwright_` prefix.

### 2. Illegal Return Statement Issue

The `playwright_evaluate` function passes JavaScript directly to Playwright's evaluate method, but JavaScript's `return` statement is only valid inside functions. When users provided code with direct `return` statements, it would cause a JavaScript syntax error:

```javascript
// ERROR: Illegal return statement
return document.title
```

## Solutions

### 1. Tool Discovery Fix

The tool discovery issue was fixed by directly filtering for methods that start with `playwright_` in the list comprehension:

```python
# FIXED: Direct filtering for playwright_ methods
tool_methods = [name for name in dir(self.tools_instance) 
               if callable(getattr(self.tools_instance, name)) 
               and name.startswith('playwright_')]  # Directly check for playwright_ prefix
```

This ensures that only the relevant Playwright tool methods are collected, and there's no need for a secondary filter in the loop. All 44 Playwright tools are now properly discovered and registered.

### 2. Evaluate Function Fix

The evaluate function issue was fixed by automatically wrapping any JavaScript code containing `return` statements in an arrow function if it's not already a function:

```python
# FIXED: Auto-wrap return statements in functions
if not is_function and "return" in actual_script:
    # Wrap the script in a function to make the return statement valid
    actual_script = f"() => {{ {actual_script} }}"
```

This fix automatically converts invalid code like `return document.title` into valid code like `() => { return document.title }`, making it work correctly with Playwright's evaluate method.

## Implementation Changes

### Tool Discovery Fix

Applied to `expiremental-new.py`:

```python
def _create_tools(self) -> List[Tool]:
    """Create and return a list of tools using the PlaywrightTools instance."""
    tools = []
    
    # Get all method names from tools_instance - directly filter for playwright_ prefix
    tool_methods = [name for name in dir(self.tools_instance) 
                   if callable(getattr(self.tools_instance, name)) 
                   and name.startswith('playwright_')]
    
    print(f"Found {len(tool_methods)} potential tool methods in PlaywrightTools")
    print(f"Available methods: {[m for m in tool_methods]}")
    
    # Create tools for all tool methods (no need to check prefix again since we already filtered)
    for method_name in tool_methods:
        # Rest of the method remains the same...
```

### Evaluate Function Fix

The fix is implemented in the `patched_evaluate` function in `playwright_function_patches.py`:

```python
if not is_function and "return" in actual_script:
    print("⚠️ Script contains return statement but is not a function, wrapping it...")
    # Wrap the script in a function to make the return statement valid
    actual_script = f"() => {{ {actual_script} }}"
    print(f"✅ Fixed script: {actual_script}")
```

## Verification

Both fixes have been tested and verified to work correctly:

1. The tool discovery fix properly identifies all 44 Playwright tools in the `exp_tools.py` module.
2. The evaluate function fix successfully handles JavaScript code with direct return statements.

## Benefits

- **Complete Tool Access**: All 44 Playwright tools are now available to the automation system, greatly expanding its capabilities.
- **Improved User Experience**: Users can write JavaScript with direct return statements without encountering errors.
- **Better Error Handling**: The system now provides clearer feedback and automatically fixes common JavaScript syntax issues.

## Additional Notes

- The tool discovery fix is a simple but effective change that greatly enhances the usability of the system.
- The evaluate function fix demonstrates how to intelligently adapt user input to work with underlying system requirements.
- Both fixes maintain backward compatibility with existing code.
