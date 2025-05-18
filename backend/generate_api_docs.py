#!/usr/bin/env python3
"""
Script to generate API documentation from FastAPI OpenAPI schema
"""

import requests
import json
import os
from collections import defaultdict

def fetch_openapi_schema(url):
    """Fetch the OpenAPI schema from the API"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OpenAPI schema: {e}")
        return None

def generate_markdown(schema):
    """Generate markdown documentation from the OpenAPI schema"""
    if not schema:
        return None
    
    # Extract API info
    info = schema.get('info', {})
    title = info.get('title', 'API Documentation')
    description = info.get('description', 'API endpoints documentation')
    version = info.get('version', '')
    
    # Start building markdown
    markdown = f"# {title}\n\n"
    markdown += f"{description}\n\n"
    markdown += f"**Version:** {version}\n\n"
    
    # Table of contents
    markdown += "## Table of Contents\n\n"
    
    # Group endpoints by tags
    paths = schema.get('paths', {})
    endpoints_by_tag = defaultdict(list)
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                tags = details.get('tags', ['Other'])
                operation_id = details.get('operationId', f"{method} {path}")
                summary = details.get('summary', operation_id)
                
                for tag in tags:
                    endpoints_by_tag[tag].append({
                        'path': path,
                        'method': method.upper(),
                        'summary': summary,
                        'description': details.get('description', ''),
                        'operation_id': operation_id
                    })
    
    # Add tags to table of contents
    for tag in sorted(endpoints_by_tag.keys()):
        tag_link = tag.lower().replace(' ', '-')
        markdown += f"- [{tag}](#{tag_link})\n"
    
    markdown += "\n"
    
    # Document endpoints by tag
    for tag in sorted(endpoints_by_tag.keys()):
        tag_link = tag.lower().replace(' ', '-')
        markdown += f"## {tag}\n\n"
        
        for endpoint in endpoints_by_tag[tag]:
            markdown += f"### {endpoint['method']} {endpoint['path']}\n\n"
            
            if endpoint['summary']:
                markdown += f"**Summary:** {endpoint['summary']}\n\n"
                
            if endpoint['description']:
                markdown += f"{endpoint['description']}\n\n"
                
            # If we wanted to add request/response details, parameters, etc.,
            # we would parse those from the schema and add them here
        
        markdown += "\n"
    
    markdown += "---\n\n"
    markdown += "*This document was generated automatically by capturing the FastAPI OpenAPI schema from the API server.*"
    
    return markdown

def main():
    """Main function"""
    # URL to the OpenAPI schema
    schema_url = "http://localhost:8000/openapi.json"
    
    # Fetch the schema
    print(f"Fetching OpenAPI schema from {schema_url}...")
    schema = fetch_openapi_schema(schema_url)
    
    if not schema:
        print("Failed to fetch schema. Make sure the API server is running.")
        return
    
    # Generate markdown
    print("Generating markdown documentation...")
    markdown = generate_markdown(schema)
    
    if not markdown:
        print("Failed to generate markdown documentation.")
        return
    
    # Ensure docs directory exists
    os.makedirs("docs", exist_ok=True)
    
    # Write to file
    output_file = "docs/api_endpoints_programmatically.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"API documentation successfully written to {output_file}")

if __name__ == "__main__":
    main() 