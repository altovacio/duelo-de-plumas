#!/usr/bin/env python3
"""
Script to fix incorrect user endpoint calls in test files.
Replaces GET /users/{user_id} calls with proper endpoints.
"""

import re
import os

def fix_admin_user_calls(content):
    """Fix admin calls that use GET /users/{user_id} with admin headers"""
    # Pattern for admin calls: await client.get(f"/users/{test_data['user_id']}", headers=test_data["admin_headers"])
    pattern = r'(\s+)(\w+)_resp = await client\.get\(f"/users/\{test_data\[\'(\w+)\'\]\}", headers=test_data\["admin_headers"\]\)'
    
    def replacement(match):
        indent = match.group(1)
        var_name = match.group(2)
        user_id_key = match.group(3)
        
        return f'''{indent}users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])
{indent}assert users_resp.status_code == 200
{indent}users_data = users_resp.json()
{indent}{var_name}_data = next(u for u in users_data if u['id'] == test_data['{user_id_key}'])'''
    
    content = re.sub(pattern, replacement, content)
    
    # Fix the usage of the response
    # Replace UserResponse(**var_resp.json()).credits with var_data['credits']
    content = re.sub(r'UserResponse\(\*\*(\w+)_resp\.json\(\)\)\.credits', r"\1_data['credits']", content)
    
    return content

def fix_user_self_calls(content):
    """Fix user calls that check their own data"""
    # Pattern for self calls: await client.get(f"/users/{test_data['user1_id']}", headers=test_data["user1_headers"])
    pattern = r'await client\.get\(f"/users/\{test_data\[\'user\d+_id\'\]\}", headers=test_data\["user\d+_headers"\]\)'
    
    def replacement(match):
        # Extract the user number from the headers
        user_match = re.search(r'user(\d+)_headers', match.group(0))
        if user_match:
            user_num = user_match.group(1)
            return f'await client.get("/users/me", headers=test_data["user{user_num}_headers"])'
        return match.group(0)
    
    return re.sub(pattern, replacement, content)

def process_file(filepath):
    """Process a single test file"""
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix admin calls first
    content = fix_admin_user_calls(content)
    
    # Fix user self calls
    content = fix_user_self_calls(content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fixed {filepath}")
        return True
    else:
        print(f"  - No changes needed in {filepath}")
        return False

def main():
    """Main function"""
    test_files = [
        'e2e_sec_05_text_submission.py',
        'e2e_sec_09_cleanup_routine.py'
    ]
    
    fixed_count = 0
    for filepath in test_files:
        if os.path.exists(filepath):
            if process_file(filepath):
                fixed_count += 1
        else:
            print(f"Warning: {filepath} not found")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main() 