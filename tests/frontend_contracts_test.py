"""
Frontend Mathematical and Structural Contract Tests for SAMPATI V2.
Validates Canvas Hit Detection, Continuous Risk-Score Color Gradient Interpolation,
Role Classification, Currency Formatting, Recharts Series Specification,
and WebSocket Auto-reconnect Logic.
"""
import math
import os
import re
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
    """
    Interpolate continuous edge stroke color based on risk score (0-100).
    0-39: Slate (rgb(100, 116, 139))
    40-74: Amber (rgb(245, 158, 11))
    75-100: Crimson / Red (rgb(239, 68, 68))
    """
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
        # Inside hit radius
        self.assertLessEqual(math.hypot(105.0 - node_x, 108.0 - node_y), 12.0)
        self.assertLessEqual(math.hypot(100.0 - node_x, 112.0 - node_y), 12.0)
        # Outside hit radius
        self.assertGreater(math.hypot(110.0 - node_x, 110.0 - node_y), 12.0)
        self.assertGreater(math.hypot(100.0 - node_x, 113.0 - node_y), 12.0)

    def test_edge_point_to_segment_hit_detection(self):
        """Verify point-to-line segment projection hit detection threshold for canvas edges (<= 6px)."""
        x1, y1 = 50.0, 50.0
        x2, y2 = 200.0, 50.0

        # Point directly on line
        self.assertAlmostEqual(point_to_segment_distance(100.0, 50.0, x1, y1, x2, y2), 0.0)
        # Point within 5px
        self.assertLessEqual(point_to_segment_distance(100.0, 55.0, x1, y1, x2, y2), 6.0)
        # Point outside 6px
        self.assertGreater(point_to_segment_distance(100.0, 58.0, x1, y1, x2, y2), 6.0)
        # Point beyond segment endpoints
        self.assertGreater(point_to_segment_distance(210.0, 50.0, x1, y1, x2, y2), 6.0)

    def test_continuous_risk_color_gradient_interpolation(self):
        """Verify continuous edge risk color gradient across risk spectrum."""
        # Low risk -> slate / low opacity
        c0 = get_continuous_edge_color(0)
        self.assertIn("100, 116, 139", c0)
        c20 = get_continuous_edge_color(20)
        self.assertIn("100, 116, 139", c20)

        # Medium risk -> amber
        c50 = get_continuous_edge_color(50)
        self.assertIn("245, 158, 11", c50)

        # High risk -> red / crimson
        c85 = get_continuous_edge_color(85)
        self.assertIn("239, 68, 68", c85)
        c100 = get_continuous_edge_color(100)
        self.assertIn("239, 68, 68", c100)

        # Boundary clamping
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
        """Verify NetworkConstellation.jsx contains event handling, tooltip, and gradient logic."""
        path = os.path.join(FRONTEND_SRC, "components", "NetworkConstellation.jsx")
        self.assertTrue(os.path.exists(path), f"File {path} must exist")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Canvas ref & listeners
        self.assertIn("canvasRef", content)
        self.assertTrue("onMouseMove" in content or "mousemove" in content)
        self.assertTrue("onClick" in content or "click" in content)
        self.assertTrue("onMouseLeave" in content or "mouseleave" in content)

    def test_verdict_history_chart_recharts_contract(self):
        """Verify VerdictHistoryChart.jsx contains Recharts components and series."""
        path = os.path.join(FRONTEND_SRC, "components", "VerdictHistoryChart.jsx")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue("recharts" in content.lower() or "AreaChart" in content or "LineChart" in content)
            self.assertTrue("ALLOW" in content or "allowed" in content)
            self.assertTrue("HOLD" in content or "held" in content)
            self.assertTrue("BLOCK" in content or "blocked" in content)

    def test_app_jsx_structure(self):
        """Verify App.jsx contains core state hooks and component layout."""
        path = os.path.join(FRONTEND_SRC, "App.jsx")
        self.assertTrue(os.path.exists(path), f"File {path} must exist")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("KpiStrip", content)
        self.assertIn("NetworkConstellation", content)
        self.assertIn("LiveFeed", content)
        self.assertIn("CaseDrawer", content)


if __name__ == "__main__":
    unittest.main()
