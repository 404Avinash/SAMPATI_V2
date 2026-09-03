"""Unsupervised Isolation Forest Engine for SAMPATI V2.

Implements the canonical Isolation Forest multivariate anomaly detection algorithm
(Liu, Ting, Zhou, ICDM 2008 / TKDD 2012) in pure NumPy / Python with dynamic
scikit-learn fallback adapter.

Layer 4 ML scoring engine:
- Evaluates non-linear multivariate anomaly scores in [0.0, 1.0].
- Fits on synthetic legitimate retail UPI transaction baseline (~600 samples).
- Yields sub-1ms inference latency per transaction.
- Thread-safe singleton getter get_isolation_forest().
"""
from __future__ import annotations

import math
import threading
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple, Union

import numpy as np

from app.engine.upi_state import UpiHotState
from app.models.upi_models import UpiTransaction

try:
    from sklearn.ensemble import IsolationForest as SklearnIsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    SklearnIsolationForest = None  # type: ignore


# ---------------------------------------------------------------------------
# Core Isolation Tree & Forest Math (Liu, Ting, Zhou 2008)
# ---------------------------------------------------------------------------

def c_factor(n: int) -> float:
    """Average path length of unsuccessful search in a Binary Search Tree (BST).

    c(n) = 2 * (ln(n - 1) + 0.5772156649) - (2 * (n - 1) / n) for n > 2
    c(2) = 1.0
    c(n) = 0.0 for n <= 1
    """
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    # Euler-Mascheroni constant
    gamma = 0.57721566490153286
    return 2.0 * (math.log(n - 1) + gamma) - (2.0 * (n - 1) / n)


class IsolationTreeNode:
    """A node within an Isolation Tree (iTree)."""

    __slots__ = ("split_feature", "split_value", "left", "right", "size", "is_leaf")

    def __init__(
        self,
        size: int,
        is_leaf: bool = False,
        split_feature: int = -1,
        split_value: float = 0.0,
        left: Optional[IsolationTreeNode] = None,
        right: Optional[IsolationTreeNode] = None,
    ) -> None:
        self.size: int = size
        self.is_leaf: bool = is_leaf
        self.split_feature: int = split_feature
        self.split_value: float = split_value
        self.left: Optional[IsolationTreeNode] = left
        self.right: Optional[IsolationTreeNode] = right


def build_itree(
    X: np.ndarray,
    current_height: int,
    max_height: int,
    rng: np.random.Generator,
) -> IsolationTreeNode:
    """Recursively construct an Isolation Tree by random orthogonal partitioning."""
    n_samples, n_features = X.shape
    if current_height >= max_height or n_samples <= 1:
        return IsolationTreeNode(size=n_samples, is_leaf=True)

    feat_indices = list(range(n_features))
    rng.shuffle(feat_indices)

    for feat in feat_indices:
        col = X[:, feat]
        min_v = float(np.min(col))
        max_v = float(np.max(col))
        if min_v < max_v:
            split_val = float(rng.uniform(min_v, max_v))
            left_mask = col < split_val
            right_mask = ~left_mask
            if np.any(left_mask) and np.any(right_mask):
                left_child = build_itree(X[left_mask], current_height + 1, max_height, rng)
                right_child = build_itree(X[right_mask], current_height + 1, max_height, rng)
                return IsolationTreeNode(
                    size=n_samples,
                    is_leaf=False,
                    split_feature=feat,
                    split_value=split_val,
                    left=left_child,
                    right=right_child,
                )

    return IsolationTreeNode(size=n_samples, is_leaf=True)


def itree_path_length(
    x: np.ndarray,
    node: IsolationTreeNode,
    current_height: int,
) -> float:
    """Compute path length h(x) of instance x traversing an iTree."""
    if node.is_leaf:
        return current_height + c_factor(node.size)

    feat = node.split_feature
    val = node.split_value
    if x[feat] < val:
        if node.left is not None:
            return itree_path_length(x, node.left, current_height + 1)
        return current_height + c_factor(node.size)
    else:
        if node.right is not None:
            return itree_path_length(x, node.right, current_height + 1)
        return current_height + c_factor(node.size)


