import os
import re
import glob
from collections import defaultdict
import argparse

# --- Configuration ---
ROUTER_DIRS = ['backend/app/routers']
TEST_DIRS = ['tests']
OUTPUT_FILE = 'endpoint_analysis_report.md'
BASE_URL_VARS = ['BASE_URL'] # Common variable names for base URLs in tests

# --- Regular Expressions ---
# Matches @router.get("/path", ...) or @app.post('/path', ...) etc.
# Made slightly more robust to handle spaces and different quote styles
ROUTER_REGEX = re.compile(
    r"""
    @\w+\.                                       # Decorator start (@router., @app.)
    (get|post|put|delete|patch|options|head|trace) # HTTP method (group 1)
    \s*\(\s*                                      # Opening parenthesis
    (?:["']([^"']*)["'])                      # Path in quotes (captures content in group 2)
    # We only care about the path string literal here
    """,
    re.IGNORECASE | re.VERBOSE
)

# New Regex: Focuses on capturing the first string literal (f-string or regular)
# after the method call.
REQUESTS_REGEX = re.compile(
    r"""
    (?:requests|client|async_client)\.              # Match the library call
    (get|post|put|delete|patch|options|head)        # Capture the HTTP method (group 1)
    \s*\(\s*                                        # Match opening parenthesis
    (?:url\s*=\s*)?                               # Optionally match 'url='
    (f?["\']                                     # Capture the start (group 2): optional 'f' and quote
      .*?                                         # Match the content (non-greedy)
     ["\']                                      # Match the closing quote
    )
    # Stop after capturing the first string literal argument
    """,
    re.IGNORECASE | re.VERBOSE
)

# --- Helper Functions ---

def find_python_files(directories):
    """Finds all .py files in the specified directories."""
    files = []
    for directory in directories:
        files.extend(glob.glob(os.path.join(directory, '**/*.py'), recursive=True))
    # Exclude __init__.py files unless specifically needed
    files = [f for f in files if os.path.basename(f) != '__init__.py']
    return files

def normalize_path(path_str):
    """Normalizes path parameters like /items/{item_id} to /items/{var}."""
    # Replace any {param_name} with {var}
    normalized = re.sub(r'\{[a-zA-Z0-9_]+\}', '{var}', path_str)
    # Remove trailing slashes if any, but keep root '/'
    if normalized != '/' and normalized.endswith('/'):
        normalized = normalized[:-1]
    return normalized

def extract_base_url_pattern(content):
    """Attempts to find the pattern used for BASE_URL in test files."""
    for var_name in BASE_URL_VARS:
        # Simple match for variable assignment like BASE_URL = "http://..."
        # Make regex non-greedy and robust to spaces
        match = re.search(rf'{var_name}\s*=\s*["\'](.*?)["\']', content)
        if match:
            # Pattern to remove f"{BASE_URL}..." part
            # Matches {BASE_URL}, potentially followed by /, inside f-string braces
            return rf'f?["\'].*?{{\s*{var_name}\s*\}}\/?.*?["\']'
            # Simpler version: remove the variable placeholder directly if found
            # return rf'\{{\s*{var_name}\s*\}}\/?' # Pattern to remove {VAR}/ or {VAR}

    # Fallback if no explicit BASE_URL variable found (less reliable)
    # Try to match common http patterns at the start of f-strings
    # This is prone to errors if URLs are constructed differently
    # return r'f?["']https?://.*?/'
    return None # Return None if no pattern found, rely on path starting with '/'

def sanitize_url_string(url_part):
    """Cleans up the captured URL part from regex, removing quotes and f-string markers."""
    if url_part is None:
        return ""
    # Remove surrounding quotes (single or double)
    # Remove f-string prefix if present
    if url_part.startswith('f'):
        url_part = url_part[1:]
    # Strip quotes again after removing 'f'
    return url_part.strip().strip('\'"')

