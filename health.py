#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get('http://localhost:8080/health')
    if response.status_code == 200:
        sys.exit(0)
    else:
        print(f"Health check failed: Status code {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"Health check failed: {str(e)}")
    sys.exit(1) 