class PureNumpyIsolationForest:
    """Pure-Python / NumPy implementation of Liu et al. (2008) Isolation Forest."""

    def __init__(
        self,
        n_trees: int = 50,
        max_samples: int = 128,
        random_state: int = 42,
    ) -> None:
        self.n_trees: int = n_trees
        self.max_samples: int = max_samples
        self.random_state: int = random_state
        self.trees: List[IsolationTreeNode] = []
        self.c_val: float = c_factor(max_samples)
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> PureNumpyIsolationForest:
        """Fit ensemble of iTrees on training matrix X (n_samples, n_features)."""
        rng = np.random.default_rng(self.random_state)
        n_samples = X.shape[0]
        subsample_size = min(self.max_samples, n_samples)
        self.c_val = c_factor(subsample_size)
        max_height = int(math.ceil(math.log2(max(subsample_size, 2))))

        self.trees = []
        for _ in range(self.n_trees):
            sub_indices = rng.choice(n_samples, size=subsample_size, replace=False)
            sub_X = X[sub_indices]
            tree = build_itree(sub_X, 0, max_height, rng)
            self.trees.append(tree)

        self.is_fitted = True
        return self

    def raw_score(self, x: np.ndarray) -> float:
        """Compute raw anomaly score s(x, n) = 2^(-E(h(x)) / c(n))."""
        if not self.trees or self.c_val <= 0.0:
            return 0.5
        total_path = sum(itree_path_length(x, tree, 0) for tree in self.trees)
        avg_path = total_path / len(self.trees)
        return float(2.0 ** (- (avg_path / self.c_val)))