def extract_path_from_test_url(raw_url_str, content):
    """Extracts the API path from a URL string found in tests.
        Tries to remove the base URL part using string manipulation.
    """
    # 1. Sanitize the raw captured string (remove outer quotes/f)
    sanitized_url = sanitize_url_string(raw_url_str)
    if not sanitized_url:
        return None

    path = None
    base_var_found = None

    # 2. Check for known BASE_URL variables within f-string braces
    for var_name in BASE_URL_VARS:
        placeholder = f"{{{var_name}}}"
        if placeholder in sanitized_url:
            base_var_found = var_name
            # Split the string at the placeholder
            parts = sanitized_url.split(placeholder, 1)
            if len(parts) > 1:
                # The path is the part after the placeholder
                # Strip trailing quotes from the fragment
                path_fragment = parts[1].rstrip('\'"')
                # Ensure it starts with a slash
                path = path_fragment if path_fragment.startswith('/') else '/' + path_fragment
                # print(f"    Debug: Split found path: {path}") # Optional debug
                break # Stop after finding the first known base var
            else:
                # Placeholder found, but nothing after it? Unlikely, but possible
                path = '/' # Default to root
                break

    # 3. If no known f-string base variable was found, check for absolute URLs
    if path is None and not base_var_found:
        if sanitized_url.startswith('http://') or sanitized_url.startswith('https://'):
            # Try to parse out the path part
            try:
                from urllib.parse import urlparse
                parsed = urlparse(sanitized_url)
                path = parsed.path
            except ImportError:
                 # Fallback if urllib not available
                 parts = sanitized_url.split('/', 3)
                 path = '/' + parts[3] if len(parts) > 3 else '/'
        elif sanitized_url.startswith('/'):
             # It might be a direct relative path already
             path = sanitized_url

    # 4. If we still haven't determined a path, return None
    if path is None:
        # print(f"  Warning: Could not determine path from '{raw_url_str}'")
        return None

    # 5. Remove query parameters if any
    path = path.split('?')[0]

    # 6. Normalize path parameters
    final_path = normalize_path(path)

    # 7. Final validation: path should start with '/'
    if not final_path or not final_path.startswith('/'):
        # print(f"  Warning: Final path '{final_path}' from '{raw_url_str}' is invalid. Skipping.")
        return None

    # 8. Skip potentially incorrect double-variable paths from complex f-strings
    if final_path == '/{var}/{var}':
        # print(f"  Warning: Skipping probable complex f-string path '{final_path}' from '{raw_url_str}'")
        return None

    return final_path

# --- Main Logic ---

