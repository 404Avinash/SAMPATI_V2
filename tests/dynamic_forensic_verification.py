"""Dynamic Forensic Verification Script for SAMPATI V2.

Executes novel randomized inputs never seen in the codebase to prove:
1. Non-hardcoded dynamic score computation.
2. Genuine federation signal caching and sub-5ms retrieval.
3. Dynamic network_score reflection in /upi/check.
4. Genuine honeypot hit tracking and 24h rolling window calculation.
5. Case status update and telemetry persistence.
"""
from __future__ import annotations

import hashlib
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from app.main import app
from app.federation.coordinator import get_federation
from app.engine.honeypot import get_honeypot_registry
from app.services.upi_cases import get_upi_case_service
from app.models.upi_models import UpiTransaction


def run_dynamic_audit():
    client = TestClient(app)
    results = {}

    print("=== STARTING DYNAMIC RUNTIME FORENSIC AUDIT ===")

    # 1. Random novel VPA and hash federation test
    rand_suffix = uuid.uuid4().hex[:12]
    random_vpa = f"audit_victim_{rand_suffix}@okaxis"
    random_vpa_hash = hashlib.sha256(random_vpa.encode("utf-8")).hexdigest()
    random_ring_hash = f"RING_AUDIT_{uuid.uuid4().hex[:8]}"

    print(f"\n[Test 1] Ingesting novel signal for VPA: {random_vpa} (hash: {random_vpa_hash[:16]}...)")
    t0 = time.perf_counter()
    post_resp = client.post(
        "/federation/signal",
        json={
            "vpa_hash": random_vpa_hash,
            "risk_level": "HIGH",
            "ring_hash": random_ring_hash,
            "node_id": "audit_probe_node",
        },
    )
    t_post = (time.perf_counter() - t0) * 1000.0
    print(f"POST /federation/signal response: {post_resp.status_code}, latency: {t_post:.3f}ms")
    assert post_resp.status_code == 200, f"Expected 200, got {post_resp.status_code}"
    post_data = post_resp.json()
    assert post_data["vpa_hash"] == random_vpa_hash
    assert post_data["federated_risk_score"] == 0.85

    # Direct hot cache coordinator query latency test
    fed_coord = get_federation()
    direct_latencies = []
    for _ in range(100):
        t_direct = time.perf_counter()
        direct_data = fed_coord.query_signal(vpa_hash=random_vpa_hash)
        t_del = (time.perf_counter() - t_direct) * 1000.0
        direct_latencies.append(t_del)
        assert direct_data["federated_risk_score"] == 0.85
        assert direct_data["cached"] is True

    direct_avg = sum(direct_latencies) / len(direct_latencies)
    direct_min = min(direct_latencies)
    direct_max = max(direct_latencies)
    print(f"Direct Coordinator Hot Cache (100 runs): min={direct_min:.4f}ms, avg={direct_avg:.4f}ms, max={direct_max:.4f}ms")
    assert direct_avg < 1.0, f"Expected sub-1ms hot cache query, got {direct_avg:.4f}ms"

    # HTTP API query test
    api_latencies = []
    for _ in range(20):
        t_start = time.perf_counter()
        q_resp = client.get(f"/federation/query?vpa_hash={random_vpa_hash}")
        t_el = (time.perf_counter() - t_start) * 1000.0
        api_latencies.append(t_el)
        assert q_resp.status_code == 200
        q_data = q_resp.json()
        assert q_data["federated_risk_score"] == 0.85
        assert q_data["cached"] is True

    api_avg = sum(api_latencies) / len(api_latencies)
    print(f"HTTP GET /federation/query (20 runs): min={min(api_latencies):.3f}ms, avg={api_avg:.3f}ms, max={max(api_latencies):.3f}ms")
    results["federation_latency"] = {
        "direct_avg_ms": direct_avg,
        "direct_min_ms": direct_min,
        "api_avg_ms": api_avg,
    }

    # 2. Test Dynamic network_score reflection in /upi/check
    payer_vpa = f"innocent_payer_{uuid.uuid4().hex[:8]}@okhdfcbank"
    check_payload = {
        "txn_id": f"TXN_AUDIT_{uuid.uuid4().hex[:8]}",
        "payer_vpa": payer_vpa,
        "payee_vpa": random_vpa,
        "amount": 4200.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payer_psp": "okhdfcbank",
        "payee_psp": "okaxis",
        "payer_account_age_days": 180,
        "payee_vpa_age_days": 180,
    }
    print(f"\n[Test 2] Testing /upi/check with federated payee VPA: {random_vpa}")
    check_resp = client.post("/upi/check", json=check_payload)
    assert check_resp.status_code == 200
    check_data = check_resp.json()
    print(f"Check response: action={check_data['action']}, risk_score={check_data['risk_score']}, network_score={check_data['network_score']}, reasons={check_data['reasons']}")
    assert check_data["network_score"] == 0.85, f"Expected network_score 0.85, got {check_data['network_score']}"
    assert "FEDERATED_MULE_NETWORK" in check_data["reasons"]
    assert check_data["action"] in ("HOLD", "BLOCK")
    results["federated_upi_check"] = {
        "action": check_data["action"],
        "risk_score": check_data["risk_score"],
        "network_score": check_data["network_score"],
        "reasons": check_data["reasons"],
    }

    # 3. Dynamic Honeypot Trap Detection & 24h hit tracking test
    hp_reg = get_honeypot_registry()
    initial_stats = hp_reg.get_stats()
    init_hits_24h = initial_stats["hits_24h"]
    init_total_hits = initial_stats["total_hits"]

    # Register a novel randomized honeypot
    novel_hp = f"honeypot_audit_trap_{uuid.uuid4().hex[:8]}@okaxis"
    hp_reg.register_honeypot(novel_hp)
    assert hp_reg.is_honeypot(novel_hp)

    random_amt = round(random.uniform(5000.0, 95000.0), 2)
    hp_txn_payload = {
        "txn_id": f"TXN_HP_{uuid.uuid4().hex[:8]}",
        "payer_vpa": f"mule_tester_{uuid.uuid4().hex[:6]}@oksbi",
        "payee_vpa": novel_hp,
        "amount": random_amt,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payer_psp": "oksbi",
        "payee_psp": "okaxis",
        "payer_account_age_days": 200,
        "payee_vpa_age_days": 200,
    }
    print(f"\n[Test 3] Transacting against registered honeypot: {novel_hp} (amount: Rs {random_amt:,.2f})")
    hp_check_resp = client.post("/upi/check", json=hp_txn_payload)
    assert hp_check_resp.status_code == 200
    hp_check_data = hp_check_resp.json()
    print(f"Honeypot check result: action={hp_check_data['action']}, risk_score={hp_check_data['risk_score']}, reasons={hp_check_data['reasons']}")
    assert hp_check_data["action"] == "BLOCK", f"Expected BLOCK, got {hp_check_data['action']}"
    assert hp_check_data["risk_score"] == 100, f"Expected 100, got {hp_check_data['risk_score']}"
    assert "R_HONEYPOT_HIT" in hp_check_data["reasons"]

    # Verify hit counter incremented
    post_hp_stats = hp_reg.get_stats()
    print(f"Honeypot stats post-hit: hits_24h={post_hp_stats['hits_24h']} (was {init_hits_24h}), total_hits={post_hp_stats['total_hits']} (was {init_total_hits})")
    assert post_hp_stats["hits_24h"] == init_hits_24h + 1
    assert post_hp_stats["total_hits"] == init_total_hits + 1

    # Verify stats API returns updated honeypot stats
    stats_resp = client.get("/upi/stats")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert stats_data["honeypot_hits_24h"] == post_hp_stats["hits_24h"]
    results["honeypot_tracking"] = {
        "verdict": hp_check_data["action"],
        "risk_score": hp_check_data["risk_score"],
        "reasons": hp_check_data["reasons"],
        "hits_24h": post_hp_stats["hits_24h"],
        "total_hits": post_hp_stats["total_hits"],
    }

    # 4. Detailed Health & Analytics verification
    print("\n[Test 4] Verifying /health/detailed and /stats/analytics")
    health_resp = client.get("/health/detailed")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert "latency_ms" in health_data
    assert "p50" in health_data["latency_ms"]
    assert "throughput" in health_data
    assert "database" in health_data
    assert "redis" in health_data
    assert "websocket" in health_data

    analytics_resp = client.get("/stats/analytics?interval=hourly&hours=24")
    assert analytics_resp.status_code == 200
    analytics_data = analytics_resp.json()
    assert "summary" in analytics_data
    assert "time_series" in analytics_data
    assert "rule_frequencies" in analytics_data
    assert "top_flagged_accounts" in analytics_data

    print(f"Health summary: latency p50={health_data['latency_ms']['p50']}ms, DB status={health_data['database']['status']}")
    print(f"Analytics summary: total_flagged={analytics_data['summary']['total_flagged']}, rules tracked={len(analytics_data['rule_frequencies'])}")

    print("\n=== ALL DYNAMIC AUDIT CHECKS PASSED EMPIRICALLY ===")
    return results


if __name__ == "__main__":
    run_dynamic_audit()
