"""
Parameter Adaptation Module for Playwright Tools

This module provides standalone functions for adapting parameters between what the
LLM might send and what the actual implementation expects. It fixes two issues:

1. When LLM sends 'selector' to playwright_smart_click instead of 'text'
2. When LLM doesn't provide 'filename' to playwright_screenshot

Usage:
    from param_adapter import adapt_smart_click, adapt_screenshot

    # For playwright_smart_click with selector parameter
    result = await adapt_smart_click(original_func, selector="a:has-text('Click me')")

    # For playwright_screenshot without filename
    result = await adapt_screenshot(original_func)
"""
import re
import time
import os
from typing import Any, Dict, Optional, Callable

async def adapt_smart_click(original_func: Callable, **kwargs) -> Dict[str, Any]:
    """
    Adapts parameters for playwright_smart_click to handle selector parameter.
    
    Args:
        original_func: The original playwright_smart_click function
        **kwargs: Parameters from the LLM
        
    Returns:
        Result from the original function
    """
    # If selector is provided but text is not, extract text from selector
    if 'selector' in kwargs and 'text' not in kwargs:
        selector = kwargs.pop('selector')
        text = None
        
        # Extract text from common selector patterns
        
        # Pattern: :has-text('Text')
        has_text_match = re.search(r":has-text\('([^']+)'\)", selector)
        if has_text_match:
            text = has_text_match.group(1)
        
        # Pattern: :text("Text")
        elif ":text(" in selector:
            text_match = re.search(r":text\(['\"]([^'\"]+)['\"]\)", selector)
            if text_match:
                text = text_match.group(1)
                
        # Pattern: [aria-label="Text"]
        elif "aria-label" in selector:
            label_match = re.search(r"\[aria-label=['\"]([^'\"]+)['\"]\]", selector)
            if label_match:
                text = label_match.group(1)
                
        # If we couldn't extract text, use the selector as is
        if not text:
            text = selector
        
        print(f"Converting selector parameter to text: '{text}'")
        kwargs['text'] = text
    
    # Call the original function with the adapted parameters
    return await original_func(**kwargs)

async def adapt_screenshot(original_func: Callable, **kwargs) -> Dict[str, Any]:
    """
    Adapts parameters for playwright_screenshot to ensure filename is provided.
    
    Args:
        original_func: The original playwright_screenshot function
        **kwargs: Parameters from the LLM
        
    Returns:
        Result from the original function
    """
    # If filename is not provided, generate a default filename
    if 'filename' not in kwargs:
        default_filename = f"screenshot_{int(time.time())}.png"
        print(f"No filename provided for screenshot, using default: {default_filename}")
        kwargs['filename'] = default_filename
    
    # Ensure filename has .png extension
    if not kwargs['filename'].endswith('.png'):
        kwargs['filename'] += '.png'
    
    # Call the original function with the updated kwargs
    return await original_func(**kwargs)

def apply_adapters(tools_instance: Any) -> None:
    """
    Apply parameter adapters to a PlaywrightTools instance.
    
    Args:
        tools_instance: Instance of PlaywrightTools
    """
    # Store original methods
    original_smart_click = tools_instance.playwright_smart_click
    original_screenshot = tools_instance.playwright_screenshot
    
    # Create wrapped methods with adapters
    async def wrapped_smart_click(**kwargs):
        return await adapt_smart_click(original_smart_click, **kwargs)
    
    async def wrapped_screenshot(**kwargs):
        return await adapt_screenshot(original_screenshot, **kwargs)
    
    # Replace methods with wrapped versions
    tools_instance.playwright_smart_click = wrapped_smart_click
    tools_instance.playwright_screenshot = wrapped_screenshot
    
    print("✅ Parameter adapters applied successfully")
