#!/usr/bin/env python3
"""
Generate Postman collection from OpenAPI/Swagger specification
"""

import json
import sys
from typing import Dict, List

def generate_collection_from_openapi(openapi_file: str, output_file: str):
    """Generate Postman collection from OpenAPI spec"""
    
    with open(openapi_file, 'r') as f:
        spec = json.load(f)
    
    collection = {
        "info": {
            "name": spec.get("info", {}).get("title", "API Collection"),
            "description": spec.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    # Add base URL variable
    servers = spec.get("servers", [])
    if servers:
        collection["variable"] = [{
            "key": "baseUrl",
            "value": servers[0].get("url", "")
        }]
    
    # Generate requests from paths
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        folder = create_folder(path, methods)
        collection["item"].append(folder)
    
    # Write output
    with open(output_file, 'w') as f:
        json.dump(collection, f, indent=2)
    
    print(f"✅ Collection generated: {output_file}")

def create_folder(path: str, methods: Dict) -> Dict:
    """Create folder for API path"""
    folder = {
        "name": path,
        "item": []
    }
    
    for method, details in methods.items():
        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            request = create_request(method.upper(), path, details)
            folder["item"].append(request)
    
    return folder

def create_request(method: str, path: str, details: Dict) -> Dict:
    """Create request item"""
    return {
        "name": details.get("summary", f"{method} {path}"),
        "request": {
            "method": method,
            "url": {
                "raw": "{{baseUrl}}" + path,
                "host": ["{{baseUrl}}"],
                "path": path.strip("/").split("/")
            },
            "description": details.get("description", "")
        }
    }

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_collection.py <openapi.json> <output.json>")
        sys.exit(1)
    
    generate_collection_from_openapi(sys.argv[1], sys.argv[2])