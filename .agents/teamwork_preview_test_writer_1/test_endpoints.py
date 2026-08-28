import asyncio
import os
import sys
import httpx

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root not in sys.path:
    sys.path.insert(0, root)

from app.main import app

async def test_endpoints():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health
        res = await client.get("/health")
        print(f"GET /health -> {res.status_code}: {res.json()}")

        # 2. Stats
        res = await client.get("/upi/stats")
        print(f"GET /upi/stats -> {res.status_code}: {res.json()}")

        # 3. Cases
        res = await client.get("/upi/cases")
        print(f"GET /upi/cases -> {res.status_code}: {res.json()}")

        # 4. Check txn
        sample_txn = {
            "txn_id": "TXN_TEST_001",
            "payer_vpa": "victim1@upi",
            "payee_vpa": "mule_hub@upi",
            "amount": 25000.0,
            "timestamp": "2026-08-28T19:00:00Z",
            "device_id": "DEV_TEST_001",
            "location": "Mumbai, IN",
            "ip_address": "103.21.244.2"
        }
        res = await client.post("/upi/check", json=sample_txn)
        print(f"POST /upi/check -> {res.status_code}: {res.json()}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