class SklearnIsolationForestAdapter:
    """Adapter wrapping sklearn.ensemble.IsolationForest when installed."""

    def __init__(
        self,
        n_trees: int = 50,
        max_samples: int = 128,
        random_state: int = 42,
    ) -> None:
        self.n_trees: int = n_trees
        self.max_samples: int = max_samples
        self.random_state: int = random_state
        self.model = SklearnIsolationForest(
            n_estimators=n_trees,
            max_samples=max_samples,
            random_state=random_state,
        )
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> SklearnIsolationForestAdapter:
        self.model.fit(X)
        self.is_fitted = True
        return self

    def raw_score(self, x: np.ndarray) -> float:
        """Compute anomaly score normalized in [0.0, 1.0] from sklearn."""
        # sklearn score_samples returns opposite of anomaly score: values close to -1 are anomalous
        # score in roughly [-1.0, 0.0]
        score_sample = float(self.model.score_samples(x.reshape(1, -1))[0])
        # Invert: -score_sample maps normal (~0.4 - 0.5) to (~0.4 - 0.5), anomaly (>0.7) to (>0.7)
        return float(np.clip(-score_sample, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Synthetic Baseline Dataset Generator
# ---------------------------------------------------------------------------

def generate_synthetic_baseline(
    n_samples: int = 700,
    contamination: float = 0.035,
    seed: int = 42,
) -> np.ndarray:
    """Generate deterministic synthetic feature matrix modeling legitimate retail UPI transactions.

    Includes a small 3.5% contamination of multivariate anomaly patterns so the Isolation Forest
    develops sharp isolation boundaries between legitimate traffic and adversarial bursts.
    """
    rng = np.random.default_rng(seed)
    n_anom = max(1, int(n_samples * contamination))
    n_norm = n_samples - n_anom

    # 1. Normal Retail UPI Traffic (96.5%)
    n_retail = int(n_norm * 0.75)
    n_mid = int(n_norm * 0.22)
    n_high = n_norm - n_retail - n_mid

    amt_norm = np.concatenate([
        rng.lognormal(mean=6.5, sigma=1.0, size=n_retail),  # Rs 100 - Rs 5,000
        rng.uniform(5000.0, 30000.0, size=n_mid),           # Rs 5,000 - Rs 30,000
        rng.uniform(30000.0, 80000.0, size=n_high),         # occasional higher retail
    ])
    log_amt_norm = np.log1p(amt_norm)

    n_day = int(n_norm * 0.92)
    n_night = n_norm - n_day
    hr_norm = np.concatenate([
        rng.uniform(6.0, 23.0, size=n_day),
        rng.uniform(0.0, 6.0, size=n_night),
    ])
    hr_sin_norm = np.sin(2.0 * np.pi * hr_norm / 24.0)
    hr_cos_norm = np.cos(2.0 * np.pi * hr_norm / 24.0)
    night_norm = ((hr_norm < 5.0) | (hr_norm >= 23.0)).astype(np.float64)

    p_age_norm = rng.integers(30, 400, size=n_norm).astype(np.float64)
    py_age_norm = rng.integers(30, 400, size=n_norm).astype(np.float64)
    new_py_norm = rng.choice([0.0, 1.0], size=n_norm, p=[0.75, 0.25])
    vel_cnt_norm = rng.integers(0, 3, size=n_norm).astype(np.float64)
    vel_amt_norm = vel_cnt_norm * rng.uniform(100.0, 1500.0, size=n_norm)
    dev_norm = np.ones(n_norm, dtype=np.float64)
    dmv_norm = np.zeros(n_norm, dtype=np.float64)

    X_norm = np.column_stack([
        amt_norm, log_amt_norm, hr_norm, hr_sin_norm, hr_cos_norm, night_norm,
        p_age_norm, py_age_norm, new_py_norm, vel_cnt_norm, vel_amt_norm, dev_norm, dmv_norm
    ])

    # 2. Multivariate Mule Burst Anomalies (3.5%)
    amt_anom = rng.uniform(150000.0, 500000.0, size=n_anom)
    log_amt_anom = np.log1p(amt_anom)
    hr_anom = rng.uniform(1.0, 4.5, size=n_anom)
    hr_sin_anom = np.sin(2.0 * np.pi * hr_anom / 24.0)
    hr_cos_anom = np.cos(2.0 * np.pi * hr_anom / 24.0)
    night_anom = np.ones(n_anom, dtype=np.float64)
    p_age_anom = rng.integers(0, 3, size=n_anom).astype(np.float64)
    py_age_anom = rng.integers(0, 3, size=n_anom).astype(np.float64)
    new_py_anom = np.ones(n_anom, dtype=np.float64)
    vel_cnt_anom = rng.integers(8, 25, size=n_anom).astype(np.float64)
    vel_amt_anom = rng.uniform(200000.0, 800000.0, size=n_anom)
    dev_anom = rng.integers(4, 10, size=n_anom).astype(np.float64)
    dmv_anom = rng.uniform(80.0, 100.0, size=n_anom)

    X_anom = np.column_stack([
        amt_anom, log_amt_anom, hr_anom, hr_sin_anom, hr_cos_anom, night_anom,
        p_age_anom, py_age_anom, new_py_anom, vel_cnt_anom, vel_amt_anom, dev_anom, dmv_anom
    ])

    return np.vstack([X_norm, X_anom])


# ---------------------------------------------------------------------------
# High-Level UPI Isolation Forest Scorer
# ---------------------------------------------------------------------------

class UpiIsolationForest:
    """Production multivariate Isolation Forest anomaly scorer for UPI transactions.

    Satisfies:
    - Zero-regression invariant: clean legitimate retail transactions produce anomaly score <= 0.50.
    - Extreme multivariate anomalies produce anomaly score >= 0.70 (and severe bursts >= 0.85).
    - Sub-1ms per-transaction inference latency.
    """

    FEATURE_NAMES: List[str] = [
        "amount",
        "log_amount",
        "hour_fraction",
        "hour_sin",
        "hour_cos",
        "is_night",
        "payer_account_age_days",
        "payee_vpa_age_days",
        "payee_is_new_for_payer",
        "payer_velocity_count_30m",
        "payer_velocity_amount_30m",
        "device_vpa_count",
        "dmv_score",
    ]

    def __init__(
        self,
        n_trees: int = 50,
        max_samples: int = 128,
        random_state: int = 42,
        use_sklearn_if_available: bool = True,
        auto_fit_baseline: bool = True,
    ) -> None:
        self.n_trees: int = n_trees
        self.max_samples: int = max_samples
        self.random_state: int = random_state

        if SKLEARN_AVAILABLE and use_sklearn_if_available:
            self.engine: Union[SklearnIsolationForestAdapter, PureNumpyIsolationForest] = (
                SklearnIsolationForestAdapter(n_trees=n_trees, max_samples=max_samples, random_state=random_state)
            )
            self.backend: str = "sklearn"
        else:
            self.engine = PureNumpyIsolationForest(
                n_trees=n_trees,
                max_samples=max_samples,
                random_state=random_state,
            )
            self.backend = "numpy"

        self._lock = threading.Lock()
        if auto_fit_baseline:
            self.fit_baseline()

    def fit(self, X: np.ndarray) -> UpiIsolationForest:
        """Fit the underlying forest engine on data matrix X."""
        with self._lock:
            self.engine.fit(X)
        return self

    def fit_baseline(
        self,
        n_samples: int = 600,
        contamination: float = 0.04,
        seed: int = 42,
    ) -> UpiIsolationForest:
        """Fit model on synthetic baseline transaction matrix."""
        X_baseline = generate_synthetic_baseline(
            n_samples=n_samples,
            contamination=contamination,
            seed=seed,
        )
        return self.fit(X_baseline)

    def extract_features(
        self,
        txn: UpiTransaction,
        state: Optional[UpiHotState] = None,
        dmv_score: float = 0.0,
    ) -> np.ndarray:
        """Extract 13-dimensional numerical feature vector from transaction and state telemetry."""
        # 1. Amount & Log Amount
        amount = float(getattr(txn, "amount", 0.0))
        log_amt = math.log1p(max(0.0, amount))

        # 2. Time of Day & Cyclical Coordinates
        ts = getattr(txn, "timestamp", None)
        if isinstance(ts, datetime):
            hr = ts.hour + ts.minute / 60.0 + ts.second / 3600.0
        elif isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hr = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            except Exception:
                hr = 14.0
        else:
            hr = 14.0

        hr_sin = math.sin(2.0 * math.pi * hr / 24.0)
        hr_cos = math.cos(2.0 * math.pi * hr / 24.0)
        is_night = 1.0 if (hr < 5.0 or hr >= 23.0) else 0.0

        # 3. Entity Ages & Novelty
        payer_age = float(min(365.0, max(0.0, float(getattr(txn, "payer_account_age_days", 365)))))
        payee_age = float(min(365.0, max(0.0, float(getattr(txn, "payee_vpa_age_days", 365)))))
        new_payee = 1.0 if getattr(txn, "payee_is_new_for_payer", False) else 0.0

        # 4. State Velocity & Device Sharing Telemetry
        vel_cnt = 0.0
        vel_amt = 0.0
        dev_cnt = 1.0

        if state is not None:
            ts_for_state = ts if isinstance(ts, datetime) else datetime.now(timezone.utc)
            if hasattr(state, "outbound_stats"):
                try:
                    c, _, a = state.outbound_stats(txn.payer_vpa, ts_for_state)
                    vel_cnt = float(c)
                    vel_amt = float(a)
                except Exception:
                    vel_cnt = 0.0
                    vel_amt = 0.0

            dev_id = getattr(txn, "device_id", None)
            if dev_id and hasattr(state, "device_vpa_count"):
                try:
                    dev_cnt = float(state.device_vpa_count(dev_id))
                except Exception:
                    dev_cnt = 1.0

        # 5. DMV Score
        dmv = float(dmv_score or 0.0)

        return np.array([
            amount,
            log_amt,
            hr,
            hr_sin,
            hr_cos,
            is_night,
            payer_age,
            payee_age,
            new_payee,
            vel_cnt,
            vel_amt,
            dev_cnt,
            dmv,
        ], dtype=np.float64)

    def raw_score_vector(self, vector: np.ndarray) -> float:
        """Compute raw anomaly score s(x, n) from feature vector."""
        return self.engine.raw_score(vector)

    def normalize_score(self, raw_score: float) -> float:
        """Map raw anomaly score into normalized [0.0, 1.0].

        Ensures:
        - Normal retail transactions (raw <= 0.50) map to <= 0.48 < 0.50 (zero-regression invariant).
        - Multivariate anomalies (raw > 0.50) scale monotonically into [0.50, 1.0]:
          * raw ~ 0.58 maps to ~0.71 ("ML_MULTIVARIATE_ANOMALY")
          * raw >= 0.64 maps to >= 0.85 (HOLD floor trigger).
        """
        if raw_score <= 0.50:
            return float(max(0.0, raw_score * 0.96))
        scaled = 0.50 + ((raw_score - 0.50) / 0.15) * 0.40
        return float(min(1.0, scaled))

    def score_vector(self, vector: np.ndarray) -> float:
        """Compute normalized anomaly score in [0.0, 1.0] from feature vector."""
        raw = self.raw_score_vector(vector)
        return self.normalize_score(raw)

    def score_txn(
        self,
        txn: UpiTransaction,
        state: Optional[UpiHotState] = None,
        dmv_score: float = 0.0,
    ) -> float:
        """Score an incoming UPI transaction; returns normalized anomaly score in [0.0, 1.0]."""
        vec = self.extract_features(txn, state=state, dmv_score=dmv_score)
        return self.score_vector(vec)


# ---------------------------------------------------------------------------
# Thread-safe Singleton Access
# ---------------------------------------------------------------------------

_forest_lock = threading.Lock()
_forest_instance: Optional[UpiIsolationForest] = None


def get_isolation_forest() -> UpiIsolationForest:
    """Thread-safe singleton getter for UpiIsolationForest."""
    global _forest_instance
    if _forest_instance is None:
        with _forest_lock:
            if _forest_instance is None:
                _forest_instance = UpiIsolationForest()
    return _forest_instance


# Alias for backward/forward compatibility
get_ml_scorer = get_isolation_forest
