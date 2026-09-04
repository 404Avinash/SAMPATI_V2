"""Pydantic Models and Pure-Python Regex Entity Extractor for SAMPATI V2 Threat Intelligence."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field, model_validator
    PYDANTIC_V2 = True
except ImportError:
    PYDANTIC_V2 = False
    from app.models.upi_models import BaseModel, Field  # type: ignore

    def model_validator(*args, **kwargs):  # type: ignore
        def decorator(f):
            return f
        return decorator


def utcnow_iso() -> str:
    """Return current UTC ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ── Robust Regex Compilations for Indian Fraud Vectors ────────────────────────

# 1. Indian Phone Numbers: 10 digits starting with 6, 7, 8, or 9
# Handles optional +91, 91, or 0 prefixes with space/hyphen formatting.
# Negative lookahead/lookbehind prevents matching 12-digit UPI UTRs or amounts.
PHONE_REGEX = re.compile(
    r"(?<!\d)(?:\+?91[\s\-]?)?(?:0[\s\-]?)?([6-9]\d{4}[\s\-]?\d{5}|[6-9]\d{2}[\s\-]?\d{3}[\s\-]?\d{4}|[6-9]\d{9})(?!\d)"
)

# 2. UPI IDs (VPAs): [username]@[handle]
# Excludes standard email provider domains (gmail.com, etc.), subdomains, and web TLDs.
UPI_REGEX = re.compile(
    r"\b([a-zA-Z0-9.\-_]{2,64}@(?!(?:gmail|yahoo|outlook|hotmail|proton|icloud|mail)\.com\b)(?![a-zA-Z0-9_\-]+\.[a-zA-Z0-9.\-]+\b)(?![a-zA-Z0-9_\-]+\.(?:com|in|co\.in|org|net|edu|gov)\b)[a-zA-Z][a-zA-Z0-9_\-]{1,32})\b(?!\.[a-zA-Z0-9])",
    re.IGNORECASE,
)

# 3. Malicious URLs and Phishing Domains:
# Matches http/https, IP endpoints, www, and high-risk fraud TLDs.
# Negative lookbehind (?<!@) avoids matching domain portions of email addresses.
URL_REGEX = re.compile(
    r"(https?://(?:(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?|[a-zA-Z0-9.\-]+)[^\s<>\"'{}|\\^`\[\]]*|"
    r"www\.[a-zA-Z0-9.\-]+[^\s<>\"'{}|\\^`\[\]]*|"
    r"(?<!@)\b[a-zA-Z0-9\-]+\.(?:com|in|co\.in|org|net|xyz|top|site|online|live|info|app|cc|club)(?:/[^\s<>\"'{}|\\^`\[\]]*)?)",
    re.IGNORECASE,
)

# 4. Standard Indian Social Engineering Tags
TAG_PATTERNS: Dict[str, re.Pattern] = {
    "Bank impersonation": re.compile(
        r"\b(?:sbi|state\s+bank|hdfc|icici|axis|pnb|punjab\s+national\s+bank|bob|bank\s+of\s+baroda|kotak|canara|union\s+bank|indusind|rbi|reserve\s+bank|netbanking|debit\s+card|credit\s+card|bank\s+account|customer\s+care)\b",
        re.IGNORECASE,
    ),
    "KYC suspension": re.compile(
        r"\b(?:kyc|pan(?:\s+card|\s+update|\s+link|\s+verification)?|aadhaar|aadhar|unblock|blocked|suspended|reactivate|update\s+kyc|kyc\s+expired?)\b",
        re.IGNORECASE,
    ),
    "Urgency": re.compile(
        r"\b(?:immediately|urgent|urgently|expire[sd]?|expiring|tonight|24\s*hours?|today\s+only|instant|warning|alert|attention|action\s+required|last\s+chance|final\s+reminder)\b",
        re.IGNORECASE,
    ),
    "Lottery/Reward": re.compile(
        r"\b(?:lottery|reward[s]?|prize|won|winner|congratulations|cashback|bonus|lucky\s+draw|gift|kbc|crore|lakh)\b",
        re.IGNORECASE,
    ),
    "Electricity/Bill": re.compile(
        r"\b(?:electricity|power(?:\s+supply)?|bill\s+unpaid|disconnection|disconnect(?:ed)?|light\s+bill|eb\s+bill|bijli|bescom|mseb|bses)\b",
        re.IGNORECASE,
    ),
    "APK/Malware": re.compile(
        r"\b(?:\.apk|install(?:\s+app)?|download\s+app|anydesk|teamviewer|rustdesk|quicksupport|security\s+update|malware)\b",
        re.IGNORECASE,
    ),
    "Investment/Job": re.compile(
        r"\b(?:part\s*time|work\s+from\s+home|telegram(?:\s+task)?|investment|invest|crypto|daily\s+income|earn\s+money|double\s+money|investment\s+scam)\b",
        re.IGNORECASE,
    ),
    "Refund/Delivery": re.compile(
        r"\b(?:refund|courier|speed\s+post|parcel|delivery\s+failed|address\s+update|customs(?:\s+fee)?|india\s+post)\b",
        re.IGNORECASE,
    ),
}


