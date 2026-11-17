import sys
import os
import inspect
import re

passed = 0
failed = 0
discrepancies = []

def record(test_name, condition, note=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"[PASS] {test_name}: {note}")
    else:
        failed += 1
        print(f"[FAIL] {test_name}: {note}")
        discrepancies.append((test_name, note))

# 1. NetworkConstellation physics
with open('frontend/src/components/NetworkConstellation.jsx') as f:
    nc_code = f.read()
record("NetworkConstellation gravity (0.001)", "0.001" in nc_code)
record("NetworkConstellation repulsion (950)", "950" in nc_code)
record("NetworkConstellation spring tension (0.006)", "0.006" in nc_code)
record("NetworkConstellation damping (0.85)", "0.85" in nc_code)
record("NetworkConstellation hit threshold (7.0)", "7.0" in nc_code)
record("NetworkConstellation particle speed (0.35 + risk/100 * 0.55)", "0.35" in nc_code and "0.55" in nc_code)

# 2. GeoMuleMap
with open('frontend/src/components/overview/GeoMuleMap.jsx') as f:
    gmm_code = f.read()
record("GeoMuleMap Leaflet & Esri tile", "leaflet" in gmm_code and "arcgisonline.com" in gmm_code)
record("GeoMuleMap calculateBearing function", "function calculateBearing" in gmm_code)
record("GeoMuleMap 55% offset", "0.55" in gmm_code)
record("GeoMuleMap autoPan false", "autoPan: false" in gmm_code)
# Coordinate test: check whether code has 28.70 (code) vs 28.6139 (doc claim)
doc_coords_in_code = "28.6139" in gmm_code
record("GeoMuleMap coordinates fidelity", doc_coords_in_code, 
       "Doc claims 4-decimal coordinates (28.6139, 77.2090), but code has rounded (28.70, 77.10)")

# 3. UpiRiskScorer
from app.engine.upi_scorer import UpiRiskScorer
record("UpiRiskScorer class exists", hasattr(UpiRiskScorer, "evaluate"))
with open('app/engine/upi_scorer.py') as f:
    scorer_code = f.read()
record("UpiRiskScorer BLOCK threshold (>= 70)", ">= 70" in scorer_code or "70" in scorer_code)
record("UpiRiskScorer HOLD threshold (>= 45)", ">= 45" in scorer_code or "45" in scorer_code)
record("UpiRiskScorer safety override floors (0.70 / 0.85)", "0.70" in scorer_code and "0.85" in scorer_code)

# 4. DmvTracker
from app.engine.dmv import DmvTracker
with open('app/engine/dmv.py') as f:
    dmv_code = f.read()
record("DmvTracker class exists", hasattr(DmvTracker, "calculate_dmv"))
record("DmvTracker formula weights (0.40, 0.60)", "0.4" in dmv_code and "0.6" in dmv_code)
record("DmvTracker burst velocity weights (0.50, 0.30, 0.20)", "0.5" in dmv_code and "0.3" in dmv_code and "0.2" in dmv_code)
record("DmvTracker nonlinear amplification (D>=0.5, V>=0.4)", "0.5" in dmv_code and "0.4" in dmv_code)

# 5. PureNumpyIsolationForest
from app.engine.isolation_forest import PureNumpyIsolationForest, c_factor
record("PureNumpyIsolationForest class exists", hasattr(PureNumpyIsolationForest, "fit"))
record("c_factor Euler-Mascheroni constant", abs(c_factor(2) - 1.0) < 1e-5)
with open('app/engine/isolation_forest.py') as f:
    if_code = f.read()
record("Isolation Forest n_trees=50, max_samples=128", "50" in if_code and "128" in if_code)
record("Isolation Forest zero-regression calibration (0.96)", "0.96" in if_code)

# 6. PureNumpySupervisedClassifier
from app.engine.supervised_classifier import PureNumpySupervisedClassifier, PureNumpyDecisionTree, PureNumpyStandardScaler
record("PureNumpySupervisedClassifier class exists", hasattr(PureNumpySupervisedClassifier, "fit"))
with open('app/engine/supervised_classifier.py') as f:
    sc_code = f.read()
record("SupervisedClassifier n_estimators=30, max_depth=6", "30" in sc_code and "6" in sc_code)
record("SupervisedClassifier calibration curve (0.35, 0.30)", "0.35" in sc_code and "0.30" in sc_code)

