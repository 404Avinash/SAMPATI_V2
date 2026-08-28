import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root not in sys.path:
    sys.path.insert(0, root)

from app.api import websocket

print(f"websocket.router routes: {len(websocket.router.routes)}")
for r in websocket.router.routes:
    print(f"  Path: {r.path} Name: {r.name}")
