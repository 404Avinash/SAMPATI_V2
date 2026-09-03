"""Adversarial Empirical Challenge Test Suite for Milestone 1 Threat Intelligence Layer.

Author: Empirical Challenger 1 (teamwork_preview_challenger_m1_1)
Evaluates:
1. Regex entity extraction (extract_entities) under dirty, obfuscated, and boundary-colliding inputs.
2. FraudGraphService under high-frequency concurrent writes, cyclic topologies, self-loops, and deep ego-graph queries.
3. Campaign similarity calculations across corner cases (empty, malformed, contradictory, massive inputs).
"""
from __future__ import annotations

import concurrent.futures
import time
import unittest
from typing import List

from app.models.threat_intel import (
    ExtractedEntities,
    ThreatSignalCreateRequest,
    extract_entities,
)
from app.services.graph_service import FraudGraphService, get_fraud_graph
from app.services.threat_intel_service import ThreatIntelService, get_threat_intel_service


class TestRegexAdversarialBoundaries(unittest.TestCase):
    """Adversarial stress-testing of regex entity extraction."""

    def test_utr_and_numeric_collision_resistance(self) -> None:
        """Verify that 12-digit bank reference numbers (UTRs) and timestamps do not falsely trigger phone extraction."""
        # 12-digit UPI UTR starting with 9, 8, 7, 6
        utr_samples = [
            "Payment of Rs 500 completed. UTR: 902182910291 ref id.",
            "Transaction successful ref 876543210987 via IMPS.",
            "NEFT ref no 712345678901 processed at bank.",
            "Reference number 612345678901 recorded.",
            "UTR 987654321012 credited to your account.",
        ]
        for msg in utr_samples:
            entities = extract_entities(msg)
            # None of the 12-digit numbers should be truncated into a 10-digit phone
            for phone in entities.phones:
                self.assertNotIn(phone[-10:], ["9021829102", "8765432109", "7123456789", "6123456789", "9876543210"],
                                 f"12-digit UTR was truncated into phone: {phone} from '{msg}'")

    def test_timestamp_collision_resistance(self) -> None:
        """Verify timestamps like 202609031234 or 9909031234 are handled."""
        msg = "Alert generated at 202609031234 by automated fraud sensor."
        entities = extract_entities(msg)
        self.assertEqual(len(entities.phones), 0, f"Timestamp was falsely extracted as phone: {entities.phones}")

    def test_international_prefix_behavior(self) -> None:
        """Examine how international numbers (+44, +1) behave against Indian phone regex."""
        # UK mobile (+44 7911 123456)
        msg_uk = "Contact UK desk at +44 7911 123456 for overseas transfer."
        entities_uk = extract_entities(msg_uk)
        # Note: If phone regex captures 7911123456 because of space boundary, record behavior
        print(f"[EMPIRICAL OBS] UK number extraction result: {entities_uk.phones}")

        # US number (+1 650 123 4567)
        msg_us = "Call US support +1 650 123 4567 immediately."
        entities_us = extract_entities(msg_us)
        print(f"[EMPIRICAL OBS] US number extraction result: {entities_us.phones}")

    def test_email_vs_upi_vpa_collision(self) -> None:
        """Verify standard emails vs actual UPI handles."""
        # Standard email providers that should NOT be extracted as UPI VPAs
        email_negative_cases = [
            "Send confirmation to user@gmail.com please.",
            "Contact admin at support@yahoo.com.",
            "Mail us at billing@outlook.com for invoices.",
            "Security reports go to alert@sbi.co.in or webmaster@icici.com.",
            "Helpdesk email is contact@bank.org or tech@service.net.",
        ]
        for text in email_negative_cases:
            entities = extract_entities(text)
            self.assertEqual(len(entities.upi_ids), 0,
                             f"Email falsely extracted as UPI VPA in: '{text}' -> {entities.upi_ids}")

        # Legitimate UPI VPAs that MUST be extracted
        legit_vpas = [
            ("Pay Rs 500 to fraudster@oksbi immediately", "fraudster@oksbi"),
            ("Refund fee to merchant@okhdfcbank now", "merchant@okhdfcbank"),
            ("Transfer to quick.cash@paytm", "quick.cash@paytm"),
            ("Send to mule_01@ybl", "mule_01@ybl"),
            ("Deposit to user123@axl", "user123@axl"),
        ]
        for text, expected_vpa in legit_vpas:
            entities = extract_entities(text)
            vpa_lower = [v.lower() for v in entities.upi_ids]
            self.assertIn(expected_vpa.lower(), vpa_lower,
                          f"Failed to extract legitimate UPI VPA: {expected_vpa} from '{text}'")

    def test_email_subdomain_and_tld_boundary_cases(self) -> None:
        """Adversarially probe subdomain and unusual TLD handling."""
        # Probing email with subdomains: user@corp.example.com vs user@support
        text_subdomain = "Contact developer at user@support.example.com for assistance."
        entities_sub = extract_entities(text_subdomain)
        # BUG RECORD: user@support.example.com gets truncated to 'user@support'
        self.assertNotIn("user@support", [v.lower() for v in entities_sub.upi_ids],
                         f"Subdomain email was falsely extracted as UPI VPA: {entities_sub.upi_ids}")

    def test_dirty_and_obfuscated_urls(self) -> None:
        """Adversarial stress-test on URL extraction with punctuation, brackets, markdown, and ports."""
        # Markdown link syntax
        text_md = "Click [here](https://sbi-kyc-update.com/login) to unblock account."
        entities_md = extract_entities(text_md)
        self.assertTrue(len(entities_md.urls) > 0, "Failed to extract URL from markdown")
        # Check if trailing parenthesis is cleanly stripped
        for u in entities_md.urls:
            self.assertFalse(u.endswith(")"), f"URL contains trailing markdown parenthesis: {u}")

        # Parenthesized URL
        text_paren = "Visit our site (https://verify-pan.online/auth) today."
        entities_paren = extract_entities(text_paren)
        self.assertTrue(len(entities_paren.urls) > 0)
        for u in entities_paren.urls:
            self.assertFalse(u.endswith(")"), f"URL contains trailing parenthesis: {u}")

        # Trailing sentence punctuation
        text_punct = "Go to https://phish-bank.xyz/portal, or call us; or visit https://fake-reward.site/claim!?"
        entities_punct = extract_entities(text_punct)
        for u in entities_punct.urls:
            self.assertFalse(u.endswith(",") or u.endswith(";") or u.endswith("!") or u.endswith("?"),
                             f"URL contains trailing punctuation: {u}")

        # IP address with port
        text_ip = "Suspicious connection to http://192.168.1.100:8080/malware.apk detected."
        entities_ip = extract_entities(text_ip)
        self.assertTrue(any("192.168.1.100:8080" in u for u in entities_ip.urls),
                        f"Failed to extract IP with port: {entities_ip.urls}")

    def test_social_engineering_evasion(self) -> None:
        """Test tag detection against evasion attempts (zero-width spaces, mixed casing)."""
        # Mixed casing should match
        text_case = "uRgEnT: YoUr sBi bAnK aCcOuNt iS bLoCkEd. uPdAtE kYc."
        entities_case = extract_entities(text_case)
        self.assertIn("Bank impersonation", entities_case.tags)
        self.assertIn("KYC suspension", entities_case.tags)
        self.assertIn("Urgency", entities_case.tags)

        # Zero-width space insertion: U\u200brgent
        text_zwsp = "U\u200brgent: Please verify your account."
        entities_zwsp = extract_entities(text_zwsp)
        # Note evasion empirical observation
        print(f"[EMPIRICAL OBS] Zero-width space evasion tags: {entities_zwsp.tags}")


