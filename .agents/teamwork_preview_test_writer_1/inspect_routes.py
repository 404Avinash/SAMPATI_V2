import asyncio
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root not in sys.path:
    sys.path.insert(0, root)

from app.main import app

def print_routes():
    print(f"Total top-level app.routes: {len(app.routes)}")
    for r in app.routes:
        if hasattr(r, "path"):
            methods = getattr(r, 'methods', None)
            m_str = ','.join(methods) if methods else 'WS'
            print(f"  {m_str:15} {r.path} -> {type(r).__name__}")
        elif hasattr(r, "routes"):
            print(f"  Container: {type(r).__name__}")
            for sub_r in r.routes:
                methods = getattr(sub_r, 'methods', None)
                m_str = ','.join(methods) if methods else 'WS'
                print(f"    {m_str:15} {getattr(sub_r, 'path', '<no path>')}")
        else:
            print(f"  Other: {type(r).__name__}")

if __name__ == "__main__":
    print_routes()
