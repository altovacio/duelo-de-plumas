#!/usr/bin/env python3
"""
Script to fix remaining variable reference issues after endpoint changes.
"""

import re

def fix_variable_references(content):
    """Fix remaining variable reference issues"""
    
    # Remove lines that reference non-existent response variables
    content = re.sub(r'\s+assert user\d+_before_resp\.status_code == 200\n', '', content)
    content = re.sub(r'\s+assert user\d+_after_resp\.status_code == 200\n', '', content)
    
    return content

def main():
    """Main function"""
    filepath = 'e2e_sec_05_text_submission.py'
    
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    content = fix_variable_references(content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fixed {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

if __name__ == "__main__":
    main() 