class TestFraudGraphServicePressure(unittest.TestCase):
    """Stress-testing FraudGraphService under concurrency, cycles, self-loops, and deep traversals."""

    def setUp(self) -> None:
        self.graph = FraudGraphService()

    def test_concurrent_high_frequency_read_write(self) -> None:
        """Execute concurrent reads, writes, transactions, and subgraph queries across 8 threads."""
        errors: List[Exception] = []
        operations_count = 50
        num_workers = 8

        def worker_task(worker_id: int) -> None:
            try:
                for i in range(operations_count):
                    # 1. Add threat signal
                    sig_id = f"SIG-CONC-{worker_id}-{i}"
                    self.graph.add_threat_signal({
                        "signal_id": sig_id,
                        "phone": f"+9198765{worker_id:02d}{i:03d}",
                        "upi_id": f"mule_{worker_id}_{i}@oksbi",
                        "url": f"https://scam_{worker_id}_{i}.com",
                        "severity": "HIGH",
                        "matched_campaign_id": "CAMP-KYC-PHISH-01",
                    })

                    # 2. Add transaction
                    self.graph.add_transaction(
                        payer_vpa=f"mule_{worker_id}_{i}@oksbi",
                        payee_vpa=f"mule_{(worker_id + 1) % num_workers}_{i}@okaxis",
                        amount=1000.0 + i,
                    )

                    # 3. Query subgraph
                    if i % 10 == 0:
                        sub = self.graph.get_subgraph(f"VPA:mule_{worker_id}_{i}@oksbi", depth=2)
                        assert "nodes" in sub
                        assert "edges" in sub

                    # 4. Query stats
                    if i % 25 == 0:
                        stats = self.graph.get_stats()
                        assert stats["total_nodes"] > 0
            except Exception as exc:
                errors.append(exc)

        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, wid) for wid in range(num_workers)]
            concurrent.futures.wait(futures)
        elapsed = time.perf_counter() - start_time

        self.assertEqual(len(errors), 0, f"Encountered concurrency errors: {errors}")
        stats = self.graph.get_stats()
        print(f"[EMPIRICAL BENCHMARK] Concurrent stress completed in {elapsed:.3f}s. Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")
        self.assertGreater(stats["total_nodes"], 400)
        self.assertGreater(stats["total_edges"], 400)

    def test_get_subgraph_none_entity_id_handling(self) -> None:
        """Verify that passing None or non-string entity_id does not raise AttributeError."""
        try:
            res = self.graph.get_subgraph(None)  # type: ignore
            self.assertFalse(res["found"])
        except AttributeError as err:
            self.fail(f"get_subgraph(None) crashed with unhandled AttributeError: {err}")

    def test_cycles_and_self_loops(self) -> None:
        """Construct directed cycles and self-loops, verifying graph integrity and ego-graph termination."""
        # 1. Self-loop: A -> A
        self.graph.add_transaction("mule_loop@oksbi", "mule_loop@oksbi", 500.0, "TXN_SELF")
        # 2. 3-node cycle: A -> B -> C -> A
        self.graph.add_transaction("cycle_a@oksbi", "cycle_b@okaxis", 1000.0, "TXN_C1")
        self.graph.add_transaction("cycle_b@okaxis", "cycle_c@icici", 1000.0, "TXN_C2")
        self.graph.add_transaction("cycle_c@icici", "cycle_a@oksbi", 1000.0, "TXN_C3")

        # Query ego-graph at varying depths
        for depth in [1, 2, 5, 10]:
            sub = self.graph.get_subgraph("VPA:cycle_a@oksbi", depth=depth)
            self.assertTrue(sub["found"])
            self.assertGreaterEqual(sub["total_nodes"], 3)
            # Must contain cycle edges
            edge_pairs = [(e["source"], e["target"]) for e in sub["edges"]]
            self.assertIn(("VPA:cycle_a@oksbi", "VPA:cycle_b@okaxis"), edge_pairs)
            self.assertIn(("VPA:cycle_b@okaxis", "VPA:cycle_c@icici"), edge_pairs)
            self.assertIn(("VPA:cycle_c@icici", "VPA:cycle_a@oksbi"), edge_pairs)

        # Self-loop query
        sub_self = self.graph.get_subgraph("VPA:mule_loop@oksbi", depth=2)
        self.assertTrue(sub_self["found"])
        self.assertEqual(sub_self["total_nodes"], 1)
        self.assertEqual(sub_self["total_edges"], 1)

    def test_deep_ego_graph_and_boundary_queries(self) -> None:
        """Verify behavior under extreme depth queries and nonexistent or empty entity IDs."""
        # Nonexistent entity
        sub_none = self.graph.get_subgraph("VPA:does_not_exist@oksbi", depth=2)
        self.assertFalse(sub_none["found"])
        self.assertEqual(sub_none["total_nodes"], 0)
        self.assertEqual(len(sub_none["nodes"]), 0)

        # Build a chain of 10 nodes
        for i in range(9):
            self.graph.add_transaction(f"chain_{i}@oksbi", f"chain_{i+1}@oksbi", 100.0)

        # Radius 1 should only get immediate neighbors (2 nodes for end, 3 for middle)
        sub_1 = self.graph.get_subgraph("VPA:chain_0@oksbi", depth=1)
        self.assertEqual(sub_1["total_nodes"], 2)

        # Radius 10 should reach all 10 nodes
        sub_10 = self.graph.get_subgraph("VPA:chain_0@oksbi", depth=10)
        self.assertEqual(sub_10["total_nodes"], 10)
        self.assertEqual(sub_10["total_edges"], 9)

        # Large radius (depth=50) should gracefully terminate at component boundary
        sub_50 = self.graph.get_subgraph("VPA:chain_0@oksbi", depth=50)
        self.assertEqual(sub_50["total_nodes"], 10)

    def test_export_graph_capping(self) -> None:
        """Verify export_graph node capping logic (limit_nodes)."""
        for i in range(30):
            self.graph.add_transaction(f"hub@oksbi", f"spoke_{i}@oksbi", 100.0)

        # Cap at 5 nodes
        capped = self.graph.export_graph(limit_nodes=5)
        self.assertEqual(len(capped["nodes"]), 5)
        # Hub node with 30 degrees must be among the top 5
        node_ids = [n["id"] for n in capped["nodes"]]
        self.assertIn("VPA:hub@oksbi", node_ids)

        # Cap at 0 nodes
        capped_0 = self.graph.export_graph(limit_nodes=0)
        self.assertEqual(len(capped_0["nodes"]), 0)


