"""
Severity Drift Detector

Detects significant changes in threat scores over time.
Used for regression detection and CI/CD gating.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .continuous_scoring import ThreatScore
from .historical_aggregator import HistoricalAggregator


@dataclass
class DriftAnalysis:
    """Analysis of score drift for an asset."""
    asset_id: str
    current_score: float
    previous_score: float
    drift_percentage: float
    drift_absolute: float
    is_regression: bool
    severity_level: str  # none, minor, major, critical
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SeverityDriftDetector:
    """
    Detects drift in threat scores between analysis runs.
    
    Thresholds:
    - Minor: ±5% drift
    - Major: ±15% drift
    - Critical: ±30% drift
    """
    
    # Drift thresholds (percentage)
    MINOR_THRESHOLD = 5.0
    MAJOR_THRESHOLD = 15.0
    CRITICAL_THRESHOLD = 30.0
    
    def __init__(self, aggregator: HistoricalAggregator):
        """
        Initialize drift detector.
        
        Args:
            aggregator: Historical aggregator for score retrieval
        """
        self.aggregator = aggregator
    
    def detect_drift(
        self,
        asset_id: str,
        current_score: ThreatScore,
    ) -> Optional[DriftAnalysis]:
        """
        Detect drift between current and previous score.
        
        Args:
            asset_id: Asset identifier
            current_score: Current threat score
            
        Returns:
            DriftAnalysis if previous score exists, None otherwise
        """
        # Get score history
        history = self.aggregator.get_score_history(asset_id, days=30)
        
        if len(history) < 1:
            # No previous score to compare against
            return None
        
        # Get previous score (excluding current if already stored)
        previous = history[-1] if history[-1].hash != current_score.hash else (
            history[-2] if len(history) > 1 else None
        )
        
        if previous is None:
            return None
        
        # Calculate drift
        drift_absolute = current_score.score - previous.score
        drift_percentage = (drift_absolute / previous.score * 100) if previous.score > 0 else 0
        
        # Determine if regression (score increased = worse security)
        is_regression = drift_absolute > 0
        
        # Determine severity level
        severity = self._determine_severity(abs(drift_percentage))
        
        return DriftAnalysis(
            asset_id=asset_id,
            current_score=current_score.score,
            previous_score=previous.score,
            drift_percentage=round(drift_percentage, 2),
            drift_absolute=round(drift_absolute, 2),
            is_regression=is_regression,
            severity_level=severity,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def _determine_severity(self, drift_percentage: float) -> str:
        """Determine severity level based on drift percentage."""
        if drift_percentage >= self.CRITICAL_THRESHOLD:
            return "critical"
        elif drift_percentage >= self.MAJOR_THRESHOLD:
            return "major"
        elif drift_percentage >= self.MINOR_THRESHOLD:
            return "minor"
        else:
            return "none"
    
    def batch_detect_drift(
        self,
        current_scores: Dict[str, ThreatScore],
    ) -> Dict[str, DriftAnalysis]:
        """
        Detect drift for multiple assets.
        
        Args:
            current_scores: Dict mapping asset_id to current ThreatScore
            
        Returns:
            Dict mapping asset_id to DriftAnalysis
        """
        drift_analyses = {}
        
        for asset_id, score in current_scores.items():
            analysis = self.detect_drift(asset_id, score)
            if analysis:
                drift_analyses[asset_id] = analysis
        
        return drift_analyses
    
    def get_regressed_assets(
        self,
        drift_analyses: Dict[str, DriftAnalysis],
        min_severity: str = "minor",
    ) -> List[str]:
        """
        Get list of assets with regressions above minimum severity.
        
        Args:
            drift_analyses: Dict of drift analyses
            min_severity: Minimum severity to include
            
        Returns:
            List of asset IDs with regressions
        """
        severity_order = ["none", "minor", "major", "critical"]
        min_level = severity_order.index(min_severity)
        
        regressed = []
        
        for asset_id, analysis in drift_analyses.items():
            if not analysis.is_regression:
                continue
            
            severity_level = severity_order.index(analysis.severity_level)
            if severity_level >= min_level:
                regressed.append(asset_id)
        
        return sorted(regressed)
    
    def generate_drift_report(
        self,
        drift_analyses: Dict[str, DriftAnalysis],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive drift report.
        
        Args:
            drift_analyses: Dict of drift analyses
            
        Returns:
            Report dictionary with statistics
        """
        total_assets = len(drift_analyses)
        
        if total_assets == 0:
            return {
                "total_assets": 0,
                "regressions": 0,
                "improvements": 0,
                "by_severity": {
                    "critical": 0,
                    "major": 0,
                    "minor": 0,
                    "none": 0,
                },
                "average_drift": 0.0,
            }
        
        regressions = sum(1 for a in drift_analyses.values() if a.is_regression)
        improvements = total_assets - regressions
        
        by_severity = {
            "critical": 0,
            "major": 0,
            "minor": 0,
            "none": 0,
        }
        
        total_drift = 0.0
        
        for analysis in drift_analyses.values():
            by_severity[analysis.severity_level] += 1
            total_drift += abs(analysis.drift_percentage)
        
        return {
            "total_assets": total_assets,
            "regressions": regressions,
            "improvements": improvements,
            "by_severity": by_severity,
            "average_drift": round(total_drift / total_assets, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Example usage
if __name__ == "__main__":
    from continuous_scoring import ContinuousScoringEngine, Finding
    
    # Create components
    aggregator = HistoricalAggregator(in_memory=True)
    engine = ContinuousScoringEngine()
    detector = SeverityDriftDetector(aggregator)
    
    # Create and store baseline score
    findings_v1 = [
        Finding(
            id="VULN-001",
            type="sql_injection",
            severity="medium",
            confidence=0.8,
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
            severity="critical",  # Severity increased
            confidence=0.95,
            source="static",
        ),
        Finding(
            id="VULN-002",
            type="xss",
            severity="high",
            confidence=0.85,
            source="static",
        ),
    ]
    
    score_v2 = engine.compute_threat_score("asset-123", findings_v2)
    print(f"New score: {score_v2.score}")
    
    # Detect drift
    drift = detector.detect_drift("asset-123", score_v2)
    
    if drift:
        print(f"\nDrift detected!")
        print(f"  Previous: {drift.previous_score}")
        print(f"  Current: {drift.current_score}")
        print(f"  Drift: {drift.drift_percentage}%")
        print(f"  Regression: {drift.is_regression}")
        print(f"  Severity: {drift.severity_level}")
