import asyncio
import os
import sys

# Ensure project root is in sys.path
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root not in sys.path:
    sys.path.insert(0, root)

async def main():
    print(f"Project root added to sys.path: {root}")
    try:
        from app.main import app
        print("Successfully imported app.main:app")
        print(f"Routes registered: {len(app.routes)}")
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', None)
                m_str = ','.join(methods) if methods else 'WS/Mount'
                print(f"  {m_str:15} {route.path}")
    except Exception as e:
        print(f"Error importing app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
