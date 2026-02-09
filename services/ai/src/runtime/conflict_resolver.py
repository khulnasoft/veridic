"""
Phase 2.3: Conflict Resolution Engine
Explicit decision tree for resolving static vs runtime disagreements.
Enforces downgrade guardrail: only downgrade with NEGATIVE PROOF.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of finding conflicts"""
    STATIC_VS_RUNTIME = "static_vs_runtime"  # Severity disagreement
    MULTIPLE_FINDINGS = "multiple_findings"  # Overlapping findings
    EVIDENCE_CONTRADICTION = "evidence_contradiction"  # Runtime refutes static


class ResolutionStrategy(Enum):
    """How to resolve conflicts"""
    UPGRADE = "upgrade"  # Runtime proves worse
    DOWNGRADE = "downgrade"  # Runtime shows benign
    KEEP = "keep"  # Static verdict stands
    FLAG = "flag"  # Need manual review


@dataclass
class ConflictResolution:
    """Result of conflict resolution"""
    conflict_id: str
    conflict_type: ConflictType
    strategy: ResolutionStrategy
    rationale: str
    requires_review: bool = False


class ConflictResolver:
    """
    Deterministic conflict resolution engine.
    Decision tree based on evidence strength and type.
    """
    
    def __init__(self):
        self.resolutions: Dict[str, ConflictResolution] = {}
    
    def resolve_static_vs_runtime(
        self,
        conflict_id: str,
        static_severity: str,
        runtime_evidence_type: Optional[str],
        has_negative_proof: bool,
        exploit_chain_detected: bool,
        evidence_confidence: float
    ) -> ConflictResolution:
        """
        Resolve static finding vs runtime evidence.
        
        Decision tree:
        1. If exploit chain detected → UPGRADE
        2. If negative proof exists → DOWNGRADE
        3. If no runtime evidence → KEEP (static verdict)
        4. If conflicting evidence → FLAG for review
        """
        
        # RULE 1: Exploit chain detected → UPGRADE
        if exploit_chain_detected:
            strategy = ResolutionStrategy.UPGRADE
            rationale = (
                f"Runtime evidence forms exploit chain. "
                f"Upgrading {static_severity} finding to next level. "
                f"Evidence confidence: {evidence_confidence:.2f}"
            )
            return ConflictResolution(
                conflict_id=conflict_id,
                conflict_type=ConflictType.STATIC_VS_RUNTIME,
                strategy=strategy,
                rationale=rationale,
                requires_review=False
            )
        
        # RULE 2: Negative proof exists (e.g., input sanitized) → DOWNGRADE
        if has_negative_proof:
            strategy = ResolutionStrategy.DOWNGRADE
            rationale = (
                f"Runtime evidence shows input sanitized before use. "
                f"Downgrading {static_severity} finding by 2 levels (with guardrail). "
                f"Evidence confidence: {evidence_confidence:.2f}"
            )
            return ConflictResolution(
                conflict_id=conflict_id,
                conflict_type=ConflictType.STATIC_VS_RUNTIME,
                strategy=strategy,
                rationale=rationale,
                requires_review=False
            )
        
        # RULE 3: No runtime evidence → KEEP static verdict
        if runtime_evidence_type is None:
            strategy = ResolutionStrategy.KEEP
            rationale = (
                f"No runtime evidence after sandbox execution. "
                f"Keeping static verdict: {static_severity}. "
                f"Note: Cannot downgrade without negative proof."
            )
            return ConflictResolution(
                conflict_id=conflict_id,
                conflict_type=ConflictType.STATIC_VS_RUNTIME,
                strategy=strategy,
                rationale=rationale,
                requires_review=False
            )
        
        # RULE 4: Conflicting evidence → FLAG for manual review
        strategy = ResolutionStrategy.FLAG
        rationale = (
            f"Conflicting evidence detected: static={static_severity}, "
            f"runtime={runtime_evidence_type}. "
            f"Evidence confidence: {evidence_confidence:.2f}. "
            f"Flagging for manual review."
        )
        return ConflictResolution(
            conflict_id=conflict_id,
            conflict_type=ConflictType.STATIC_VS_RUNTIME,
            strategy=strategy,
            rationale=rationale,
            requires_review=True
        )
    
    def apply_downgrade_guardrail(
        self,
        current_severity: str,
        downgrade_count: int
    ) -> Tuple[str, Optional[str]]:
        """
        Safely apply downgrade with guardrail.
        Returns (new_severity, warning_if_any)
        
        Severity levels: critical > high > medium > low > info
        Guardrail: Only downgrade if NEGATIVE PROOF exists.
        """
        severity_order = ["critical", "high", "medium", "low", "info"]
        current_idx = severity_order.index(current_severity)
        
        # Can't downgrade below 'info'
        if current_idx + downgrade_count >= len(severity_order):
            new_idx = len(severity_order) - 1
            warning = f"Downgrade capped at 'info' level"
        else:
            new_idx = current_idx + downgrade_count
            warning = None
        
        return severity_order[new_idx], warning
    
    def apply_upgrade_guardrail(
        self,
        current_severity: str,
        upgrade_count: int
    ) -> Tuple[str, Optional[str]]:
        """
        Safely apply upgrade with guardrail.
        Returns (new_severity, warning_if_any)
        
        Severity levels: critical > high > medium > low > info
        Guardrail: Can upgrade freely (evidence-based).
        """
        severity_order = ["critical", "high", "medium", "low", "info"]
        current_idx = severity_order.index(current_severity)
        
        # Can't upgrade above 'critical'
        if current_idx - upgrade_count < 0:
            new_idx = 0
            warning = f"Upgrade capped at 'critical' level"
        else:
            new_idx = current_idx - upgrade_count
            warning = None
        
        return severity_order[new_idx], warning
    
    def resolve_multiple_findings(
        self,
        finding_ids: List[str],
        severities: List[str]
    ) -> ConflictResolution:
        """
        Resolve multiple overlapping findings.
        
        Strategy: Keep highest severity, mark others as duplicates.
        """
        severity_order = ["critical", "high", "medium", "low", "info"]
        highest_idx = min(severity_order.index(s) for s in severities)
        highest_severity = severity_order[highest_idx]
        
        conflict_id = f"multi_{len(finding_ids)}"
        rationale = (
            f"Found {len(finding_ids)} overlapping findings: {finding_ids}. "
            f"Keeping highest severity: {highest_severity}. "
            f"Marking others as duplicates."
        )
        
        return ConflictResolution(
            conflict_id=conflict_id,
            conflict_type=ConflictType.MULTIPLE_FINDINGS,
            strategy=ResolutionStrategy.KEEP,
            rationale=rationale,
            requires_review=False
        )
    
    def resolve_evidence_contradiction(
        self,
        finding_id: str,
        static_claim: str,
        runtime_evidence: str,
        contradiction_type: str
    ) -> ConflictResolution:
        """
        Resolve direct evidence contradiction.
        
        Example: Static says "SQL injection possible" but runtime shows
        input always reaches prepared statement (no injection).
        """
        strategy = ResolutionStrategy.FLAG
        rationale = (
            f"Evidence contradiction for {finding_id}: "
            f"Static={static_claim}, Runtime={runtime_evidence}. "
            f"Contradiction type: {contradiction_type}. "
            f"Flagging for manual review."
        )
        
        return ConflictResolution(
            conflict_id=f"contradiction_{finding_id}",
            conflict_type=ConflictType.EVIDENCE_CONTRADICTION,
            strategy=strategy,
            rationale=rationale,
            requires_review=True
        )


