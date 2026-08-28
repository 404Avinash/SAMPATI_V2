import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root not in sys.path:
    sys.path.insert(0, root)

from app.main import app

def print_openapi_paths():
    openapi_schema = app.openapi()
    print(f"Title: {openapi_schema.get('info', {}).get('title')}")
    print(f"Version: {openapi_schema.get('info', {}).get('version')}")
    print("\nAPI Endpoints:")
    for path, methods in sorted(openapi_schema.get("paths", {}).items()):
        for method, spec in sorted(methods.items()):
            summary = spec.get("summary") or spec.get("description") or ""
            print(f"  {method.upper():6} {path:35} - {summary[:50]}")

if __name__ == "__main__":
    print_openapi_paths()
