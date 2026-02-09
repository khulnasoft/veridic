"""
CI/CD Gating for Automated Security Checks

Provides automated PASS/WARN/FAIL verdicts based on:
- Threat score thresholds
- Drift detection
- Regression analysis
- Deterministic hashing for reproducibility
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from ..scoring.continuous_scoring import ThreatScore
from ..scoring.severity_drift import SeverityDriftDetector, DriftAnalysis
from ..scoring.historical_aggregator import HistoricalAggregator


class Verdict(Enum):
    """CI/CD check verdict."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class CICDCheckResult:
    """Result of CI/CD security check."""
    verdict: Verdict
    score: float
    threshold_fail: float
    threshold_warn: float
    drift_detected: bool
    drift_percentage: Optional[float]
    regression_count: int
    failing_assets: List[str]
    warnings: List[str]
    hash: str
    timestamp: str
    deterministic: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["verdict"] = self.verdict.value
        return data


class CICDGating:
    """
    Automated CI/CD security gating with deterministic verdicts.
    
    Thresholds:
    - FAIL: score >= 70 OR critical regression > 30%
    - WARN: score >= 50 OR major regression > 15%
    - PASS: score < 50 AND no significant regressions
    """
    
    # Threat score thresholds
    FAIL_THRESHOLD = 70.0
    WARN_THRESHOLD = 50.0
    
    # Drift thresholds
    CRITICAL_DRIFT = 30.0  # %
    MAJOR_DRIFT = 15.0     # %
    MINOR_DRIFT = 5.0      # %
    
    def __init__(
        self,
        aggregator: HistoricalAggregator,
        fail_threshold: Optional[float] = None,
        warn_threshold: Optional[float] = None,
    ):
        """
        Initialize CI/CD gating.
        
        Args:
            aggregator: Historical aggregator for drift detection
            fail_threshold: Optional custom FAIL threshold
            warn_threshold: Optional custom WARN threshold
        """
        self.aggregator = aggregator
        self.drift_detector = SeverityDriftDetector(aggregator)
        
        self.fail_threshold = fail_threshold or self.FAIL_THRESHOLD
        self.warn_threshold = warn_threshold or self.WARN_THRESHOLD
    
    def check_asset(
        self,
        asset_id: str,
        current_score: ThreatScore,
    ) -> CICDCheckResult:
        """
        Perform CI/CD check for a single asset.
        
        Args:
            asset_id: Asset identifier
            current_score: Current threat score
            
        Returns:
            CICDCheckResult with verdict
        """
        # Detect drift
        drift = self.drift_detector.detect_drift(asset_id, current_score)
        
        # Determine verdict
        verdict = Verdict.PASS
        warnings = []
        failing_assets = []
        
        # Check score thresholds
        if current_score.score >= self.fail_threshold:
            verdict = Verdict.FAIL
            failing_assets.append(asset_id)
        elif current_score.score >= self.warn_threshold:
            verdict = Verdict.WARN
            warnings.append(f"Score {current_score.score} exceeds warn threshold")
        
        # Check drift
        drift_detected = False
        drift_percentage = None
        
        if drift:
            drift_detected = True
            drift_percentage = drift.drift_percentage
            
            if abs(drift.drift_percentage) >= self.CRITICAL_DRIFT and drift.is_regression:
                verdict = Verdict.FAIL
                failing_assets.append(asset_id)
            elif abs(drift.drift_percentage) >= self.MAJOR_DRIFT and drift.is_regression:
                if verdict == Verdict.PASS:
                    verdict = Verdict.WARN
                warnings.append(
                    f"Regression detected: {drift.drift_percentage}% drift"
                )
        
        # Generate deterministic hash
        check_hash = self._generate_check_hash(
            asset_id,
            current_score,
            drift,
            verdict,
        )
        
        return CICDCheckResult(
            verdict=verdict,
            score=current_score.score,
            threshold_fail=self.fail_threshold,
            threshold_warn=self.warn_threshold,
            drift_detected=drift_detected,
            drift_percentage=drift_percentage,
            regression_count=1 if (drift and drift.is_regression) else 0,
            failing_assets=failing_assets,
            warnings=warnings,
            hash=check_hash,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def check_multiple_assets(
        self,
        scores: Dict[str, ThreatScore],
    ) -> CICDCheckResult:
        """
        Perform CI/CD check for multiple assets (aggregated verdict).
        
        Args:
            scores: Dict mapping asset_id to ThreatScore
            
        Returns:
            Aggregated CICDCheckResult
        """
        all_failing = []
        all_warnings = []
        total_regressions = 0
        any_drift = False
        max_drift = 0.0
        
        # Check each asset
        for asset_id, score in scores.items():
            result = self.check_asset(asset_id, score)
            
            if result.verdict == Verdict.FAIL:
                all_failing.extend(result.failing_assets)
            
            all_warnings.extend(result.warnings)
            total_regressions += result.regression_count
            
            if result.drift_detected:
                any_drift = True
                if result.drift_percentage and abs(result.drift_percentage) > abs(max_drift):
                    max_drift = result.drift_percentage
        
        # Determine overall verdict
        if all_failing:
            verdict = Verdict.FAIL
        elif all_warnings:
            verdict = Verdict.WARN
        else:
            verdict = Verdict.PASS
        
        # Calculate average score
        avg_score = sum(s.score for s in scores.values()) / len(scores) if scores else 0
        
        # Generate deterministic hash
        check_hash = self._generate_multi_check_hash(
            scores,
            verdict,
            all_failing,
        )
        
        return CICDCheckResult(
            verdict=verdict,
            score=round(avg_score, 2),
            threshold_fail=self.fail_threshold,
            threshold_warn=self.warn_threshold,
            drift_detected=any_drift,
            drift_percentage=max_drift if any_drift else None,
            regression_count=total_regressions,
            failing_assets=sorted(set(all_failing)),
            warnings=all_warnings,
            hash=check_hash,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def _generate_check_hash(
        self,
        asset_id: str,
        score: ThreatScore,
        drift: Optional[DriftAnalysis],
        verdict: Verdict,
    ) -> str:
        """Generate deterministic hash for CI/CD check."""
        hash_input = {
            "asset_id": asset_id,
            "score": score.score,
            "score_hash": score.hash,
            "drift": drift.drift_percentage if drift else None,
            "verdict": verdict.value,
            "threshold_fail": self.fail_threshold,
            "threshold_warn": self.warn_threshold,
        }
        
        json_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _generate_multi_check_hash(
        self,
        scores: Dict[str, ThreatScore],
        verdict: Verdict,
        failing_assets: List[str],
    ) -> str:
        """Generate deterministic hash for multi-asset check."""
        hash_input = {
            "scores": {
                asset_id: score.hash
                for asset_id, score in sorted(scores.items())
            },
            "verdict": verdict.value,
            "failing_assets": sorted(failing_assets),
            "threshold_fail": self.fail_threshold,
            "threshold_warn": self.warn_threshold,
        }
        
        json_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def export_check_result(
        self,
        result: CICDCheckResult,
        output_path: str,
    ):
        """
        Export CI/CD check result to JSON file.
        
        Args:
            result: CICDCheckResult to export
            output_path: Path to write JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def should_block_deployment(self, result: CICDCheckResult) -> bool:
        """
        Determine if deployment should be blocked based on result.
        
        Args:
            result: CICDCheckResult
            
        Returns:
            True if deployment should be blocked, False otherwise
        """
        return result.verdict == Verdict.FAIL


# Example usage
if __name__ == "__main__":
    from ..scoring.continuous_scoring import ContinuousScoringEngine, Finding
    
    # Create components
    aggregator = HistoricalAggregator(in_memory=True)
    engine = ContinuousScoringEngine()
    gating = CICDGating(aggregator)
    
    # Create baseline score
    findings_v1 = [
        Finding(
            id="VULN-001",
            type="sql_injection",
            severity="medium",
            confidence=0.7,
            source="static",
        ),
    ]
    
    score_v1 = engine.compute_threat_score("asset-123", findings_v1)
    aggregator.store_score(score_v1)
    print(f"Baseline score: {score_v1.score}")
    
    # Create new score with regression
    findings_v2 = [
        Finding(
            id="VULN-001",
            type="sql_injection",
            severity="critical",
            confidence=0.95,
            source="static",
        ),
        Finding(
            id="VULN-002",
            type="command_injection",
            severity="critical",
            confidence=0.90,
            source="runtime",
        ),
    ]
    
    score_v2 = engine.compute_threat_score("asset-123", findings_v2)
    print(f"New score: {score_v2.score}")
    
    # Run CI/CD check
    result = gating.check_asset("asset-123", score_v2)
    
    print(f"\nCI/CD Check Result:")
    print(f"  Verdict: {result.verdict.value}")
    print(f"  Score: {result.score}")
    print(f"  Drift Detected: {result.drift_detected}")
    if result.drift_percentage:
        print(f"  Drift: {result.drift_percentage}%")
    print(f"  Regressions: {result.regression_count}")
    print(f"  Block Deployment: {gating.should_block_deployment(result)}")
    print(f"  Hash: {result.hash[:16]}...")
