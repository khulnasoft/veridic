"""
Phase 2.0: Resolution Rules Engine
Approved Model: Balanced/Dynamic with Downgrade Guardrail
Runtime evidence can UPGRADE freely.
Runtime evidence can DOWNGRADE only with NEGATIVE PROOF.
"""

import logging
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Severity(Enum):
    """CVSS-aligned severity levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


@dataclass
class ResolutionContext:
    """Decision context for verdict"""
    finding_id: str
    static_severity: str
    exploitability_score: float  # 0-100
    supporting_events: List[dict]
    ai_suggested_severity: Optional[str] = None


@dataclass
class ResolutionVerdict:
    """Final resolution of static vs runtime conflict"""
    finding_id: str
    static_severity: str
    runtime_severity: Optional[str]
    final_severity: str
    applied_rule: str
    reasoning: str
    confidence: float
    requires_review: bool = False


class ResolutionRules:
    """
    Decision engine for resolving static vs runtime conflicts.
    Core rule: Runtime can upgrade freely, downgrade only with negative proof.
    """
    
    def resolve(self, context: ResolutionContext) -> ResolutionVerdict:
        """
        Main resolution entrypoint.
        Applies decision tree to determine final verdict.
        """
        
        # If no runtime evidence, keep static
        if context.exploitability_score == 0:
            return ResolutionVerdict(
                finding_id=context.finding_id,
                static_severity=context.static_severity,
                runtime_severity=None,
                final_severity=context.static_severity,
                applied_rule="no_runtime_evidence",
                reasoning="No runtime events captured. Static severity unchanged.",
                confidence=0.9,
            )
        
        # Compute runtime severity from exploitability
        runtime_severity = self._exploitability_to_severity(context.exploitability_score)
        
        # Apply upgrade/downgrade rules
        if self._severity_rank(runtime_severity) > self._severity_rank(context.static_severity):
            # UPGRADE: Always allowed
            return self._apply_upgrade(context, runtime_severity)
        elif self._severity_rank(runtime_severity) < self._severity_rank(context.static_severity):
            # DOWNGRADE: Only with negative proof
            return self._apply_downgrade_with_guardrail(context, runtime_severity)
        else:
            # Same: Confirm with events
            return ResolutionVerdict(
                finding_id=context.finding_id,
                static_severity=context.static_severity,
                runtime_severity=runtime_severity,
                final_severity=context.static_severity,
                applied_rule="confirmed_by_events",
                reasoning=f"Runtime evidence confirms {context.static_severity} severity.",
                confidence=0.95,
            )
    
    def _apply_upgrade(self, context: ResolutionContext, runtime_severity: str) -> ResolutionVerdict:
        """Upgrade severity based on runtime evidence"""
        return ResolutionVerdict(
            finding_id=context.finding_id,
            static_severity=context.static_severity,
            runtime_severity=runtime_severity,
            final_severity=runtime_severity,
            applied_rule="runtime_evidence_upgrade",
            reasoning=f"Runtime evidence ({context.exploitability_score:.1f} exploitability) "
                      f"demonstrates {runtime_severity} severity. "
                      f"Upgraded from {context.static_severity}.",
            confidence=0.92,
        )
    
    def _apply_downgrade_with_guardrail(
        self, context: ResolutionContext, runtime_severity: str
    ) -> ResolutionVerdict:
        """
        CRITICAL GUARDRAIL: Only downgrade with negative proof.
        Without explicit negative proof, flag for review.
        """
        
        # Check for negative proof in events
        has_negative_proof = self._detect_negative_proof(context.supporting_events)
        
        if has_negative_proof:
            return ResolutionVerdict(
                finding_id=context.finding_id,
                static_severity=context.static_severity,
                runtime_severity=runtime_severity,
                final_severity=runtime_severity,
                applied_rule="downgrade_with_negative_proof",
                reasoning=f"Runtime evidence shows vulnerability is mitigated/unreachable. "
                          f"Downgraded from {context.static_severity} to {runtime_severity}.",
                confidence=0.85,
            )
        else:
            # NO negative proof: Keep static, flag for review
            return ResolutionVerdict(
                finding_id=context.finding_id,
                static_severity=context.static_severity,
                runtime_severity=runtime_severity,
                final_severity=context.static_severity,
                applied_rule="downgrade_blocked_no_negative_proof",
                reasoning=f"Runtime exploitability ({context.exploitability_score:.1f}) is lower, "
                          f"but no negative proof detected. Refusing downgrade as safeguard. "
                          f"Flagged for security review.",
                confidence=0.70,
                requires_review=True,
            )
    
    def _detect_negative_proof(self, supporting_events: List[dict]) -> bool:
        """
        Detect explicit evidence of mitigation/unreachability.
        Examples:
        - Input sanitized (filter_pattern, html_escape)
        - Path validation prevented access (permission_denied)
        - Memory access blocked (segfault, out_of_bounds)
        - Auth check prevented execution (401, 403)
        """
        negative_indicators = [
            "permission_denied",
            "access_denied",
            "authorization_failed",
            "sanitized",
            "escaped",
            "validated",
            "blocked",
            "forbidden",
            "out_of_bounds",
        ]
        
        for event in supporting_events:
            event_str = str(event).lower()
            if any(indicator in event_str for indicator in negative_indicators):
                return True
        
        return False
    
    def _exploitability_to_severity(self, exploitability: float) -> str:
        """Convert exploitability score to severity level"""
        if exploitability >= 80:
            return "Critical"
        elif exploitability >= 60:
            return "High"
        elif exploitability >= 40:
            return "Medium"
        elif exploitability >= 20:
            return "Low"
        else:
            return "Info"
    
    def _severity_rank(self, severity: str) -> int:
        """Convert severity to numeric rank for comparison"""
        ranks = {
            "Critical": 5,
            "High": 4,
            "Medium": 3,
            "Low": 2,
            "Info": 1,
        }
        return ranks.get(severity, 0)


# Utility for decision tree visualization
class DecisionTree:
    """Visualizes resolution decisions"""
    
    @staticmethod
    def explain_decision(verdict: ResolutionVerdict) -> str:
        """Generate human-readable explanation"""
        return f"""
Decision: {verdict.final_severity}
============================================
Finding ID:       {verdict.finding_id}
Static Severity:  {verdict.static_severity}
Runtime Verdict:  {verdict.runtime_severity or "N/A"}
Final Severity:   {verdict.final_severity}
Confidence:       {verdict.confidence * 100:.0f}%
Requires Review:  {'YES' if verdict.requires_review else 'NO'}

Rule Applied:     {verdict.applied_rule}
Reasoning:
{verdict.reasoning}
============================================
""".strip()
