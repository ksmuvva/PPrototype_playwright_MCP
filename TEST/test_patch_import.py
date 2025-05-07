#!/usr/bin/env python3
"""
Test if the playwright_function_patches module can be imported after the fix
"""

print("Testing if playwright_function_patches can be imported...")

try:
    from playwright_function_patches import apply_patches
    print("✅ Successfully imported apply_patches from playwright_function_patches")
    
    # Create a dummy class to test the patch function
    class DummyTools:
        async def playwright_evaluate(self, script, arg=None):
            pass
            
    # Try to apply patches
    dummy = DummyTools()
    apply_patches(dummy)
    print("✅ Successfully applied patches to dummy class")
    
except Exception as e:
    print(f"❌ Error importing or using apply_patches: {e}")
    import traceback
    traceback.print_exc()
