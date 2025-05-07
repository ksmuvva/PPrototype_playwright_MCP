"""
Adapter module for Playwright functions.

This module provides adapter functions to handle parameter mismatches
between AI-generated function calls and the actual implementations.
"""
from typing import Any, Dict, Optional

async def adapt_smart_click(original_func, **kwargs):
    """
    Adapter for the playwright_smart_click function.
    
    Handles parameter mismatches between what the LLM might send (like 'selector')
    and what the actual function expects (like 'text').
    
    Args:
        original_func: The original playwright_smart_click function to call
        **kwargs: The keyword arguments received from the LLM
    
    Returns:
        The result from the original function call
    """
    # If selector is provided but text is not, extract text from selector
    if 'selector' in kwargs and 'text' not in kwargs:
        # Extract text content from the selector if possible
        selector = kwargs.pop('selector')
        
        # Try to extract text from different selector formats
        text = None
        
        # Format: a:has-text('Text Here')
        import re
        has_text_match = re.search(r":has-text\('([^']+)'\)", selector)
        if has_text_match:
            text = has_text_match.group(1)
        
        # Format: button:text("Text Here")
        elif ":text(" in selector:
            text_match = re.search(r":text\(['\"]([^'\"]+)['\"]\)", selector)
            if text_match:
                text = text_match.group(1)
                
        # Format: [aria-label="Text Here"]
        elif "aria-label" in selector:
            label_match = re.search(r"\[aria-label=['\"]([^'\"]+)['\"]\]", selector)
            if label_match:
                text = label_match.group(1)
                
        # If we couldn't extract text, use the selector as is
        if not text:
            text = selector
            
        # Call original function with extracted text
        return await original_func(text=text, **kwargs)
    else:
        # If text is already provided, just use it
        return await original_func(**kwargs)

async def adapt_screenshot(original_func, **kwargs):
    """
    Adapter for the playwright_screenshot function.
    
    Ensures that the required 'filename' parameter is always provided,
    generating a default filename if it's missing.
    
    Args:
        original_func: The original playwright_screenshot function to call
        **kwargs: The keyword arguments received from the LLM
    
    Returns:
        The result from the original function call
    """
    # If filename is not provided, generate a default filename
    if 'filename' not in kwargs:
        import time
        default_filename = f"screenshot_{int(time.time())}.png"
        print(f"No filename provided for screenshot, using default: {default_filename}")
        kwargs['filename'] = default_filename
    
    # Ensure filename has .png extension
    if not kwargs['filename'].endswith('.png'):
        kwargs['filename'] += '.png'
    
    # Call the original function with the updated kwargs
    return await original_func(**kwargs)
