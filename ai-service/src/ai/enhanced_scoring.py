"""
Phase 2.4: Evidence-Weighted CVSS Scoring
Extends Phase 2.3 scoring with confidence factors from aggregated findings.
Produces reproducible scores across multiple runs.
"""

import logging
import hashlib
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ScoringMetric(Enum):
    """CVSS metrics"""
    CVSS_V3_1 = "cvss_v3.1"
    EXPLOITABILITY = "exploitability"
    IMPACT = "impact"


@dataclass
class ScoringInput:
    """Deterministic input for evidence-weighted scoring"""
    aggregation_id: str
    finding_type: str
    static_confidence: float
    runtime_confidence: float
    combined_confidence: float
    exploit_chain_detected: bool
    has_negative_proof: bool
    asset_context: Dict[str, Any]
    
    def to_deterministic_dict(self) -> Dict[str, Any]:
        """Convert to deterministic dict for hashing"""
        return {
            "aggregation_id": self.aggregation_id,
            "finding_type": self.finding_type,
            "static_confidence": round(self.static_confidence, 4),
            "runtime_confidence": round(self.runtime_confidence, 4),
            "combined_confidence": round(self.combined_confidence, 4),
            "exploit_chain_detected": self.exploit_chain_detected,
            "has_negative_proof": self.has_negative_proof,
            "asset_context": self.asset_context,
        }


@dataclass
class EnhancedScore:
    """Enhanced CVSS score with evidence weighting"""
    base_score: float  # Traditional CVSS base (0.0-10.0)
    exploitability_boost: float  # Additional points from runtime evidence
    impact_adjustment: float  # Negative if mitigated by runtime evidence
    final_score: float  # Combined score (0.0-10.0)
    severity: str  # "critical", "high", "medium", "low"
    evidence_factors: Dict[str, float]  # Breakdown of weighting
    scoring_hash: str = ""  # SHA256 for determinism validation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "base_score": self.base_score,
            "exploitability_boost": self.exploitability_boost,
            "impact_adjustment": self.impact_adjustment,
            "final_score": self.final_score,
            "severity": self.severity,
            "evidence_factors": self.evidence_factors,
            "scoring_hash": self.scoring_hash,
        }


