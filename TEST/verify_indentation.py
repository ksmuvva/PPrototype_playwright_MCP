#!/usr/bin/env python3
"""
Direct indentation verification for playwright_function_patches.py
"""
import os
import re

# Get the full path to the file
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'playwright_function_patches.py')

print(f"Checking indentation in {file_path}")
print("=" * 50)

with open(file_path, 'r') as f:
    lines = f.readlines()

# Check line 257 and surrounding lines for proper indentation
target_line = 257 - 1  # Convert to 0-based index
print(f"\nChecking line {target_line+1} and surrounding context:")

for i in range(max(0, target_line - 5), min(len(lines), target_line + 5)):
    line = lines[i].rstrip()
    indentation = len(line) - len(line.lstrip())
    print(f"{i+1:3d}: {'_' * indentation}{line.lstrip()} (indent: {indentation})")
    if i == target_line:
        # Check if this line starts with proper indentation
        if line.strip().startswith('if') and indentation == 12:
            print(f"✅ Line {i+1} has correct indentation ({indentation} spaces)")
        else:
            print(f"❌ Line {i+1} may have incorrect indentation ({indentation} spaces)")

print("\nFix verification complete!")
