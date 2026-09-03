"""Central Fraud Graph Service for SAMPATI V2.

Maintains a unified, thread-safe, multi-entity knowledge graph using NetworkX DiGraph.
Connects Pre-Transaction Early Warning Threat Signals, Identifiers (VPAs, Phones, URLs),
Active Fraud Syndicates (Campaigns), Post-Transaction Investigative Cases, and Mule Rings.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

logger = logging.getLogger("sampati.services.graph")

# Supported Node Types
NODE_TYPES: Set[str] = {"VPA", "PHONE", "URL", "CAMPAIGN", "CASE", "SIGNAL", "RING"}

# Supported Edge Types
EDGE_TYPES: Set[str] = {
    "EXTRACTED_FROM",      # Entity (VPA/PHONE/URL) -> SIGNAL
    "ASSOCIATED_WITH",     # PHONE -> VPA
    "TRANSACTED_TO",       # Payer VPA -> Payee VPA
    "MEMBER_OF_CAMPAIGN",  # SIGNAL/VPA -> CAMPAIGN
    "LINKED_TO_CASE",      # VPA/SIGNAL -> CASE
}


class NodeList(list):
    """List of node IDs with dict-like compatibility attributes for ingestion responses."""

    def __init__(
        self,
        node_ids: List[str],
        signal_id: str = "",
        edge_count: int = 0,
        edges: Optional[List[Any]] = None,
    ) -> None:
        super().__init__(node_ids)
        self.node_ids = node_ids
        self.signal_id = signal_id
        self.edge_count = edge_count
        self.edges = edges or []

    def get(self, key: str, default: Any = None) -> Any:
        if key == "node_ids":
            return self.node_ids
        if key == "signal_id":
            return self.signal_id
        if key == "edge_count":
            return self.edge_count
        if key == "edges":
            return self.edges
        return default


class FraudGraphService:
    """Thread-safe multi-entity fraud graph powered by NetworkX DiGraph."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._graph: nx.DiGraph = nx.DiGraph()

    def _resolve_node_id(self, entity_id: str) -> Optional[str]:
        """Resolve raw string or prefixed ID to an existing node ID in the graph."""
        if not entity_id or not isinstance(entity_id, str):
            return None
        if entity_id in self._graph:
            return entity_id
        prefixes = ["VPA:", "PHONE:", "URL:", "CAMPAIGN:", "CASE:", "SIGNAL:", "RING:"]
        for p in prefixes:
            candidate = f"{p}{entity_id}"
            if candidate in self._graph:
                return candidate
            candidate_lower = f"{p}{entity_id.lower().strip()}"
            if candidate_lower in self._graph:
                return candidate_lower
        # Case-insensitive fallback lookup
        entity_lower = entity_id.lower().strip()
        for n in self._graph.nodes():
            if n.lower() == entity_lower or n.split(":", 1)[-1].lower() == entity_lower:
                return n
        return None

    def add_threat_signal(self, signal_data: Dict[str, Any]) -> NodeList:
        """Ingest a threat signal into the graph, creating nodes and linking relationships.

        Returns NodeList containing added node IDs, with dict-like metadata.
        """
        signal_id = signal_data.get("signal_id")
        if not signal_id:
            raise ValueError("signal_data must contain a valid signal_id")

        now_iso = signal_data.get("created_at") or datetime.now(timezone.utc).isoformat()
        severity = signal_data.get("severity", "MEDIUM")
        confidence = float(signal_data.get("confidence", 0.8))
        source = signal_data.get("source", "unknown")
        phone = signal_data.get("phone")
        upi_id = signal_data.get("upi_id")
        url = signal_data.get("url")
        tags = signal_data.get("tags") or []
        raw_content = signal_data.get("raw_content")
        camp_id = signal_data.get("matched_campaign_id") or signal_data.get("campaign_id")
        camp_name = signal_data.get("matched_campaign_name")
        similarity = float(signal_data.get("similarity_score", 0.0) or signal_data.get("similarity", 0.0) or 0.0)
        case_id = signal_data.get("linked_case_id") or signal_data.get("case_id")

        signal_node_id = f"SIGNAL:{signal_id}"
        added_node_ids: List[str] = [signal_node_id]
        added_edge_tuples: List[Tuple[str, str, str]] = []

        with self._lock:
            # 1. Add SIGNAL Node
            self._graph.add_node(
                signal_node_id,
                type="SIGNAL",
                label=f"Signal {signal_id[:12]}",
                signal_id=signal_id,
                source=source,
                severity=severity,
                confidence=confidence,
                tags=tags,
                raw_content=raw_content[:120] if raw_content else None,
                created_at=now_iso,
            )

            # 2. Add PHONE Node & EXTRACTED_FROM Edge
            phone_node_id = None
            if phone:
                phone_clean = phone.strip()
                phone_node_id = f"PHONE:{phone_clean}"
                self._graph.add_node(
                    phone_node_id,
                    type="PHONE",
                    label=phone_clean,
                    phone=phone_clean,
                    severity=severity,
                    created_at=now_iso,
                )
                self._graph.add_edge(
                    phone_node_id,
                    signal_node_id,
                    type="EXTRACTED_FROM",
                    label="EXTRACTED_FROM",
                    created_at=now_iso,
                )
                added_node_ids.append(phone_node_id)
                added_edge_tuples.append((phone_node_id, signal_node_id, "EXTRACTED_FROM"))

            # 3. Add VPA Node & EXTRACTED_FROM Edge
            vpa_node_id = None
            if upi_id:
                vpa_clean = upi_id.lower().strip()
                vpa_node_id = f"VPA:{vpa_clean}"
                self._graph.add_node(
                    vpa_node_id,
                    type="VPA",
                    label=vpa_clean,
                    vpa=vpa_clean,
                    severity=severity,
                    created_at=now_iso,
                )
                self._graph.add_edge(
                    vpa_node_id,
                    signal_node_id,
                    type="EXTRACTED_FROM",
                    label="EXTRACTED_FROM",
                    created_at=now_iso,
                )
                added_node_ids.append(vpa_node_id)
                added_edge_tuples.append((vpa_node_id, signal_node_id, "EXTRACTED_FROM"))

            # 4. Add URL Node & EXTRACTED_FROM Edge
            url_node_id = None
            if url:
                url_clean = url.strip()
                url_node_id = f"URL:{url_clean}"
                self._graph.add_node(
                    url_node_id,
                    type="URL",
                    label=url_clean[:32] + "..." if len(url_clean) > 35 else url_clean,
                    url=url_clean,
                    severity=severity,
                    created_at=now_iso,
                )
                self._graph.add_edge(
                    url_node_id,
                    signal_node_id,
                    type="EXTRACTED_FROM",
                    label="EXTRACTED_FROM",
                    created_at=now_iso,
                )
                added_node_ids.append(url_node_id)
                added_edge_tuples.append((url_node_id, signal_node_id, "EXTRACTED_FROM"))

            # 5. Add ASSOCIATED_WITH Edge between Phone and VPA
            if phone_node_id and vpa_node_id:
                self._graph.add_edge(
                    phone_node_id,
                    vpa_node_id,
                    type="ASSOCIATED_WITH",
                    label="ASSOCIATED_WITH",
                    created_at=now_iso,
                )
                added_edge_tuples.append((phone_node_id, vpa_node_id, "ASSOCIATED_WITH"))

            # 6. Add CAMPAIGN Node & MEMBER_OF_CAMPAIGN Edges
            if camp_id:
                camp_node_id = f"CAMPAIGN:{camp_id}"
                if camp_node_id not in self._graph:
                    self._graph.add_node(
                        camp_node_id,
                        type="CAMPAIGN",
                        label=camp_name or camp_id,
                        campaign_id=camp_id,
                        created_at=now_iso,
                    )
                self._graph.add_edge(
                    signal_node_id,
                    camp_node_id,
                    type="MEMBER_OF_CAMPAIGN",
                    label="MEMBER_OF_CAMPAIGN",
                    similarity=similarity,
                    created_at=now_iso,
                )
                added_edge_tuples.append((signal_node_id, camp_node_id, "MEMBER_OF_CAMPAIGN"))
                if vpa_node_id:
                    self._graph.add_edge(
                        vpa_node_id,
                        camp_node_id,
                        type="MEMBER_OF_CAMPAIGN",
                        label="MEMBER_OF_CAMPAIGN",
                        similarity=similarity,
                        created_at=now_iso,
                    )
                    added_edge_tuples.append((vpa_node_id, camp_node_id, "MEMBER_OF_CAMPAIGN"))
                added_node_ids.append(camp_node_id)

            # 7. Add CASE Node & LINKED_TO_CASE Edges
            if case_id:
                case_node_id = f"CASE:{case_id}"
                if case_node_id not in self._graph:
                    self._graph.add_node(
                        case_node_id,
                        type="CASE",
                        label=f"Case {case_id[:10]}",
                        case_id=case_id,
                        created_at=now_iso,
                    )
                self._graph.add_edge(
                    signal_node_id,
                    case_node_id,
                    type="LINKED_TO_CASE",
                    label="LINKED_TO_CASE",
                    created_at=now_iso,
                )
                added_edge_tuples.append((signal_node_id, case_node_id, "LINKED_TO_CASE"))
                if vpa_node_id:
                    self._graph.add_edge(
                        vpa_node_id,
                        case_node_id,
                        type="LINKED_TO_CASE",
                        label="LINKED_TO_CASE",
                        created_at=now_iso,
                    )
                    added_edge_tuples.append((vpa_node_id, case_node_id, "LINKED_TO_CASE"))
                added_node_ids.append(case_node_id)

        # Deduplicate node IDs while preserving order
        unique_nodes: List[str] = []
        for n in added_node_ids:
            if n not in unique_nodes:
                unique_nodes.append(n)

        return NodeList(
            node_ids=unique_nodes,
            signal_id=signal_id,
            edge_count=len(added_edge_tuples),
            edges=added_edge_tuples,
        )

    def link_vpa_to_case(
        self,
        vpa: str,
        case_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Link a VPA node to an investigative Case node."""
        if not vpa or not case_id:
            return False

        now_iso = datetime.now(timezone.utc).isoformat()
        vpa_clean = vpa.lower().strip()
        vpa_node_id = f"VPA:{vpa_clean}"
        case_node_id = f"CASE:{case_id}"

        with self._lock:
            if vpa_node_id not in self._graph:
                self._graph.add_node(
                    vpa_node_id,
                    type="VPA",
                    label=vpa_clean,
                    vpa=vpa_clean,
                    created_at=now_iso,
                )
            if case_node_id not in self._graph:
                self._graph.add_node(
                    case_node_id,
                    type="CASE",
                    label=f"Case {case_id[:10]}",
                    case_id=case_id,
                    created_at=now_iso,
                )

            edge_attrs: Dict[str, Any] = {
                "type": "LINKED_TO_CASE",
                "label": "LINKED_TO_CASE",
                "created_at": now_iso,
            }
            if metadata:
                edge_attrs.update(metadata)

            self._graph.add_edge(vpa_node_id, case_node_id, **edge_attrs)
            return True

    def link_vpa_to_campaign(
        self,
        vpa: str,
        campaign_id: str,
        similarity: float = 1.0,
    ) -> bool:
        """Link a VPA node to a Campaign node."""
        if not vpa or not campaign_id:
            return False

        now_iso = datetime.now(timezone.utc).isoformat()
        vpa_clean = vpa.lower().strip()
        vpa_node_id = f"VPA:{vpa_clean}"
        camp_node_id = f"CAMPAIGN:{campaign_id}"

        with self._lock:
            if vpa_node_id not in self._graph:
                self._graph.add_node(
                    vpa_node_id,
                    type="VPA",
                    label=vpa_clean,
                    vpa=vpa_clean,
                    created_at=now_iso,
                )
            if camp_node_id not in self._graph:
                self._graph.add_node(
                    camp_node_id,
                    type="CAMPAIGN",
                    label=campaign_id,
                    campaign_id=campaign_id,
                    created_at=now_iso,
                )
            self._graph.add_edge(
                vpa_node_id,
                camp_node_id,
                type="MEMBER_OF_CAMPAIGN",
                label="MEMBER_OF_CAMPAIGN",
                similarity=float(similarity),
                created_at=now_iso,
            )
            return True

    def add_transaction(
        self,
        payer_vpa: str,
        payee_vpa: str,
        amount: float,
        txn_id: Optional[str] = None,
    ) -> bool:
        """Add a financial transfer edge between two VPAs."""
        if not payer_vpa or not payee_vpa:
            return False

        now_iso = datetime.now(timezone.utc).isoformat()
        payer_node = f"VPA:{payer_vpa.lower().strip()}"
        payee_node = f"VPA:{payee_vpa.lower().strip()}"

        with self._lock:
            for node, vpa in [(payer_node, payer_vpa), (payee_node, payee_vpa)]:
                if node not in self._graph:
                    self._graph.add_node(
                        node,
                        type="VPA",
                        label=vpa.lower().strip(),
                        vpa=vpa.lower().strip(),
                        created_at=now_iso,
                    )
            self._graph.add_edge(
                payer_node,
                payee_node,
                type="TRANSACTED_TO",
                label="TRANSACTED_TO",
                amount=float(amount),
                txn_id=txn_id,
                created_at=now_iso,
            )
            return True

    def get_subgraph(self, entity_id: str, depth: int = 2) -> Dict[str, Any]:
        """Extract the k-hop neighborhood around an entity (VPA, Phone, Case, Signal, Campaign)."""
        if not entity_id or not isinstance(entity_id, str):
            return {
                "nodes": [],
                "edges": [],
                "total_nodes": 0,
                "total_edges": 0,
                "target": entity_id,
                "found": False,
            }
        with self._lock:
            target_node = self._resolve_node_id(entity_id)
            if not target_node or target_node not in self._graph:
                return {
                    "nodes": [],
                    "edges": [],
                    "total_nodes": 0,
                    "total_edges": 0,
                    "target": entity_id,
                    "found": False,
                }

            # Use undirected view for symmetric neighborhood traversal
            undirected_view = self._graph.to_undirected(as_view=True)
            ego_g = nx.ego_graph(undirected_view, target_node, radius=max(1, depth))
            subgraph = self._graph.subgraph(ego_g.nodes())

            exported = self._export_graph_object(subgraph)
            exported["target"] = target_node
            exported["found"] = True
            return exported

    def export_graph(self, limit_nodes: Optional[int] = None) -> Dict[str, Any]:
        """Export full graph or capped graph in standard nodes/edges JSON format."""
        with self._lock:
            if limit_nodes is not None and self._graph.number_of_nodes() > limit_nodes:
                # Prioritize nodes with highest degree
                degrees = sorted(self._graph.degree(), key=lambda x: x[1], reverse=True)
                top_nodes = [n for n, _ in degrees[:limit_nodes]]
                subgraph = self._graph.subgraph(top_nodes)
                return self._export_graph_object(subgraph)
            return self._export_graph_object(self._graph)

    def _export_graph_object(self, g: nx.DiGraph) -> Dict[str, Any]:
        """Convert a NetworkX DiGraph instance to standard API dictionary format."""
        nodes_list: List[Dict[str, Any]] = []
        for n, data in g.nodes(data=True):
            node_dict = {
                "id": n,
                "type": data.get("type", "UNKNOWN"),
                "label": data.get("label", n),
                "severity": data.get("severity"),
                "created_at": data.get("created_at"),
            }
            meta = {k: v for k, v in data.items() if k not in ("id", "type", "label", "severity", "created_at")}
            if meta:
                node_dict["metadata"] = meta
            nodes_list.append(node_dict)

        edges_list: List[Dict[str, Any]] = []
        for u, v, data in g.edges(data=True):
            edge_dict = {
                "source": u,
                "target": v,
                "type": data.get("type", "ASSOCIATED_WITH"),
                "label": data.get("label", data.get("type", "")),
                "created_at": data.get("created_at"),
            }
            meta = {k: v for k, v in data.items() if k not in ("source", "target", "type", "label", "created_at")}
            if meta:
                edge_dict["metadata"] = meta
            edges_list.append(edge_dict)

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "total_nodes": len(nodes_list),
            "total_edges": len(edges_list),
            "stats": {
                "nodes_count": len(nodes_list),
                "edges_count": len(edges_list),
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """Compute aggregate graph topology metrics and counts by type."""
        with self._lock:
            nodes_by_type: Dict[str, int] = {t: 0 for t in NODE_TYPES}
            for _, data in self._graph.nodes(data=True):
                nt = data.get("type", "UNKNOWN")
                nodes_by_type[nt] = nodes_by_type.get(nt, 0) + 1

            edges_by_type: Dict[str, int] = {t: 0 for t in EDGE_TYPES}
            for _, _, data in self._graph.edges(data=True):
                et = data.get("type", "UNKNOWN")
                edges_by_type[et] = edges_by_type.get(et, 0) + 1

            total_nodes = self._graph.number_of_nodes()
            total_edges = self._graph.number_of_edges()
            density = round(nx.density(self._graph), 4) if total_nodes > 1 else 0.0

            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "nodes_by_type": nodes_by_type,
                "edges_by_type": edges_by_type,
                "density": density,
            }

    def clear(self) -> None:
        """Clear all nodes and edges from graph."""
        with self._lock:
            self._graph.clear()


_fraud_graph: Optional[FraudGraphService] = None
_graph_singleton_lock = threading.Lock()


def get_fraud_graph() -> FraudGraphService:
    """Obtain or initialize the global thread-safe FraudGraphService singleton."""
    global _fraud_graph
    if _fraud_graph is None:
        with _graph_singleton_lock:
            if _fraud_graph is None:
                _fraud_graph = FraudGraphService()
    return _fraud_graph
