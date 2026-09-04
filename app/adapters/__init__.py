"""Simulated Institutional Signal Adapters package for SAMPATI V2."""
from app.adapters.dpip import (
    DpipRegistryRecord,
    DpipRegistryUpdateRequest,
    DpipSmartRegistryAdapter,
    get_dpip_adapter,
)
from app.adapters.npci import (
    NpciMuleHunterAdapter,
    NpciMuleHunterResponse,
    get_npci_adapter,
)
from app.adapters.psp import (
    MockPspAdapter,
    get_psp_adapter,
)
from app.adapters.service import (
    InstitutionalAdapterService,
    get_institutional_adapters,
)

__all__ = [
    "NpciMuleHunterAdapter",
    "NpciMuleHunterResponse",
    "get_npci_adapter",
    "DpipSmartRegistryAdapter",
    "DpipRegistryRecord",
    "DpipRegistryUpdateRequest",
    "get_dpip_adapter",
    "MockPspAdapter",
    "get_psp_adapter",
    "InstitutionalAdapterService",
    "get_institutional_adapters",
]
