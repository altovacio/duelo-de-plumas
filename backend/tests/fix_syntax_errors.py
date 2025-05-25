#!/usr/bin/env python3
"""
Script to fix syntax errors caused by missing line breaks.
"""

import re

def fix_syntax_errors(content):
    """Fix syntax errors by adding proper line breaks"""
    
    # Fix lines where two statements are on the same line
    # Pattern: variable = something    other_variable = something_else
    pattern = r'(\w+_data = next\([^)]+\))\s+(\w+_credits_\w+ = \w+_data\[\'credits\'\])'
    content = re.sub(pattern, r'\1\n    \2', content)
    
    return content

def main():
    """Main function"""
    filepath = 'e2e_sec_05_text_submission.py'
    
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    content = fix_syntax_errors(content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fixed {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

if __name__ == "__main__":
    main() 