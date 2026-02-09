"""
Continuous Threat Scoring Engine

Computes real-time threat scores for assets based on:
- Static analysis findings
- Runtime validation evidence
- Exploit chain severity
- Historical trends

All scoring is deterministic and SHA256-hashable for reproducibility.
"""

import hashlib
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Finding:
    """Individual security finding."""
    id: str
    type: str
    severity: str  # critical, high, medium, low
    confidence: float  # 0.0 - 1.0
    source: str  # static, runtime, ai_reasoning
    line: Optional[int] = None
    exploit_chain: Optional[List[str]] = None


@dataclass
class ThreatScore:
    """Deterministic threat score for an asset."""
    asset_id: str
    score: float  # 0.0 - 100.0
    severity_breakdown: Dict[str, int]
    confidence_weighted_score: float
    exploit_chains_count: int
    findings_count: int
    timestamp: str
    hash: str  # SHA256 of deterministic inputs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ContinuousScoringEngine:
    """
    Real-time threat scoring engine with deterministic output.
    
    Scoring Formula:
    - Base score from severity counts
    - Confidence weighting
    - Exploit chain multipliers
    - Normalized to 0-100 scale
    """
    
    # Severity weights
    SEVERITY_WEIGHTS = {
        "critical": 10.0,
        "high": 7.0,
        "medium": 4.0,
        "low": 2.0,
        "none": 0.0,
    }
    
    # Exploit chain multiplier
    EXPLOIT_CHAIN_MULTIPLIER = 1.5
    
    def __init__(self):
        """Initialize scoring engine."""
        self.scoring_version = "2.5.0"
    
    def compute_threat_score(
        self,
        asset_id: str,
        findings: List[Finding],
        timestamp: Optional[str] = None,
    ) -> ThreatScore:
        """
        Compute deterministic threat score for an asset.
        
        Args:
            asset_id: Unique asset identifier
            findings: List of security findings
            timestamp: Optional timestamp (for reproducibility)
            
        Returns:
            ThreatScore with deterministic hash
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        # Sort findings deterministically for consistent hashing
        sorted_findings = sorted(
            findings,
            key=lambda f: (f.id, f.type, f.severity, f.confidence)
        )
        
        # Count findings by severity
        severity_breakdown = self._count_by_severity(sorted_findings)
        
        # Calculate base score
        base_score = self._calculate_base_score(severity_breakdown)
        
        # Apply confidence weighting
        confidence_weighted_score = self._apply_confidence_weighting(
            sorted_findings, base_score
        )
        
        # Count exploit chains
        exploit_chains_count = sum(
            1 for f in sorted_findings if f.exploit_chain
        )
        
        # Apply exploit chain multiplier
        final_score = confidence_weighted_score
        if exploit_chains_count > 0:
            final_score *= (1 + (exploit_chains_count * 0.1))
        
        # Normalize to 0-100
        final_score = min(100.0, max(0.0, final_score))
        
        # Generate deterministic hash
        score_hash = self._generate_hash(
            asset_id,
            sorted_findings,
            severity_breakdown,
            final_score,
            timestamp,
        )
        
        return ThreatScore(
            asset_id=asset_id,
            score=round(final_score, 2),
            severity_breakdown=severity_breakdown,
            confidence_weighted_score=round(confidence_weighted_score, 2),
            exploit_chains_count=exploit_chains_count,
            findings_count=len(findings),
            timestamp=timestamp,
            hash=score_hash,
        )
    
    def _count_by_severity(self, findings: List[Finding]) -> Dict[str, int]:
        """Count findings by severity level."""
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        
        for finding in findings:
            severity = finding.severity.lower()
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    def _calculate_base_score(self, severity_breakdown: Dict[str, int]) -> float:
        """Calculate base score from severity counts."""
        score = 0.0
        
        for severity, count in severity_breakdown.items():
            weight = self.SEVERITY_WEIGHTS.get(severity, 0.0)
            score += weight * count
        
        return score
    
    def _apply_confidence_weighting(
        self,
        findings: List[Finding],
        base_score: float
    ) -> float:
        """Apply confidence weighting to base score."""
        if not findings:
            return 0.0
        
        # Calculate average confidence
        avg_confidence = sum(f.confidence for f in findings) / len(findings)
        
        # Weight the score by confidence
        return base_score * avg_confidence
    
    def _generate_hash(
        self,
        asset_id: str,
        findings: List[Finding],
        severity_breakdown: Dict[str, int],
        score: float,
        timestamp: str,
    ) -> str:
        """Generate SHA256 hash for deterministic verification."""
        # Create deterministic representation
        hash_input = {
            "asset_id": asset_id,
            "findings": [
                {
                    "id": f.id,
                    "type": f.type,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "source": f.source,
                }
                for f in findings
            ],
            "severity_breakdown": severity_breakdown,
            "score": round(score, 2),
            "timestamp": timestamp,
            "version": self.scoring_version,
        }
        
        # Convert to JSON with sorted keys
        json_str = json.dumps(hash_input, sort_keys=True)
        
        # Generate SHA256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def batch_compute_scores(
        self,
        assets_findings: Dict[str, List[Finding]],
        timestamp: Optional[str] = None,
    ) -> Dict[str, ThreatScore]:
        """
        Compute threat scores for multiple assets.
        
        Args:
            assets_findings: Dict mapping asset_id to findings list
            timestamp: Optional timestamp for all scores
            
        Returns:
            Dict mapping asset_id to ThreatScore
        """
        scores = {}
        
        for asset_id, findings in assets_findings.items():
            scores[asset_id] = self.compute_threat_score(
                asset_id, findings, timestamp
            )
        
        return scores
    
    def verify_score_hash(self, score: ThreatScore, findings: List[Finding]) -> bool:
        """
        Verify that a threat score hash matches expected value.
        
        Args:
            score: ThreatScore to verify
            findings: Original findings used for scoring
            
        Returns:
            True if hash matches, False otherwise
        """
        # Recompute score
        recomputed = self.compute_threat_score(
            score.asset_id,
            findings,
            score.timestamp,
        )
        
        return recomputed.hash == score.hash


# Example usage
if __name__ == "__main__":
    # Create sample findings
    findings = [
        Finding(
            id="VULN-001",
            type="sql_injection",
            severity="critical",
            confidence=0.95,
            source="static",
            line=42,
            exploit_chain=["input_validation", "database_query"],
        ),
        Finding(
            id="VULN-002",
            type="xss",
            severity="high",
            confidence=0.85,
            source="static",
            line=78,
        ),
        Finding(
            id="VULN-003",
            type="path_traversal",
            severity="medium",
            confidence=0.70,
            source="runtime",
        ),
    ]
    
    # Compute threat score
    engine = ContinuousScoringEngine()
    score = engine.compute_threat_score("asset-123", findings)
    
    print(f"Asset: {score.asset_id}")
    print(f"Threat Score: {score.score}/100")
    print(f"Severity Breakdown: {score.severity_breakdown}")
    print(f"Exploit Chains: {score.exploit_chains_count}")
    print(f"Hash: {score.hash}")
    
    # Verify hash
    is_valid = engine.verify_score_hash(score, findings)
    print(f"Hash Valid: {is_valid}")
