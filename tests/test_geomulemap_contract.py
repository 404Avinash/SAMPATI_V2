# Contract tests for GeoMuleMap.jsx, react-simple-maps, and India TopoJSON boundaries.
from __future__ import annotations

import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT, "frontend")
SRC_DIR = os.path.join(FRONTEND_DIR, "src")
GEOMULEMAP_PATH = os.path.join(SRC_DIR, "components", "overview", "GeoMuleMap.jsx")
TOPOJSON_PATH = os.path.join(SRC_DIR, "data", "india-topo.json")
GEOJSON_PATH = os.path.join(SRC_DIR, "data", "india-geojson.json")


class TestGeoMuleMapOfflineContract(unittest.TestCase):

    def test_geomulemap_exists(self):
        self.assertTrue(os.path.exists(GEOMULEMAP_PATH), "GeoMuleMap.jsx must exist")

    def test_react_simple_maps_imports(self):
        with open(GEOMULEMAP_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("react-simple-maps", content, "Must import from react-simple-maps")
        self.assertIn("ComposableMap", content)
        self.assertIn("Geographies", content)
        self.assertIn("Geography", content)
        self.assertIn("Marker", content)
        self.assertIn("Line", content)

    def test_topojson_file_embedded_and_imported(self):
        self.assertTrue(os.path.exists(TOPOJSON_PATH), "india-topo.json must exist")
        with open(GEOMULEMAP_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(
            "india-topo.json" in content or "indiaTopo" in content,
            "Must import india-topo.json",
        )

    def test_no_external_network_requests(self):
        with open(GEOMULEMAP_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        external_patterns = [
            "unpkg.com",
            "cartocdn.com",
            "tile.openstreetmap",
            "mapbox.com",
            "http://",
            "https://",
            "loadLeaflet",
        ]
        for pat in external_patterns:
            self.assertNotIn(
                pat,
                content,
                f"GeoMuleMap.jsx must not reference external resource {pat}",
            )


class TestIndiaTopoJsonValidity(unittest.TestCase):

    def test_topojson_structure_and_bounds(self):
        with open(TOPOJSON_PATH, "r", encoding="utf-8") as f:
            topo = json.load(f)

        self.assertEqual(topo.get("type"), "Topology")
        self.assertIn("objects", topo)
        self.assertIn("india", topo["objects"])
        self.assertIn("arcs", topo)
        self.assertGreaterEqual(len(topo["arcs"]), 1)

        mainland = topo["arcs"][0]
        self.assertGreater(len(mainland), 50, "Mainland boundary should have >= 50 vertices")

        for lon, lat in mainland:
            self.assertGreaterEqual(lon, 68.0, f"Longitude {lon} out of India bounds")
            self.assertLessEqual(lon, 98.0, f"Longitude {lon} out of India bounds")
            self.assertGreaterEqual(lat, 6.0, f"Latitude {lat} out of India bounds")
            self.assertLessEqual(lat, 37.5, f"Latitude {lat} out of India bounds")

    def test_geojson_structure(self):
        self.assertTrue(os.path.exists(GEOJSON_PATH))
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            geo = json.load(f)

        self.assertEqual(geo.get("type"), "FeatureCollection")
        self.assertGreaterEqual(len(geo.get("features", [])), 1)
        feat = geo["features"][0]
        self.assertEqual(feat.get("geometry", {}).get("type"), "MultiPolygon")


class TestGeodeticCoordinatePlotting(unittest.TestCase):

    def test_hubs_lat_lon_geodetic_fidelity(self):
        from app.engine.upi_rules import CITY_COORDINATES

        with open(GEOMULEMAP_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("export const INDIAN_HUBS", content)
        self.assertIn("export const MULE_CORRIDORS", content)

        expected_hubs = {
            "DELHI": (28.70, 77.10),
            "MUMBAI": (19.08, 72.88),
            "KOLKATA": (22.57, 88.36),
            "BENGALURU": (12.97, 77.59),
            "CHENNAI": (13.08, 80.27),
            "HYDERABAD": (17.38, 78.49),
            "AHMEDABAD": (23.02, 72.57),
            "JAMTARA": (24.00, 86.79),
            "MEWAT": (28.06, 76.99),
        }

        for hub_id, (lat, lon) in expected_hubs.items():
            self.assertIn(f'"{hub_id}"', content)
            city_key = hub_id.lower()
            if city_key in CITY_COORDINATES:
                engine_lat, engine_lon = CITY_COORDINATES[city_key]
                self.assertAlmostEqual(lat, engine_lat, delta=0.1)
                self.assertAlmostEqual(lon, engine_lon, delta=0.1)

    def test_corridors_connectivity(self):
        with open(GEOMULEMAP_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("JAMTARA", content)
        self.assertIn("MEWAT", content)
        self.assertIn("CRITICAL", content)
        self.assertIn("HIGH", content)


if __name__ == "__main__":
    unittest.main()
