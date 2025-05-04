import requests
import json
import csv
import os

# Configuration
OPENAPI_URL = "http://localhost:8000/openapi.json"
OUTPUT_CSV_FILE = "endpoints_existent.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Get directory of the script
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_CSV_FILE)

print(f"Attempting to fetch OpenAPI schema from: {OPENAPI_URL}")

try:
    response = requests.get(OPENAPI_URL, timeout=10) # Added timeout
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    
    print("Successfully fetched OpenAPI schema.")
    openapi_data = response.json()
    
    endpoints = []
    if "paths" in openapi_data:
        for path, methods in openapi_data["paths"].items():
            for method in methods.keys():
                endpoints.append({"Method": method.upper(), "Endpoint": path})
    else:
        print("Warning: 'paths' key not found in the OpenAPI schema.")

    if not endpoints:
        print("No endpoints found in the schema.")
    else:
        print(f"Found {len(endpoints)} endpoints. Writing to {OUTPUT_PATH}...")
        # Sort endpoints for consistent output
        endpoints.sort(key=lambda x: (x["Endpoint"], x["Method"]))
        
        with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Method", "Endpoint"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(endpoints)
        
        print(f"Successfully wrote endpoints to {OUTPUT_PATH}")

except requests.exceptions.ConnectionError:
    print(f"Error: Could not connect to the server at {OPENAPI_URL}.")
    print("Please ensure the FastAPI application is running.")
except requests.exceptions.Timeout:
    print(f"Error: Request timed out while trying to connect to {OPENAPI_URL}.")
except requests.exceptions.RequestException as e:
    print(f"Error fetching OpenAPI schema: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response text: {e.response.text[:200]}...") # Show beginning of response
except json.JSONDecodeError:
    print("Error: Could not decode the response as JSON. Is the URL correct and returning valid JSON?")
except Exception as e:
    print(f"An unexpected error occurred: {e}") 