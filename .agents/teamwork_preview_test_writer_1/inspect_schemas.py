import json
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root not in sys.path:
    sys.path.insert(0, root)

from app.main import app

def print_schemas():
    openapi = app.openapi()
    schemas = openapi.get("components", {}).get("schemas", {})
    print(f"Total Schemas: {len(schemas)}")
    for name, s in schemas.items():
        props = list(s.get("properties", {}).keys())
        req = s.get("required", [])
        print(f"\nSchema: {name} (required: {req})")
        for p, spec in s.get("properties", {}).items():
            t = spec.get("type") or spec.get("$ref") or "any"
            print(f"  - {p}: {t}")

if __name__ == "__main__":
    print_schemas()