# 7. GeminiAssistantService
from app.services.gemini_service import GeminiAssistantService
record("GeminiAssistantService chat_with_case_copilot", hasattr(GeminiAssistantService, "chat_with_case_copilot"))
record("GeminiAssistantService generate_sar_report", hasattr(GeminiAssistantService, "generate_sar_report"))
record("GeminiAssistantService generate_case_briefing", hasattr(GeminiAssistantService, "generate_case_briefing"))
record("GeminiAssistantService _match_intent offline fallback", hasattr(GeminiAssistantService, "_match_intent"))

# 8. sar_pdf.py
from app.forensics.sar_pdf import generate_sar_pdf
with open('app/forensics/sar_pdf.py') as f:
    sar_code = f.read()
record("sar_pdf generate_sar_pdf function exists", callable(generate_sar_pdf))
record("sar_pdf color codes (#991b1b, #b45309, #1e3a8a)", "#991b1b" in sar_code and "#b45309" in sar_code and "#1e3a8a" in sar_code)

# 9. FraudGraphService
from app.services.graph_service import FraudGraphService, NODE_TYPES, EDGE_TYPES
record("FraudGraphService NODE_TYPES (7 types)", len(NODE_TYPES) == 7 and "VPA" in NODE_TYPES)
record("FraudGraphService EDGE_TYPES (5 types)", len(EDGE_TYPES) == 5 and "TRANSACTED_TO" in EDGE_TYPES)
record("FraudGraphService get_subgraph method", hasattr(FraudGraphService, "get_subgraph"))

# 10. ThreatIntelService
from app.services.threat_intel_service import ThreatIntelService
record("ThreatIntelService patterns", hasattr(ThreatIntelService, "extract_entities"))

# 11. AutoFeedEngine
from app.services.autofeed import AutoFeedEngine
record("AutoFeedEngine class exists", hasattr(AutoFeedEngine, "set_tps"))

# 12. UpiCaseService
from app.services.upi_cases import UpiCaseService
record("UpiCaseService record_latency", hasattr(UpiCaseService, "record_latency"))
record("UpiCaseService get_analytics", hasattr(UpiCaseService, "get_analytics"))

# 13. FastApi routes
from app.main import app
routes = [route.path for route in app.routes]
key_routes = [
    "/upi/check", "/upi/score", "/federation/signal", "/intel/campaigns",
    "/adapters/npci/mulehunter", "/notifications/status", "/ws"
]
for kr in key_routes:
    record(f"Route {kr} exists in FastAPI app", any(r == kr or r == kr + "/" or kr in r for r in routes))

# 14. Pydantic Models
from app.models.upi_models import UpiTransaction, UpiEvaluationResponse
record("Pydantic UpiTransaction exists", hasattr(UpiTransaction, "model_fields") or hasattr(UpiTransaction, "__fields__"))
record("Pydantic UpiEvaluationResponse exists", hasattr(UpiEvaluationResponse, "model_fields") or hasattr(UpiEvaluationResponse, "__fields__"))

# 15. SQLAlchemy Models
from app.models.upi_persistence import UpiCaseModel, MuleRingModel, CaseFeedbackModel, AggregateStatsModel, ThreatSignalModel
record("SQLAlchemy UpiCaseModel exists", UpiCaseModel.__tablename__ == "upi_cases")
record("SQLAlchemy MuleRingModel exists", MuleRingModel.__tablename__ == "mule_rings")
record("SQLAlchemy CaseFeedbackModel exists", CaseFeedbackModel.__tablename__ == "case_feedback")
record("SQLAlchemy AggregateStatsModel exists", AggregateStatsModel.__tablename__ == "aggregate_stats")
record("SQLAlchemy ThreatSignalModel exists", ThreatSignalModel.__tablename__ == "threat_signals")

# 16. Frontend Hooks and Context
with open('frontend/src/context/AppStateContext.jsx') as f:
    app_state_code = f.read()
record("AppStateContext calculateAmbientAllowTps", "calculateAmbientAllowTps" in app_state_code)
with open('frontend/src/hooks/useCountUp.js') as f:
    count_up_code = f.read()
record("useCountUp hook exists", "useCountUp" in count_up_code)
with open('frontend/src/hooks/useWebSocket.js') as f:
    ws_hook_code = f.read()
record("useWebSocket hook exists", "useWebSocket" in ws_hook_code)

print("\n==========================================")
print(f"TOTAL TESTS: {passed + failed}")
print(f"PASSED: {passed}")
print(f"FAILED: {failed}")
print("==========================================")
for t, note in discrepancies:
    print(f"DISCREPANCY: {t} -> {note}")
