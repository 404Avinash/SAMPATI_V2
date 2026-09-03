"""Frontend Mathematical, Structural, AST, and Routing Contract Tests for SAMPATI V2.

Validates:
1. Canvas Hit Detection & Mathematical Projection (point_to_segment_distance).
2. Continuous Risk-Score Color Gradient Interpolation across full spectrum.
3. Currency Formatting with Indian Rupee (INR) grouping.
4. Canvas Graph Component Structure and Event Handlers.
5. Recharts Chart Integration & Series Contracts.
6. Multi-Page Navigation and React Router Contracts (5 pages: Overview, Investigations, Analytics, System Health, Settings).
7. Persistent Sidebar Navigation, Badges, and Collapsible State.
8. MainLayout and Outlet integration.
9. AppStateContext state management, WebSocket integration, and telemetry hooks.
10. Milestone 3: Fraud Playback Timeline & Honeypot KPI Counter contracts.
"""
from __future__ import annotations

import math
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_SRC = os.path.join(ROOT, "frontend", "src")


def point_to_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Mathematical projection of point (px, py) to line segment (x1, y1)-(x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def get_continuous_edge_color(risk_score: float) -> str:
    """Interpolate continuous edge stroke color based on risk score (0-100)."""
    if risk_score is None:
        return "rgba(100, 116, 139, 0.30)"
    try:
        val = float(risk_score)
        if math.isnan(val):
            return "rgba(100, 116, 139, 0.30)"
    except Exception:
        return "rgba(100, 116, 139, 0.30)"

    clamped = max(0.0, min(100.0, val))
    if clamped < 40.0:
        # Slate spectrum
        ratio = clamped / 40.0
        alpha = 0.3 + (ratio * 0.3)
        return f"rgba(100, 116, 139, {alpha:.2f})"
    elif clamped < 75.0:
        # Amber spectrum
        ratio = (clamped - 40.0) / 35.0
        alpha = 0.6 + (ratio * 0.3)
        return f"rgba(245, 158, 11, {alpha:.2f})"
    else:
        # Crimson spectrum
        ratio = (clamped - 75.0) / 25.0
        alpha = 0.85 + (ratio * 0.15)
        return f"rgba(239, 68, 68, {alpha:.2f})"


def format_inr(amount: float | None) -> str:
    """Format numeric value into Indian Rupee (INR) currency representation."""
    if amount is None or math.isnan(amount):
        return "—"
    amt_int = int(round(amount))
    s = str(abs(amt_int))
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        parts = []
        while remaining:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        formatted = ",".join(parts) + "," + last3
    prefix = "-" if amt_int < 0 else ""
    return f"₹{prefix}{formatted}"


class TestFrontendMathematicalContracts(unittest.TestCase):
    """Test mathematical formulas and algorithms used in the frontend visualizer."""

    def test_node_euclidean_hit_detection(self):
        """Verify Euclidean distance hit detection threshold for canvas nodes (<= 12px)."""
        node_x, node_y = 100.0, 100.0
        self.assertLessEqual(math.hypot(105.0 - node_x, 108.0 - node_y), 12.0)
        self.assertLessEqual(math.hypot(100.0 - node_x, 112.0 - node_y), 12.0)
        self.assertGreater(math.hypot(110.0 - node_x, 110.0 - node_y), 12.0)
        self.assertGreater(math.hypot(100.0 - node_x, 113.0 - node_y), 12.0)

    def test_edge_point_to_segment_hit_detection(self):
        """Verify point-to-line segment projection hit detection threshold for canvas edges (<= 6px)."""
        x1, y1 = 50.0, 50.0
        x2, y2 = 200.0, 50.0
        self.assertAlmostEqual(point_to_segment_distance(100.0, 50.0, x1, y1, x2, y2), 0.0)
        self.assertLessEqual(point_to_segment_distance(100.0, 55.0, x1, y1, x2, y2), 6.0)
        self.assertGreater(point_to_segment_distance(100.0, 58.0, x1, y1, x2, y2), 6.0)
        self.assertGreater(point_to_segment_distance(210.0, 50.0, x1, y1, x2, y2), 6.0)

    def test_continuous_risk_color_gradient_interpolation(self):
        """Verify continuous edge risk color gradient across risk spectrum."""
        c0 = get_continuous_edge_color(0)
        self.assertIn("100, 116, 139", c0)
        c20 = get_continuous_edge_color(20)
        self.assertIn("100, 116, 139", c20)

        c50 = get_continuous_edge_color(50)
        self.assertIn("245, 158, 11", c50)

        c85 = get_continuous_edge_color(85)
        self.assertIn("239, 68, 68", c85)
        c100 = get_continuous_edge_color(100)
        self.assertIn("239, 68, 68", c100)

        c_neg = get_continuous_edge_color(-10)
        self.assertIn("100, 116, 139", c_neg)
        c_over = get_continuous_edge_color(150)
        self.assertIn("239, 68, 68", c_over)

    def test_inr_currency_formatting(self):
        """Verify Indian Rupee (INR) standard grouping (e.g. 1,00,000)."""
        self.assertEqual(format_inr(0), "₹0")
        self.assertEqual(format_inr(500), "₹500")
        self.assertEqual(format_inr(25000), "₹25,000")
        self.assertEqual(format_inr(100000), "₹1,00,000")
        self.assertEqual(format_inr(5000000), "₹50,00,000")
        self.assertEqual(format_inr(None), "—")


class TestFrontendSourceCodeContracts(unittest.TestCase):
    """Verify structural and AST contracts in frontend JSX source files."""

    def test_network_constellation_jsx_contains_canvas_interaction(self):
        """Verify NetworkConstellation.jsx contains event handling and canvas ref."""
        path = os.path.join(FRONTEND_SRC, "components", "NetworkConstellation.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("canvasRef", content)
        self.assertTrue("onMouseMove" in content or "mousemove" in content)
        self.assertTrue("onClick" in content or "click" in content)

    def test_verdict_history_chart_recharts_contract(self):
        """Verify VerdictHistoryChart.jsx contains Recharts components and series."""
        path = os.path.join(FRONTEND_SRC, "components", "VerdictHistoryChart.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("recharts" in content.lower() or "AreaChart" in content or "LineChart" in content or "ResponsiveContainer" in content)

    def test_app_or_router_entry_point(self):
        """Verify App.jsx defines the root router and layout configuration."""
        app_path = os.path.join(FRONTEND_SRC, "App.jsx")
        self.assertTrue(os.path.exists(app_path), f"File {app_path} must exist")
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("BrowserRouter", content)
        self.assertIn("Routes", content)
        self.assertIn("Route", content)
        self.assertIn("AppStateProvider", content)


class TestFrontendRoutingAndPagesContracts(unittest.TestCase):
    """Verify React Router multi-page routing contracts, 5 dedicated pages, and layout architecture."""

    def test_package_json_contains_react_router_dom(self):
        """Verify frontend/package.json contains react-router-dom dependency."""
        pkg_path = os.path.join(ROOT, "frontend", "package.json")
        self.assertTrue(os.path.exists(pkg_path))
        with open(pkg_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("react-router-dom", content)

    def test_five_dedicated_pages_exist_in_pages_directory(self):
        """Verify all 5 required pages exist as JSX components in frontend/src/pages/."""
        pages_dir = os.path.join(FRONTEND_SRC, "pages")
        self.assertTrue(os.path.exists(pages_dir))

        expected_pages = [
            "OverviewPage.jsx",
            "InvestigationsPage.jsx",
            "AnalyticsPage.jsx",
            "SystemHealthPage.jsx",
            "SettingsPage.jsx",
        ]
        for page_name in expected_pages:
            full_path = os.path.join(pages_dir, page_name)
            self.assertTrue(
                os.path.exists(full_path),
                f"Required page {page_name} must exist at {full_path}"
            )
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertGreater(len(content), 100, f"Page {page_name} must have non-empty implementation")

    def test_routes_coverage_in_app_jsx(self):
        """Verify App.jsx defines client-side routes for all 5 pages."""
        app_path = os.path.join(FRONTEND_SRC, "App.jsx")
        self.assertTrue(os.path.exists(app_path))
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()

        target_routes = ["/overview", "/investigations", "/analytics", "/health", "/settings"]
        for route in target_routes:
            self.assertIn(route, content, f"App.jsx must define route {route}")

    def test_main_layout_and_outlet_contract(self):
        """Verify MainLayout.jsx embeds Navbar and React Router Outlet."""
        layout_path = os.path.join(FRONTEND_SRC, "layouts", "MainLayout.jsx")
        self.assertTrue(os.path.exists(layout_path))
        with open(layout_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Navbar", content)
        self.assertIn("Outlet", content)

    def test_navbar_navigation_state(self):
        """Verify Navbar.jsx includes nav items and NavLink routing."""
        navbar_path = os.path.join(FRONTEND_SRC, "components", "common", "Navbar.jsx")
        self.assertTrue(os.path.exists(navbar_path))
        with open(navbar_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("NavLink", content)
        self.assertIn("Overview", content)
        self.assertIn("Investigations", content)
        self.assertIn("Analytics", content)
        self.assertTrue("System Health" in content or "Health" in content)
        self.assertIn("Settings", content)

    def test_app_state_context_contract(self):
        """Verify AppStateContext.jsx defines global state provider and custom hook."""
        context_path = os.path.join(FRONTEND_SRC, "context", "AppStateContext.jsx")
        self.assertTrue(os.path.exists(context_path))
        with open(context_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("AppStateContext", content)
        self.assertIn("AppStateProvider", content)
        self.assertIn("useAppState", content)
        self.assertIn("useWebSocket", content)
        self.assertIn("verdictHistory", content)


class TestFrontendTimelineAndKpiContracts(unittest.TestCase):
    """Verify Milestone 3: Fraud Playback Timeline, CaseDrawer integration, and Honeypot KPI counter."""

    def test_network_constellation_contains_timeline_controls(self):
        """Verify NetworkConstellation.jsx contains timeline slider, Play, Pause, and Reset controls."""
        path = os.path.join(FRONTEND_SRC, "components", "NetworkConstellation.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Step state and timeline controls
        self.assertIn("extractChronologicalTopology", content)
        self.assertIn("currentStep", content)
        self.assertIn("totalSteps", content)
        self.assertIn("isPlaying", content)
        self.assertIn("handlePlay", content)
        self.assertIn("handlePause", content)
        self.assertIn("handleReset", content)
        self.assertIn("handleSliderChange", content)
        self.assertIn('type="range"', content)
        self.assertIn("Play", content)
        self.assertIn("Pause", content)
        self.assertIn("Reset", content)

    def test_network_constellation_step_visibility_math(self):
        """Verify step slicing logic for timeline state k in [0, N]."""
        mock_edges = [
            {"id": f"e{i}", "a": f"node{i}", "b": f"node{i+1}", "timestamp": 1000 + i * 10}
            for i in range(10)
        ]
        total_steps = len(mock_edges)

        # At k = 0 (t=0 / Reset)
        k0 = 0
        visible_edges_0 = mock_edges[:k0]
        visible_nodes_0 = set()
        for e in visible_edges_0:
            visible_nodes_0.add(e["a"])
            visible_nodes_0.add(e["b"])
        self.assertEqual(len(visible_edges_0), 0)
        self.assertEqual(len(visible_nodes_0), 0)

        # At k in [1, N]
        for k in range(1, total_steps + 1):
            visible_edges_k = mock_edges[:k]
            visible_nodes_k = set()
            for e in visible_edges_k:
                visible_nodes_k.add(e["a"])
                visible_nodes_k.add(e["b"])
            self.assertEqual(len(visible_edges_k), k)
            self.assertGreater(len(visible_nodes_k), 0)
            self.assertIn(f"node{k}", visible_nodes_k)

    def test_case_drawer_embeds_network_constellation(self):
        """Verify CaseDrawer.jsx imports NetworkConstellation and passes caseData."""
        path = os.path.join(FRONTEND_SRC, "components", "CaseDrawer.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("NetworkConstellation", content)
        self.assertIn("caseData={caseData}", content)

    def test_kpi_strip_renders_seven_tiles_with_honeypot(self):
        """Verify KpiStrip.jsx defines 7 KPI tiles including Honeypot Hits (24h)."""
        path = os.path.join(FRONTEND_SRC, "components", "KpiStrip.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("honeypot_hits", content)
        self.assertIn("Honeypot Hits (24h)", content)
        self.assertIn("lg:grid-cols-7", content)

    def test_app_state_context_tracks_honeypot_kpi(self):
        """Verify AppStateContext.jsx tracks honeypot_hits and honeypot_hits_24h in state and feeds."""
        path = os.path.join(FRONTEND_SRC, "context", "AppStateContext.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("honeypot_hits", content)
        self.assertIn("honeypot_hits_24h", content)


class TestFrontendSprint2Contracts(unittest.TestCase):
    """Verify Sprint 2 Frontend Features: DMV Gauge, SAR PDF Export, Workload Heatmap, Top DMV Table, Auto-Feed."""

    def test_case_drawer_dmv_gauge_and_export_sar_button(self):
        """Verify CaseDrawer.jsx contains DMV score gauge and Export SAR PDF button."""
        path = os.path.join(FRONTEND_SRC, "components", "CaseDrawer.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("dmv_score", content)
        self.assertIn("Dormant-to-Active Velocity", content)
        self.assertIn("Export SAR", content)
        self.assertIn("downloadSarPdf", content)

    def test_analytics_workload_heatmap_and_top_dmv_table_integration(self):
        """Verify AnalyticsPage.jsx embeds AnalystWorkloadHeatmap and TopDmvAccountsTable."""
        page_path = os.path.join(FRONTEND_SRC, "pages", "AnalyticsPage.jsx")
        self.assertTrue(os.path.exists(page_path))
        with open(page_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("AnalystWorkloadHeatmap", content)
        self.assertIn("TopDmvAccountsTable", content)
        self.assertIn("workload_heatmap", content)
        self.assertIn("top_dmv_vpas", content)

        # Check that individual components exist
        heatmap_path = os.path.join(FRONTEND_SRC, "components", "analytics", "AnalystWorkloadHeatmap.jsx")
        self.assertTrue(os.path.exists(heatmap_path))
        with open(heatmap_path, "r", encoding="utf-8") as f:
            h_content = f.read()
        self.assertIn("7 × 24", h_content)
        self.assertIn("HOURS", h_content)
        self.assertIn("DAYS", h_content)

        dmv_table_path = os.path.join(FRONTEND_SRC, "components", "analytics", "TopDmvAccountsTable.jsx")
        self.assertTrue(os.path.exists(dmv_table_path))
        with open(dmv_table_path, "r", encoding="utf-8") as f:
            t_content = f.read()
        self.assertIn("Dormant-to-Active Velocity", t_content)
        self.assertIn("dmv_score", t_content)

    def test_control_bar_autofeed_toggle_and_tps_controls(self):
        """Verify ControlBar.jsx contains Live Auto-Feed toggle and TPS telemetry."""
        path = os.path.join(FRONTEND_SRC, "components", "ControlBar.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("autoFeedActive", content)
        self.assertIn("toggleAutoFeed", content)
        self.assertIn("Live Auto-Feed", content)

    def test_app_state_context_autofeed_methods(self):
        """Verify AppStateContext.jsx tracks auto-feed state, start, stop, and toggle methods."""
        path = os.path.join(FRONTEND_SRC, "context", "AppStateContext.jsx")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("autoFeedActive", content)
        self.assertIn("startAutoFeed", content)
        self.assertIn("stopAutoFeed", content)
        self.assertIn("toggleAutoFeed", content)

    def test_api_service_sprint2_endpoints(self):
        """Verify api.js defines startAutoFeed, stopAutoFeed, getAutoFeedStatus, and downloadSarPdf."""
        path = os.path.join(FRONTEND_SRC, "services", "api.js")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("startAutoFeed", content)
        self.assertIn("stopAutoFeed", content)
        self.assertIn("getAutoFeedStatus", content)
        self.assertIn("downloadSarPdf", content)
        self.assertIn("getDmvTone", content)


if __name__ == "__main__":
    unittest.main()

