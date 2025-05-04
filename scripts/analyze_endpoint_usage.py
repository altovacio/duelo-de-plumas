import csv
import os
from collections import defaultdict

# Configuration
USED_ENDPOINTS_FILE = 'endpoints_used.csv'
EXISTENT_ENDPOINTS_FILE = 'endpoints_existent.csv'
OUTPUT_REPORT_FILE = 'endpoint_usage_report.csv'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Get workspace root

# Construct full paths
used_path = os.path.join(BASE_DIR, USED_ENDPOINTS_FILE)
existent_path = os.path.join(BASE_DIR, EXISTENT_ENDPOINTS_FILE)
output_path = os.path.join(BASE_DIR, OUTPUT_REPORT_FILE)

print(f"Reading used endpoints from: {used_path}")
print(f"Reading existent endpoints from: {existent_path}")

# --- Helper Function for Path Matching ---
def paths_match(logged_path: str, template_path: str) -> bool:
    """
    Checks if a logged path matches a template path based on the rule:
    '{var}' in template matches any integer segment in logged path.
    Other segments must match exactly.
    """
    logged_segments = logged_path.strip('/').split('/')
    template_segments = template_path.strip('/').split('/')

    if len(logged_segments) != len(template_segments):
        return False

    for log_seg, tpl_seg in zip(logged_segments, template_segments):
        if tpl_seg.startswith('{') and tpl_seg.endswith('}'):
            # Template segment is a variable, check if logged segment is an integer
            if not log_seg.isdigit():
                return False
        elif log_seg != tpl_seg:
            # Segments are not variables and do not match literally
            return False
            
    # If all segments matched according to the rules
    return True

# --- Read Used Endpoints ---
# Dictionary to store usage: {(Method, LoggedEndpoint): set(filepaths)}
raw_endpoint_usage = defaultdict(set)
# Set to store all unique (Method, LoggedEndpoint) pairs found in usage logs
raw_used_endpoint_pairs = set()

try:
    with open(used_path, 'r', newline='', encoding='utf-8') as csvfile:
        header_line = csvfile.readline().strip()
        if 'Method' not in header_line or 'Endpoint' not in header_line or 'File' not in header_line:
            print("Warning: Header row likely missing/incorrect in endpoints_used.csv. Attempting to process.")
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, fieldnames=['Method', 'Endpoint', 'Variables', 'File'])
        else:
            csvfile.seek(0)
            reader = csv.DictReader(csvfile)

        if not all(col in reader.fieldnames for col in ['Method', 'Endpoint', 'File']):
             print(f"Error: Cannot find required columns ('Method', 'Endpoint', 'File') in {used_path}. Found: {reader.fieldnames}")
             exit(1)

        for row in reader:
            if not row.get('Method') or not row.get('Endpoint') or not row.get('File'):
                continue
                
            method = row['Method'].strip().upper()
            logged_endpoint = row['Endpoint'].strip()
            # Skip variable endpoints logged explicitly
            if logged_endpoint.startswith("Variable:"):
                continue
                
            filepath = row['File'].strip()
            current_pair = (method, logged_endpoint)
            raw_endpoint_usage[current_pair].add(filepath)
            raw_used_endpoint_pairs.add(current_pair)
            
    print(f"Processed {len(raw_used_endpoint_pairs)} unique non-variable used endpoint/method pairs.")

except FileNotFoundError:
    print(f"Error: File not found - {used_path}")
    exit(1)
except Exception as e:
    print(f"Error reading {used_path}: {e}")
    exit(1)

# --- Read Existent Endpoints (Templates) ---
existent_template_pairs = set()
try:
    with open(existent_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        expected_cols = ['Method', 'Endpoint']
        if not all(col in reader.fieldnames for col in expected_cols):
             print(f"Error: Missing expected columns in {existent_path}. Found: {reader.fieldnames}. Expected: {expected_cols}")
             exit(1)
             
        for row in reader:
             method = row['Method'].strip().upper()
             template_endpoint = row['Endpoint'].strip()
             if method and template_endpoint:
                 existent_template_pairs.add((method, template_endpoint))
                 
    print(f"Read {len(existent_template_pairs)} unique existent endpoint template/method pairs.")

except FileNotFoundError:
    print(f"Error: File not found - {existent_path}")
    exit(1)
except Exception as e:
    print(f"Error reading {existent_path}: {e}")
    exit(1)

# --- Match Used Endpoints to Templates ---
# {(Method, TemplateEndpoint): set(filepaths)}
template_usage = defaultdict(set)
tested_template_pairs = set()
unmatched_used_endpoints = raw_used_endpoint_pairs.copy() # Keep track of used endpoints that didn't match any template

for t_method, t_endpoint in existent_template_pairs:
    for u_method, u_endpoint in raw_used_endpoint_pairs:
        if t_method == u_method and paths_match(u_endpoint, t_endpoint):
            # Match found! Associate files from the raw usage with the template
            files = raw_endpoint_usage[(u_method, u_endpoint)]
            template_usage[(t_method, t_endpoint)].update(files)
            tested_template_pairs.add((t_method, t_endpoint))
            # Remove the matched used endpoint from the unmatched set
            unmatched_used_endpoints.discard((u_method, u_endpoint))


# --- Generate Report Data (Based on Templates) ---
report_data = []
endpoints_tested_count = 0
endpoints_not_tested_count = 0

# Iterate through sorted templates
for method, template_endpoint in sorted(list(existent_template_pairs), key=lambda x: (x[1], x[0])):
    files_tested_in = template_usage.get((method, template_endpoint), set())
    
    if files_tested_in:
        files_str = ", ".join(sorted(list(files_tested_in)))
        endpoints_tested_count += 1
    else:
        files_str = "Not Tested"
        endpoints_not_tested_count += 1
        
    report_data.append({
        "Endpoint": template_endpoint, # Report the template path
        "Method": method,
        "Scripts Where Tested": files_str
    })

# --- Write the output report ---
print(f"\nWriting report to: {output_path}")
try:
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Endpoint", "Method", "Scripts Where Tested"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(report_data)
    
    print("\n--- Analysis Summary ---")
    print(f"Total unique endpoint templates defined in OpenAPI: {len(existent_template_pairs)}")
    print(f"Total unique non-variable endpoint/method pairs logged in tests: {len(raw_used_endpoint_pairs)}")
    print(f"Endpoint templates covered by tests (after matching): {len(tested_template_pairs)}")
    print(f"Endpoint templates NOT covered by tests: {endpoints_not_tested_count}")
    
    print("\n--- Logged Endpoints NOT Matching Any OpenAPI Template ---")
    if not unmatched_used_endpoints:
        print("None - All logged non-variable endpoints matched an OpenAPI template.")
    else:
        print(f"Total unmatched: {len(unmatched_used_endpoints)}")
        for method, endpoint in sorted(list(unmatched_used_endpoints)):
             files = ", ".join(sorted(list(raw_endpoint_usage.get((method, endpoint), set()))))
             print(f"  - {method} {endpoint} (Used in: {files})")

    print(f"\nReport successfully written to {output_path}")

except Exception as e:
    print(f"Error writing report file {output_path}: {e}")
    exit(1) 