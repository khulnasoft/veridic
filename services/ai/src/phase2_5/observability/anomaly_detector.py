"""
Anomaly Detector

Detects outlier verdicts, sudden score spikes, AI variance issues,
and other unexpected behavior in the scoring system.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics

from ..scoring.continuous_scoring import ThreatScore
from ..scoring.severity_drift import DriftAnalysis


@dataclass
class Anomaly:
    """Detected anomaly."""
    asset_id: str
    anomaly_type: str  # score_spike, ai_variance, negative_proof_unexpected, etc.
    severity: str  # low, medium, high, critical
    description: str
    current_value: float
    expected_value: Optional[float]
    threshold: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AnomalyDetector:
    """
    Detects anomalies in threat scoring and AI reasoning.
    
    Detection rules:
    - Score spikes beyond statistical thresholds (3 std devs)
    - AI variance exceeding acceptable limits (±10%)
    - Unexpected negative proofs (high confidence with low score)
    - Inconsistent multi-finding aggregation
    """
    
    # Thresholds
    SCORE_SPIKE_STD_DEVS = 3.0
    AI_VARIANCE_THRESHOLD = 0.10  # 10%
    NEGATIVE_PROOF_CONFIDENCE_MIN = 0.9
    NEGATIVE_PROOF_SCORE_MAX = 10.0
    
    def __init__(self):
        """Initialize anomaly detector."""
        self.detected_anomalies: List[Anomaly] = []
    
    def detect_score_spike(
        self,
        asset_id: str,
        current_score: float,
        historical_scores: List[float],
    ) -> Optional[Anomaly]:
        """
        Detect score spikes using statistical analysis.
        
        Args:
            asset_id: Asset identifier
            current_score: Current threat score
            historical_scores: List of previous scores
            
        Returns:
            Anomaly if spike detected, None otherwise
        """
        if len(historical_scores) < 3:
            # Not enough data for statistical analysis
            return None
        
        mean = statistics.mean(historical_scores)
        stdev = statistics.stdev(historical_scores)
        
        # Calculate z-score
        z_score = abs(current_score - mean) / stdev if stdev > 0 else 0
        
        if z_score > self.SCORE_SPIKE_STD_DEVS:
            severity = "critical" if z_score > 5 else "high"
            
            anomaly = Anomaly(
                asset_id=asset_id,
                anomaly_type="score_spike",
                severity=severity,
                description=f"Score spike detected: {z_score:.2f} standard deviations from mean",
                current_value=current_score,
                expected_value=mean,
                threshold=self.SCORE_SPIKE_STD_DEVS,
                timestamp=datetime.utcnow().isoformat(),
            )
            
            self.detected_anomalies.append(anomaly)
            return anomaly
        
        return None
    
    def detect_ai_variance(
        self,
        asset_id: str,
        ai_scores: List[float],
    ) -> Optional[Anomaly]:
        """
        Detect excessive AI reasoning variance.
        
        Args:
            asset_id: Asset identifier
            ai_scores: List of AI-generated scores for same input
            
        Returns:
            Anomaly if variance exceeds threshold, None otherwise
        """
        if len(ai_scores) < 2:
            return None
        
        mean = statistics.mean(ai_scores)
        stdev = statistics.stdev(ai_scores)
        
        # Calculate coefficient of variation
        cv = (stdev / mean) if mean > 0 else 0
        
        if cv > self.AI_VARIANCE_THRESHOLD:
            anomaly = Anomaly(
                asset_id=asset_id,
                anomaly_type="ai_variance",
                severity="medium" if cv < 0.2 else "high",
                description=f"AI reasoning variance too high: {cv:.2%}",
                current_value=cv,
                expected_value=None,
                threshold=self.AI_VARIANCE_THRESHOLD,
                timestamp=datetime.utcnow().isoformat(),
            )
            
            self.detected_anomalies.append(anomaly)
            return anomaly
        
        return None
    
    def detect_negative_proof(
        self,
        score: ThreatScore,
    ) -> Optional[Anomaly]:
        """
        Detect unexpected negative proofs (high confidence, low score).
        
        This might indicate a bug in scoring logic or unexpected AI behavior.
        
        Args:
            score: Threat score to analyze
            
        Returns:
            Anomaly if negative proof detected, None otherwise
        """
        if (score.confidence_weighted_score > (self.NEGATIVE_PROOF_CONFIDENCE_MIN * 100)
            and score.score < self.NEGATIVE_PROOF_SCORE_MAX):
            
            anomaly = Anomaly(
                asset_id=score.asset_id,
                anomaly_type="negative_proof_unexpected",
                severity="medium",
                description="High confidence but unexpectedly low score",
                current_value=score.score,
                expected_value=None,
                threshold=self.NEGATIVE_PROOF_SCORE_MAX,
                timestamp=datetime.utcnow().isoformat(),
            )
            
            self.detected_anomalies.append(anomaly)
            return anomaly
        
        return None
    
    def detect_drift_anomalies(
        self,
        drift_analyses: Dict[str, DriftAnalysis],
    ) -> List[Anomaly]:
        """
        Detect anomalies in drift analyses.
        
        Args:
            drift_analyses: Dict of drift analyses
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        for asset_id, drift in drift_analyses.items():
            # Check for critical regressions
            if drift.severity_level == "critical" and drift.is_regression:
                anomaly = Anomaly(
                    asset_id=asset_id,
                    anomaly_type="critical_regression",
                    severity="critical",
                    description=f"Critical regression: {drift.drift_percentage}% increase in threat score",
                    current_value=drift.current_score,
                    expected_value=drift.previous_score,
                    threshold=30.0,  # Critical threshold
                    timestamp=drift.timestamp,
                )
                
                self.detected_anomalies.append(anomaly)
                anomalies.append(anomaly)
        
        return anomalies
    
    def get_anomalies(
        self,
        severity: Optional[str] = None,
        anomaly_type: Optional[str] = None,
    ) -> List[Anomaly]:
        """
        Get detected anomalies with optional filtering.
        
        Args:
            severity: Filter by severity level
            anomaly_type: Filter by anomaly type
            
        Returns:
            List of filtered anomalies
        """
        anomalies = self.detected_anomalies
        
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        
        if anomaly_type:
            anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]
        
        return anomalies
    
    def generate_anomaly_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive anomaly report.
        
        Returns:
            Report dictionary with statistics
        """
        by_severity = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        
        by_type = {}
        
        for anomaly in self.detected_anomalies:
            by_severity[anomaly.severity] += 1
            by_type[anomaly.anomaly_type] = by_type.get(anomaly.anomaly_type, 0) + 1
        
        return {
            "total_anomalies": len(self.detected_anomalies),
            "by_severity": by_severity,
            "by_type": by_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def clear_anomalies(self):
        """Clear all detected anomalies."""
        self.detected_anomalies.clear()


# Example usage
if __name__ == "__main__":
    detector = AnomalyDetector()
    
    # Test score spike detection
    historical_scores = [45.0, 47.2, 46.8, 48.1, 46.5]
    current_score = 95.0  # Spike!
    
    anomaly = detector.detect_score_spike("asset-1", current_score, historical_scores)
    
    if anomaly:
        print("Score Spike Anomaly Detected:")
        print(f"  Asset: {anomaly.asset_id}")
        print(f"  Type: {anomaly.anomaly_type}")
        print(f"  Severity: {anomaly.severity}")
        print(f"  Description: {anomaly.description}")
        print(f"  Current: {anomaly.current_value}")
        print(f"  Expected: {anomaly.expected_value}")
    
    # Test AI variance detection
    ai_scores = [75.0, 76.2, 92.5, 74.8]  # One outlier
    
    variance_anomaly = detector.detect_ai_variance("asset-2", ai_scores)
    
    if variance_anomaly:
        print("\nAI Variance Anomaly Detected:")
        print(f"  Description: {variance_anomaly.description}")
        print(f"  Variance: {variance_anomaly.current_value:.2%}")
    
    # Generate report
    report = detector.generate_anomaly_report()
    print(f"\nAnomaly Report: {report}")