class EnhancedCVSSScorer:
    """
    Evidence-weighted CVSS scoring that extends Phase 2.3 scoring.
    Incorporates aggregated findings and confidence factors.
    Produces deterministic scores.
    """
    
    # CWE to CVSS base score mapping (same as Phase 2.3)
    CWE_CVSS_MAP = {
        "CWE-89": 9.8,    # SQL Injection
        "CWE-79": 6.1,    # XSS
        "CWE-20": 9.8,    # Improper Input Validation
        "CWE-22": 9.1,    # Path Traversal
        "CWE-78": 9.8,    # OS Command Injection
        "CWE-502": 8.8,   # Insecure Deserialization
        "CWE-259": 7.5,   # Hardcoded Password
        "CWE-327": 9.1,   # Weak Cryptography
        "CWE-362": 5.5,   # Race Condition
        "CWE-772": 7.5,   # Missing Resource Release
    }
    
    # Finding type to CWE mapping
    FINDING_TYPE_CWE_MAP = {
        "sql_injection": "CWE-89",
        "xss": "CWE-79",
        "input_validation": "CWE-20",
        "path_traversal": "CWE-22",
        "command_injection": "CWE-78",
        "insecure_deserialization": "CWE-502",
        "hardcoded_secret": "CWE-259",
        "weak_cryptography": "CWE-327",
        "race_condition": "CWE-362",
        "resource_leak": "CWE-772",
    }
    
    def __init__(self):
        logger.info("Initializing EnhancedCVSSScorer")
    
    def score_aggregated_finding(
        self,
        scoring_input: ScoringInput,
    ) -> EnhancedScore:
        """
        Generate evidence-weighted CVSS score for aggregated finding.
        
        Args:
            scoring_input: ScoringInput with confidence factors
            
        Returns:
            EnhancedScore with adjusted CVSS and evidence weighting
        """
        logger.info(f"Scoring aggregated finding: {scoring_input.aggregation_id}")
        
        # Get base CVSS from CWE
        cwe = self._finding_type_to_cwe(scoring_input.finding_type)
        base_score = self.CWE_CVSS_MAP.get(cwe, 5.0)  # Default medium
        
        # Compute evidence-based adjustments
        evidence_factors = self._compute_evidence_factors(
            base_score=base_score,
            static_confidence=scoring_input.static_confidence,
            runtime_confidence=scoring_input.runtime_confidence,
            combined_confidence=scoring_input.combined_confidence,
            exploit_chain_detected=scoring_input.exploit_chain_detected,
            has_negative_proof=scoring_input.has_negative_proof,
        )
        
        exploitability_boost = evidence_factors.get("exploitability_boost", 0.0)
        impact_adjustment = evidence_factors.get("impact_adjustment", 0.0)
        
        # Compute final score
        final_score = base_score + exploitability_boost + impact_adjustment
        final_score = max(0.0, min(10.0, final_score))  # Clamp to 0.0-10.0
        
        # Determine severity
        severity = self._score_to_severity(final_score)
        
        # Create enhanced score
        enhanced = EnhancedScore(
            base_score=base_score,
            exploitability_boost=exploitability_boost,
            impact_adjustment=impact_adjustment,
            final_score=final_score,
            severity=severity,
            evidence_factors=evidence_factors,
        )
        
        # Compute scoring hash
        enhanced.scoring_hash = self._compute_scoring_hash(scoring_input, enhanced)
        
        logger.info(
            f"Scored finding: base={base_score:.1f}, "
            f"boost={exploitability_boost:.1f}, adjust={impact_adjustment:.1f}, "
            f"final={final_score:.1f}, severity={severity}"
        )
        
        return enhanced
    
    def _compute_evidence_factors(
        self,
        base_score: float,
        static_confidence: float,
        runtime_confidence: float,
        combined_confidence: float,
        exploit_chain_detected: bool,
        has_negative_proof: bool,
    ) -> Dict[str, float]:
        """
        Compute evidence-based adjustments to CVSS score.
        
        Returns:
            Dict with keys: exploitability_boost, impact_adjustment, confidence_weight, etc.
        """
        factors = {}
        
        # Confidence-based weighting
        confidence_weight = combined_confidence  # 0.0-1.0
        factors["confidence_weight"] = confidence_weight
        
        # Runtime evidence increases exploitability when present
        runtime_boost = 0.0
        if runtime_confidence > 0.7:
            # Strong runtime evidence indicates vulnerability is real
            runtime_boost = min(1.5, runtime_confidence * 2.0)  # Cap at +1.5
        factors["runtime_boost"] = runtime_boost
        
        # Exploit chain dramatically increases severity
        exploit_boost = 0.0
        if exploit_chain_detected:
            exploit_boost = 2.0  # +2.0 for proven exploit chain
        factors["exploit_boost"] = exploit_boost
        
        # Negative proof (mitigation) reduces severity
        mitigation_penalty = 0.0
        if has_negative_proof:
            mitigation_penalty = -3.0  # -3.0 if mitigated by input sanitization, etc.
        factors["mitigation_penalty"] = mitigation_penalty
        
        # Static confidence provides baseline
        static_penalty = 0.0
        if static_confidence < 0.5:
            # Low static confidence means less certain (still add but with penalty)
            static_penalty = -0.5
        factors["static_penalty"] = static_penalty
        
        # Combine into exploitability and impact adjustments
        exploitability_boost = runtime_boost + exploit_boost + static_penalty
        impact_adjustment = mitigation_penalty
        
        factors["exploitability_boost"] = exploitability_boost
        factors["impact_adjustment"] = impact_adjustment
        
        return factors
    
    def _finding_type_to_cwe(self, finding_type: str) -> str:
        """Map finding type to CWE"""
        return self.FINDING_TYPE_CWE_MAP.get(finding_type, "CWE-20")
    
    def _score_to_severity(self, score: float) -> str:
        """Convert CVSS score to severity level"""
        if score >= 9.0:
            return "critical"
        elif score >= 7.0:
            return "high"
        elif score >= 4.0:
            return "medium"
        else:
            return "low"
    
    def _compute_scoring_hash(
        self,
        scoring_input: ScoringInput,
        enhanced_score: EnhancedScore,
    ) -> str:
        """Compute SHA256 hash of scoring for determinism validation"""
        import json
        
        data = {
            **scoring_input.to_deterministic_dict(),
            "base_score": round(enhanced_score.base_score, 2),
            "exploitability_boost": round(enhanced_score.exploitability_boost, 2),
            "impact_adjustment": round(enhanced_score.impact_adjustment, 2),
            "final_score": round(enhanced_score.final_score, 2),
            "severity": enhanced_score.severity,
        }
        
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class ScoringBatchProcessor:
    """Process multiple findings through enhanced scoring (deterministic batch)"""
    
    def __init__(self, scorer: Optional[EnhancedCVSSScorer] = None):
        self.scorer = scorer or EnhancedCVSSScorer()
    
    def score_batch(
        self,
        inputs: Dict[str, ScoringInput],
    ) -> Dict[str, EnhancedScore]:
        """
        Score multiple aggregated findings deterministically.
        
        Args:
            inputs: Dict mapping aggregation_id to ScoringInput
            
        Returns:
            Dict mapping aggregation_id to EnhancedScore
        """
        logger.info(f"Processing batch of {len(inputs)} findings through enhanced scoring")
        
        results = {}
        
        # Deterministic processing order
        for agg_id in sorted(inputs.keys()):
            try:
                score = self.scorer.score_aggregated_finding(inputs[agg_id])
                results[agg_id] = score
            except Exception as e:
                logger.error(f"Error scoring {agg_id}: {e}")
                # Return default score on error
                results[agg_id] = EnhancedScore(
                    base_score=5.0,
                    exploitability_boost=0.0,
                    impact_adjustment=0.0,
                    final_score=5.0,
                    severity="medium",
                    evidence_factors={"error": str(e)},
                )
        
        logger.info(f"Batch scoring complete: {len(results)} scores computed")
        
        return results