class TestCampaignSimilarityEdgeCases(unittest.TestCase):
    """Adversarial testing of campaign similarity calculations."""

    def setUp(self) -> None:
        self.service = ThreatIntelService()

    def test_empty_and_null_inputs(self) -> None:
        """Verify handling of empty tags, null raw_content, null IDs."""
        camp_id, sim, name = self.service.compute_campaign_similarity(
            tags=[],
            raw_content=None,
            upi_id=None,
            url=None,
        )
        self.assertIsNone(camp_id)
        self.assertEqual(sim, 0.0)
        self.assertIsNone(name)

    def test_single_character_and_whitespace_tags(self) -> None:
        """Verify that single character or whitespace tags do not cause false matches or crashes."""
        tags = ["a", " ", "", "   ", "x", "!"]
        camp_id, sim, name = self.service.compute_campaign_similarity(
            tags=tags,
            raw_content="hello world",
        )
        self.assertIsNone(camp_id)
        self.assertEqual(sim, 0.0)

    def test_conflicting_tags_and_multi_scam_signals(self) -> None:
        """Test behavior when conflicting/contradictory tags from all 3 campaigns are passed."""
        conflicting_tags = [
            "Bank impersonation", "KYC suspension",  # Phishing
            "Smurfing Dispersal", "Rapid Conduit",   # Smurfing
            "Telegram task", "Crypto reward",       # Investment
        ]
        camp_id, sim, name = self.service.compute_campaign_similarity(
            tags=conflicting_tags,
            raw_content="Dear user bank KYC blocked but earn crypto bonus and split transfer now",
        )
        # Should pick the strongest match without crashing
        self.assertIsNotNone(camp_id)
        self.assertGreaterEqual(sim, 0.60)
        self.assertLessEqual(sim, 0.98)
        print(f"[EMPIRICAL OBS] Conflicting tags matched: {camp_id} ({name}) with similarity {sim}")

    def test_massive_payload_dos_resistance(self) -> None:
        """Verify performance and memory stability when processing massive text (100,000 characters)."""
        massive_text = "This is legitimate communication. " * 3000 + "Urgent: Update your SBI KYC at https://sbi.in or account blocked."
        start = time.perf_counter()
        entities = extract_entities(massive_text)
        extract_time = time.perf_counter() - start

        start_sim = time.perf_counter()
        camp_id, sim, name = self.service.compute_campaign_similarity(
            tags=entities.tags,
            raw_content=massive_text,
        )
        sim_time = time.perf_counter() - start_sim

        print(f"[EMPIRICAL BENCHMARK] Massive payload (100k chars): extract={extract_time:.4f}s, similarity={sim_time:.4f}s")
        self.assertLess(extract_time, 0.20, f"Extraction on 100k chars exceeded 200ms: {extract_time:.4f}s")
        self.assertLess(sim_time, 0.05, f"Similarity on 100k chars exceeded 50ms: {sim_time:.4f}s")
        self.assertEqual(camp_id, "CAMP-KYC-PHISH-01")
    def test_non_string_tags_graceful_handling(self) -> None:
        """Verify that passing None or non-string items in tags list does not raise unhandled TypeError."""
        try:
            camp_id, sim, name = self.service.compute_campaign_similarity(
                tags=[None, 123],  # type: ignore
                raw_content="hello world",
            )
            self.assertIsNone(camp_id)
        except TypeError as err:
            self.fail(f"compute_campaign_similarity(tags=[None]) crashed with unhandled TypeError: {err}")


if __name__ == "__main__":
    unittest.main()
