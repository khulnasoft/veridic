"""
Phase 2.0: Runtime Analysis Module
Enables dynamic and runtime analysis of vulnerabilities.

Architecture (Skeleton-First):
- No engine coupling
- Collectors (eBPF, mitmproxy) are independent
- Correlation logic is stateless
- Resolution rules have explicit guardrails

Components:
1. sandbox.py - Execution environment lifecycle
2. trace_store.py - Event storage and querying
3. correlator.py - Static-to-runtime mapping (stateless)
4. resolution_rules.py - Verdict engine with downgrade guardrail
5. phase2_determinism.py - Reproducibility validation
"""

from .sandbox import SandboxManager, SandboxSession, SandboxConfig, CollectorInterface
from .trace_store import TraceStore, EventFilter, DeterminismAnalyzer
from .correlator import CorrelationModel, CorrelationResult
from .resolution_rules import ResolutionRules, ResolutionContext, ResolutionVerdict, DecisionTree
from .phase2_determinism import Phase2DeterminismValidator

__all__ = [
    "SandboxManager",
    "SandboxSession",
    "SandboxConfig",
    "CollectorInterface",
    "TraceStore",
    "EventFilter",
    "DeterminismAnalyzer",
    "CorrelationModel",
    "CorrelationResult",
    "ResolutionRules",
    "ResolutionContext",
    "ResolutionVerdict",
    "DecisionTree",
    "Phase2DeterminismValidator",
]