def analyze_endpoints():
    endpoints = defaultdict(lambda: {'defined_in': set(), 'tested_in': set()})

    # 1. Analyze Router Files
    print("Analyzing router files...")
    router_files = find_python_files(ROUTER_DIRS)
    for filepath in router_files:
        rel_path = os.path.relpath(filepath)
        print(f"--- Analyzing Router File: {rel_path} ---") # DEBUG: Show file being processed

        # <<< HEURISTIC: Determine prefix based on filename >>>
        filename = os.path.basename(filepath)
        stem = os.path.splitext(filename)[0]
        prefix = ""

        # Refined Heuristic Rules
        if stem == 'contest':
            prefix = '/contests' # Plural
        elif stem == 'auth':
            prefix = '/auth'
        elif stem == 'admin':
            prefix = '/admin'
        elif stem == 'submission':
             prefix = '/submissions' # Plural guess
        # Assume ai_agents and ai_router define full paths or are mounted differently
        elif stem in ['ai_agents', 'ai_router']:
             prefix = '' # No prefix - paths inside are assumed absolute or mounted elsewhere
        elif stem == 'main':
            prefix = '' # No prefix
        # Fallback for other routers (if any) - use filename stem
        # elif stem:
        #     prefix = "/" + stem.replace('_', '-')

        print(f"    Derived Prefix: '{prefix}'") # DEBUG
        # <<< END HEURISTIC >>>

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                match_count = 0 # DEBUG
                for match in ROUTER_REGEX.finditer(content):
                    match_count += 1 # DEBUG
                    method = match.group(1).upper()
                    # Path is now always in group 2
                    path_raw = match.group(2)
                    if path_raw is None: # Skip if regex matched but group was empty
                        print(f"    Regex matched but path group was empty (potential issue in {rel_path})") # DEBUG
                        continue

                    # Normalize the path found *relative* to the router
                    relative_path_norm = normalize_path(path_raw if path_raw.startswith('/') else '/' + path_raw)

                    # <<< HEURISTIC: Prepend the derived prefix >>>
                    # Handle root path ('/') defined within a prefixed router
                    if relative_path_norm == '/':
                        full_path_norm = prefix if prefix else '/' # Use prefix itself, or root if no prefix
                    else:
                        full_path_norm = prefix + relative_path_norm # Combine prefix and relative path
                    # <<< END HEURISTIC >>>

                    print(f"    Found definition: {method} '{path_raw}' -> Full Path: '{full_path_norm}'") # DEBUG

                    if full_path_norm:
                        # Store using the full path including the inferred prefix
                        endpoints[(method, full_path_norm)]['defined_in'].add(rel_path)

                print(f"    Found {match_count} definitions in {rel_path}") # DEBUG
        except Exception as e:
            print(f"  Error reading/parsing router {rel_path}: {e}")

    # 2. Analyze Test Files
    print("\nAnalyzing test files...")
    test_files = find_python_files(TEST_DIRS)
    for filepath in test_files:
        rel_path = os.path.relpath(filepath)
        print(f"\n--- Processing Test File: {rel_path} ---") # DEBUG: Indicate file start
        found_in_file = 0 # DEBUG: Count matches per file
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # No need for base_url_pattern extraction here anymore

                for match_num, match in enumerate(REQUESTS_REGEX.finditer(content)):
                    found_in_file += 1 # DEBUG
                    method = match.group(1).upper()
                    raw_url_part = match.group(2) # This is the f?"..." part

                    print(f"  Match {match_num+1}: Method='{method}', Raw URL Part='{raw_url_part}'") # DEBUG

                    path = extract_path_from_test_url(raw_url_part, content)

                    print(f"    -> Extracted Path: '{path}'") # DEBUG

                    if path:
                        endpoints[(method, path)]['tested_in'].add(rel_path)
                        print(f"    --> Added: ({method}, '{path}')") # DEBUG
                    else:
                        print("    --> Skipped (Path extraction failed)") # DEBUG

            print(f"--- Finished Processing {rel_path}: Found {found_in_file} potential API calls --- ") # DEBUG

        except Exception as e:
            print(f"  Error reading/parsing test {rel_path}: {e}")

    # 3. Generate Report
    print(f"\nGenerating report: {OUTPUT_FILE}...")
    # Sort by path first, then method
    sorted_endpoints = sorted(endpoints.items(), key=lambda item: (item[0][1], item[0][0]))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Endpoint Definition vs. Test Usage Report\n\n")
        f.write("| Method | Path                       | Defined In (Routers)                  | Tested In (Tests)                     |\n")
        f.write("|--------|----------------------------|---------------------------------------|---------------------------------------|\n")

        for (method, path), data in sorted_endpoints:
            defined_files = ", ".join(sorted(data['defined_in'])) or "*None*"
            tested_files = ", ".join(sorted(data['tested_in'])) or "*None*"
            # Added padding for better alignment
            path_display = f"`{path}`"
            method_display = f"{method:<6}"
            defined_display = f"{defined_files}"
            tested_display = f"{tested_files}"
            # Ensure minimum width for columns
            f.write(f"| {method_display} | {path_display:<26} | {defined_display:<37} | {tested_display:<37} |\n")

    print("\nAnalysis complete.")
    print(f"Found {len(endpoints)} unique endpoints.")
    defined_count = sum(1 for data in endpoints.values() if data['defined_in'])
    tested_count = sum(1 for data in endpoints.values() if data['tested_in'])
    untested_count = sum(1 for data in endpoints.values() if data['defined_in'] and not data['tested_in'])
    undefined_tested_count = sum(1 for data in endpoints.values() if not data['defined_in'] and data['tested_in'])

    print(f"- Defined in routers: {defined_count}")
    print(f"- Used in tests: {tested_count}")
    print(f"- Defined but NOT tested: {untested_count}")
    print(f"- Tested but NOT defined (potential issue): {undefined_tested_count}")


if __name__ == "__main__":
    # Optional: Add command-line arguments if needed later
    # parser = argparse.ArgumentParser(description='Analyze FastAPI endpoint usage.')
    # args = parser.parse_args()
    analyze_endpoints() 