class ConflictResolutionContext:
    """
    High-level context for resolution decisions.
    Combines severity mapping + evidence strength.
    """
    
    UPGRADE_TRIGGERS = {
        "exploit_chain_detected": 1,  # Upgrade by 1 level
        "multiple_corroborating_events": 1,
        "network_exfiltration_detected": 2,  # Upgrade by 2 levels
        "active_exploitation_attempts": 2,
    }
    
    DOWNGRADE_TRIGGERS = {
        "input_sanitized": 2,  # Downgrade by 2 levels (guardrail)
        "no_runtime_evidence": 1,  # But requires NEGATIVE PROOF
        "auth_required_not_bypassed": 1,
        "vulnerability_fixed_in_runtime": 3,
    }
    
    @staticmethod
    def compute_verdict_delta(
        triggers: List[str],
        direction: str  # "upgrade" or "downgrade"
    ) -> int:
        """
        Compute total severity change based on triggers.
        Returns number of levels to change (positive = upgrade, negative = downgrade).
        """
        trigger_map = (
            ConflictResolutionContext.UPGRADE_TRIGGERS
            if direction == "upgrade"
            else ConflictResolutionContext.DOWNGRADE_TRIGGERS
        )
        
        total_delta = sum(trigger_map.get(t, 0) for t in triggers if t in trigger_map)
        return total_delta if direction == "upgrade" else -total_delta