# ── Standalone Pure-Python Entity Extractor ───────────────────────────────────

def extract_entities(text: Optional[str]) -> ExtractedEntities:
    """Extract Indian phone numbers, UPI VPAs, URLs, and social engineering tags from raw text."""
    if not text:
        return ExtractedEntities()

    # Extract Phone numbers
    phones: List[str] = []
    for m in PHONE_REGEX.finditer(text):
        raw = m.group(1)
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 10 and digits[0] in "6789":
            canonical = f"+91{digits}"
            if canonical not in phones:
                phones.append(canonical)

    # Extract UPI VPAs
    upis: List[str] = []
    for m in UPI_REGEX.finditer(text):
        vpa = m.group(1).rstrip(".,;:!?")
        if vpa.lower() not in [u.lower() for u in upis]:
            upis.append(vpa)

    # Extract URLs
    urls: List[str] = []
    for m in URL_REGEX.finditer(text):
        u = m.group(1).rstrip(".,;:!?>\"'")
        while u.endswith(")") and u.count(")") > u.count("("):
            u = u[:-1].rstrip(".,;:!?>\"'")
        if "(" not in u:
            u = u.rstrip(".,;:!?)>\"'")
        if u and u not in urls:
            urls.append(u)

    # Extract Social Engineering Tags
    tags: List[str] = []
    for tag_name, pattern in TAG_PATTERNS.items():
        if pattern.search(text) and tag_name not in tags:
            tags.append(tag_name)

    return ExtractedEntities(
        phones=phones,
        upi_ids=upis,
        urls=urls,
        tags=tags,
        primary_phone=phones[0] if phones else None,
        primary_upi_id=upis[0] if upis else None,
        primary_url=urls[0] if urls else None,
    )


# Function alias for consistency with external test callers
extract_entities_from_text = extract_entities


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ExtractedEntities(BaseModel):
    """Structured forensic entities extracted from raw unstructured content."""
    phones: List[str] = Field(default_factory=list, description="Extracted phone numbers in canonical format (+91XXXXXXXXXX)")
    upi_ids: List[str] = Field(default_factory=list, description="Extracted UPI Virtual Payment Addresses")
    urls: List[str] = Field(default_factory=list, description="Extracted suspicious URLs or domains")
    tags: List[str] = Field(default_factory=list, description="Extracted social engineering detection tags")
    primary_phone: Optional[str] = Field(default=None, description="Primary detected phone number")
    primary_upi_id: Optional[str] = Field(default=None, description="Primary detected UPI VPA")
    primary_url: Optional[str] = Field(default=None, description="Primary detected URL")


class ThreatSignalCreateRequest(BaseModel):
    """Request payload for ingesting a pre-transaction threat signal."""
    source: str = Field(default="external", description="Signal origin: mobile_app, psp_feed, user_report, telecom_feed, honeypot")
    phone: Optional[str] = Field(default=None, description="Reported or extracted phone number")
    upi_id: Optional[str] = Field(default=None, description="Reported or extracted UPI VPA")
    url: Optional[str] = Field(default=None, description="Reported or extracted malicious URL")
    tags: List[str] = Field(default_factory=list, description="Scam/social engineering tags")
    raw_content: Optional[str] = Field(default=None, description="Unstructured SMS text, phishing message, or call transcript")
    severity: str = Field(default="MEDIUM", description="Assessed signal severity: LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence score in [0.0, 1.0]")

    @classmethod
    def _validate_and_normalize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize fields, auto-extract entities, and validate constraints."""
        raw = data.get("raw_content")
        phone = data.get("phone")
        upi_id = data.get("upi_id")
        url = data.get("url")
        tags = data.get("tags") or []

        # Auto-extract entities from raw_content if explicit identifiers are absent
        if raw and isinstance(raw, str) and raw.strip():
            extracted = extract_entities(raw)
            if not phone and extracted.primary_phone:
                phone = extracted.primary_phone
                data["phone"] = phone
            if not upi_id and extracted.primary_upi_id:
                upi_id = extracted.primary_upi_id
                data["upi_id"] = upi_id
            if not url and extracted.primary_url:
                url = extracted.primary_url
                data["url"] = url
            if extracted.tags:
                merged = list(tags)
                for t in extracted.tags:
                    if t not in merged:
                        merged.append(t)
                tags = merged
                data["tags"] = tags

        # Rejection: missing all identifiers and non-empty raw_content
        has_identifier = bool(phone or upi_id or url or (raw and isinstance(raw, str) and raw.strip()))
        if not has_identifier:
            raise ValueError("At least one identifier (phone, upi_id, url) or raw_content must be provided")

        # Validate severity
        severity = data.get("severity", "MEDIUM")
        valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if severity not in valid_severities:
            raise ValueError(f"Invalid severity '{severity}'. Must be one of: {', '.join(sorted(valid_severities))}")

        # Defensible confidence capping: cap at 0.98 to strip 100% certainty claims
        conf = data.get("confidence", 0.85)
        if conf is not None:
            try:
                conf_f = float(conf)
                if conf_f > 0.98:
                    data["confidence"] = 0.98
                elif conf_f < 0.0:
                    data["confidence"] = 0.0
            except (TypeError, ValueError):
                pass

        return data

    @model_validator(mode="before")
    @classmethod
    def _validate_before(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return cls._validate_and_normalize_dict(data)
        return data

    def __init__(self, **data: Any):
        norm_data = self._validate_and_normalize_dict(dict(data))
        super().__init__(**norm_data)


class StandardFraudSignal(ThreatSignalCreateRequest):
    """Standardized fraud signal format produced by PSP and institutional adapters."""
    institution: Optional[str] = Field(default=None, description="Originating financial institution or PSP name (e.g. PhonePe, Paytm, NPCI, DPIP)")
    anomaly_type: Optional[str] = Field(default=None, description="Typology or anomaly category (e.g. velocity_anomaly, suspicious_beneficiary)")

    @classmethod
    def from_psp(
        cls,
        psp: str,
        vpa: str,
        anomaly_type: str = "velocity_anomaly",
        severity: str = "HIGH",
        confidence: float = 0.88,
        details: Optional[str] = None,
        phone: Optional[str] = None,
        url: Optional[str] = None,
    ) -> StandardFraudSignal:
        """Create a standardized fraud signal originating from a mock PSP engine."""
        clean_psp = psp.strip() if psp else "PSP"
        tags = [f"PSP:{clean_psp}", anomaly_type.replace("_", " ").title(), "Pre-transaction alert"]
        raw_msg = details or f"[{clean_psp} Fraud Engine] Flagged {anomaly_type.replace('_', ' ')} for VPA {vpa}."
        source = f"psp_{clean_psp.lower().replace(' ', '')}"
        return cls(
            source=source,
            institution=clean_psp,
            anomaly_type=anomaly_type,
            upi_id=vpa,
            phone=phone,
            url=url,
            tags=tags,
            raw_content=raw_msg,
            severity=severity,
            confidence=confidence,
        )

    @classmethod
    def from_npci(
        cls,
        vpa: str,
        mule_probability: float,
        flags: Optional[List[str]] = None,
        severity: str = "HIGH",
    ) -> StandardFraudSignal:
        """Create a standardized fraud signal originating from NPCI MuleHunter."""
        flags_list = flags or ["CENTRAL_SWITCH_FLAG"]
        tags = ["NPCI:MuleHunter", "Central Switch Flag"] + flags_list[:2]
        raw_msg = f"[NPCI Central Switch] MuleHunter probability {round(mule_probability, 2)} with flags: {', '.join(flags_list)}."
        return cls(
            source="npci_mulehunter",
            institution="NPCI",
            anomaly_type="mule_cluster",
            upi_id=vpa,
            tags=tags,
            raw_content=raw_msg,
            severity=severity,
            confidence=min(0.98, max(0.5, mule_probability)),
        )

    @classmethod
    def from_dpip(
        cls,
        vpa_or_hash: str,
        threat_level: str = "HIGH",
        threat_score: float = 0.90,
        reporting_agencies: Optional[List[str]] = None,
    ) -> StandardFraudSignal:
        """Create a standardized fraud signal originating from DPIP Smart Registry."""
        agencies = reporting_agencies or ["NATIONAL_CYBER_CRIME_PORTAL"]
        tags = ["DPIP:Registry", threat_level] + agencies[:2]
        raw_msg = f"[DPIP Smart Registry] Listed entity {vpa_or_hash} threat_level={threat_level} score={threat_score}."
        upi = vpa_or_hash if "@" in vpa_or_hash else None
        return cls(
            source="dpip_registry",
            institution="DPIP",
            anomaly_type="national_registry_match",
            upi_id=upi,
            raw_content=raw_msg,
            tags=tags,
            severity=threat_level if threat_level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "HIGH",
            confidence=min(0.98, max(0.5, threat_score)),
        )


class CampaignMatch(BaseModel):
    """Clustered fraud campaign syndicate match details."""
    campaign_id: str = Field(..., description="Unique campaign identifier")
    name: str = Field(default="", description="Human-readable campaign syndicate name")
    campaign_name: Optional[str] = Field(default=None, description="Campaign syndicate name alias")
    similarity: float = Field(..., description="Calculated clustering similarity score in [0.0, 1.0]")
    scenario: Optional[str] = Field(default=None, description="Syndicate scam typology descriptor")

    def __init__(self, **data: Any):
        if "name" in data and not data.get("campaign_name"):
            data["campaign_name"] = data["name"]
        elif "campaign_name" in data and not data.get("name"):
            data["name"] = data["campaign_name"]
        super().__init__(**data)


class ThreatSignalResponse(BaseModel):
    """Enriched response for an ingested pre-transaction threat signal."""
    signal_id: str = Field(..., description="Unique threat signal identifier (SIG-XXXXXXXX)")
    source: str = Field(default="external", description="Reporting source")
    phone: Optional[str] = Field(default=None, description="Phone number associated with threat")
    upi_id: Optional[str] = Field(default=None, description="UPI VPA associated with threat")
    url: Optional[str] = Field(default=None, description="URL associated with threat")
    tags: List[str] = Field(default_factory=list, description="Social engineering tags")
    raw_content: Optional[str] = Field(default=None, description="Raw threat message content")
    severity: str = Field(default="MEDIUM", description="Assessed signal severity level")
    confidence: float = Field(default=0.85, description="Confidence score in [0.0, 1.0]")
    extracted_entities: ExtractedEntities = Field(default_factory=ExtractedEntities, description="Extracted forensic entities")
    matched_campaign: Optional[CampaignMatch] = Field(default=None, description="Matched campaign clustering metrics")
    matched_campaign_id: Optional[str] = Field(default=None, description="Matched campaign identifier")
    matched_campaign_name: Optional[str] = Field(default=None, description="Matched campaign name")
    similarity_score: float = Field(default=0.0, description="Campaign clustering similarity score")
    case_id: Optional[str] = Field(default=None, description="Linked case ID if matched against existing cases")
    ring_hash: Optional[str] = Field(default=None, description="Linked mule ring hash if matched against syndicates")
    linked_graph_nodes: List[str] = Field(default_factory=list, description="Node IDs linked in Central Fraud Graph")
    created_at: str = Field(default_factory=utcnow_iso, description="UTC creation ISO-8601 timestamp")

    def __init__(self, **data: Any):
        # Resolve aliases for case_id and ring_hash
        if "linked_case_id" in data and not data.get("case_id"):
            data["case_id"] = data["linked_case_id"]
        if "linked_ring_hash" in data and not data.get("ring_hash"):
            data["ring_hash"] = data["linked_ring_hash"]
        super().__init__(**data)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class ThreatSignalListResponse(BaseModel):
    """Paginated collection of threat signals."""
    total: int = Field(..., description="Total threat signals matching query filters")
    signals: List[ThreatSignalResponse] = Field(default_factory=list, description="List of threat signal records")
    limit: int = Field(default=50, description="Pagination query limit")
    offset: int = Field(default=0, description="Pagination query offset")


class GraphNode(BaseModel):
    """A single vertex in the Central Fraud Graph."""
    id: str = Field(..., description="Unique node identifier e.g. VPA:mule@oksbi, PHONE:+919876543210")
    type: str = Field(..., description="Node classification: SIGNAL, VPA, PHONE, URL, CAMPAIGN, CASE, RING")
    label: str = Field(..., description="Human-readable label for visual rendering")
    severity: Optional[str] = Field(default=None, description="Severity if applicable")
    created_at: Optional[str] = Field(default=None, description="Creation ISO-8601 timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary forensic attributes")


class GraphEdge(BaseModel):
    """A directed relationship in the Central Fraud Graph."""
    source: str = Field(..., description="Source node identifier")
    target: str = Field(..., description="Target node identifier")
    type: str = Field(..., description="Relationship type: EXTRACTED_FROM, ASSOCIATED_WITH, TRANSACTED_TO, MEMBER_OF_CAMPAIGN, LINKED_TO_CASE")
    label: Optional[str] = Field(default=None, description="Human-readable label")
    created_at: Optional[str] = Field(default=None, description="Creation ISO-8601 timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Edge weights and attributes")


class ThreatGraphResponse(BaseModel):
    """Topology payload for Central Fraud Graph visualization."""
    nodes: List[GraphNode] = Field(default_factory=list, description="Graph vertices")
    edges: List[GraphEdge] = Field(default_factory=list, description="Graph edges")
    total_nodes: int = Field(default=0, description="Total node count")
    total_edges: int = Field(default=0, description="Total edge count")


class SimulateThreatSignalsRequest(BaseModel):
    """Request payload for generating synthetic early-warning threat traffic."""
    count: int = Field(default=5, ge=1, le=50, description="Number of demo signals to simulate")
    scenario: Optional[str] = Field(default="mixed", description="Scenario: kyc_phish, investment_scam, bill_fraud, apk_malware, mixed")


# Alias for backward/alternative compatibility
ThreatSimulateRequest = SimulateThreatSignalsRequest


class ThreatSimulateResponse(BaseModel):
    """Response payload for threat signal simulation."""
    status: str = Field(default="ok", description="Status code")
    signals_generated: int = Field(default=0, description="Count of signals generated and ingested")
    count: int = Field(default=0, description="Count of signals generated")
    signal_ids: List[str] = Field(default_factory=list, description="List of generated signal IDs")
    signals: List[Any] = Field(default_factory=list, description="List of generated signal payloads")
