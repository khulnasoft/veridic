"""
Comprehensive tests for Phase 2.5 components.

Tests:
- Continuous Scoring determinism
- Historical Aggregation
- Severity Drift Detection
- Metrics Collection
- Anomaly Detection
- Alert Management
- Batch Integration
- CI/CD Gating
"""

import pytest
import tempfile
import json
from pathlib import Path

from ..scoring.continuous_scoring import ContinuousScoringEngine, Finding, ThreatScore
from ..scoring.historical_aggregator import HistoricalAggregator
from ..scoring.severity_drift import SeverityDriftDetector
from ..observability.metrics_collector import MetricsCollector
from ..observability.anomaly_detector import AnomalyDetector
from ..observability.alert_manager import AlertManager, Alert Channel
from ..integration.batch_connector import BatchConnector
from ..integration.ci_cd_gating import CICDGating, Verdict


class TestContinuousScoring:
    """Test continuous scoring engine."""
    
    def test_deterministic_scoring(self):
        """Test that scoring is deterministic."""
        engine = ContinuousScoringEngine()
        
        findings = [
            Finding(
                id="VULN-001",
                type="sql_injection",
                severity="critical",
                confidence=0.95,
                source="static",
            ),
        ]
        
        # Compute score twice
        score1 = engine.compute_threat_score("asset-1", findings, timestamp="2026-01-01T00:00:00")
        score2 = engine.compute_threat_score("asset-1", findings, timestamp="2026-01-01T00:00:00")
        
        # Should be identical
        assert score1.hash == score2.hash
        assert score1.score == score2.score
    
    def test_severity_weighting(self):
        """Test that severity affects score correctly."""
        engine = ContinuousScoringEngine()
        
        critical_finding = [
            Finding(id="V1", type="sqli", severity="critical", confidence=1.0, source="static"),
        ]
        
        low_finding = [
            Finding(id="V2", type="xss", severity="low", confidence=1.0, source="static"),
        ]
        
        critical_score = engine.compute_threat_score("asset-1", critical_finding)
        low_score = engine.compute_threat_score("asset-2", low_finding)
        
        assert critical_score.score > low_score.score
    
    def test_hash_verification(self):
        """Test hash verification."""
        engine = ContinuousScoringEngine()
        
        findings = [
            Finding(id="V1", type="sqli", severity="high", confidence=0.9, source="static"),
        ]
        
        score = engine.compute_threat_score("asset-1", findings)
        
        # Verify hash
        assert engine.verify_score_hash(score, findings)


class TestHistoricalAggregator:
    """Test historical aggregator."""
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving scores."""
        aggregator = HistoricalAggregator(in_memory=True)
        engine = ContinuousScoringEngine()
        
        finding = [
            Finding(id="V1", type="sqli", severity="medium", confidence=0.8, source="static"),
        ]
        
        score = engine.compute_threat_score("asset-1", finding)
        aggregator.store_score(score)
        
        latest = aggregator.get_latest_score("asset-1")
        
        assert latest is not None
        assert latest.asset_id == "asset-1"
        assert latest.hash == score.hash
    
    def test_score_history(self):
        """Test retrieving score history."""
        aggregator = HistoricalAggregator(in_memory=True)
        engine = ContinuousScoringEngine()
        
        # Store multiple scores
        for i in range(5):
            finding = [
                Finding(id=f"V{i}", type="sqli", severity="medium", confidence=0.8, source="static"),
            ]
            score = engine.compute_threat_score("asset-1", finding)
            aggregator.store_score(score)
        
        history = aggregator.get_score_history("asset-1")
        
        assert len(history) == 5


class TestSeverityDrift:
    """Test severity drift detection."""
    
    def test_drift_detection(self):
        """Test drift detection between scores."""
        aggregator = HistoricalAggregator(in_memory=True)
        engine = ContinuousScoringEngine()
        detector = SeverityDriftDetector(aggregator)
        
        # Baseline score
        findings_v1 = [
            Finding(id="V1", type="sqli", severity="medium", confidence=0.7, source="static"),
        ]
        score_v1 = engine.compute_threat_score("asset-1", findings_v1)
        aggregator.store_score(score_v1)
        
        # Regressed score
        findings_v2 = [
            Finding(id="V1", type="sqli", severity="critical", confidence=0.95, source="static"),
            Finding(id="V2", type="xss", severity="high", confidence=0.85, source="static"),
        ]
        score_v2 = engine.compute_threat_score("asset-1", findings_v2)
        
        # Detect drift
        drift = detector.detect_drift("asset-1", score_v2)
        
        assert drift is not None
        assert drift.is_regression
        assert drift.drift_percentage > 0
    
    def test_drift_severity_levels(self):
        """Test drift severity classification."""
        detector = SeverityDriftDetector(HistoricalAggregator(in_memory=True))
        
        # Test severity determination
        assert detector._determine_severity(3.0) == "none"
        assert detector._determine_severity(7.0) == "minor"
        assert detector._determine_severity(20.0) == "major"
        assert detector._determine_severity(35.0) == "critical"


class TestMetricsCollector:
    """Test metrics collector."""
    
    def test_counter_increment(self):
        """Test counter increments."""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter")
        collector.increment_counter("test_counter")
        
        assert collector.get_counter("test_counter") == 2.0
    
    def test_gauge_set(self):
        """Test gauge setting."""
        collector = MetricsCollector()
        
        collector.set_gauge("test_gauge", 42.5)
        
        assert collector.get_gauge("test_gauge") == 42.5
    
    def test_histogram_stats(self):
        """Test histogram statistics."""
        collector = MetricsCollector()
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for v in values:
            collector.observe_histogram("test_histogram", v)
        
        stats = collector.get_histogram_stats("test_histogram")
        
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["avg"] == 3.0


class TestAnomalyDetector:
    """Test anomaly detector."""
    
    def test_score_spike_detection(self):
        """Test score spike detection."""
        detector = AnomalyDetector()
        
        historical = [45.0, 47.0, 46.0, 48.0, 46.5]
        current = 95.0  # Spike!
        
        anomaly = detector.detect_score_spike("asset-1", current, historical)
        
        assert anomaly is not None
        assert anomaly.anomaly_type == "score_spike"
        assert anomaly.severity in ["high", "critical"]
    
    def test_ai_variance_detection(self):
        """Test AI variance detection."""
        detector = AnomalyDetector()
        
        ai_scores = [75.0, 76.0, 92.0, 74.0]  # One outlier
        
        anomaly = detector.detect_ai_variance("asset-1", ai_scores)
        
        assert anomaly is not None
        assert anomaly.anomaly_type == "ai_variance"


class TestAlertManager:
    """Test alert manager."""
    
    def test_send_alert(self):
        """Test sending alerts."""
        manager = AlertManager()
        
        alert = manager.send_alert(
            title="Test Alert",
            message="This is a test",
            severity="high",
            channel=AlertChannel.LOG,
        )
        
        assert alert.sent
        assert alert.severity == "high"
    
    def test_regression_alert(self):
        """Test regression alert."""
        manager = AlertManager()
        
        alert = manager.send_regression_alert(
            asset_id="asset-1",
            drift_percentage=35.0,
            current_score=85.0,
            previous_score=62.0,
        )
        
        assert alert.severity == "critical"
        assert "regression" in alert.title.lower()


class TestBatchConnector:
    """Test batch connector."""
    
    def test_convert_batch_findings(self):
        """Test converting batch findings."""
        connector = BatchConnector()
        
        batch_findings = [
            {
                "id": "VULN-001",
                "type": "sql_injection",
                "severity": "critical",
                "confidence": 0.95,
                "source": "static",
            },
        ]
        
        findings = connector.convert_batch_findings(batch_findings)
        
        assert len(findings) == 1
        assert findings[0].id == "VULN-001"
        assert findings[0].severity == "critical"
    
    def test_process_batch_file(self):
        """Test processing batch file."""
        connector = BatchConnector()
        
        batch_data = {
            "findings": [
                {
                    "id": "V1",
                    "type": "sqli",
                    "severity": "high",
                    "confidence": 0.9,
                    "source": "static",
                },
            ]
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name
        
        try:
            score = connector.process_batch_file(temp_file, "test-asset")
            
            assert score.asset_id == "test-asset"
            assert score.findings_count == 1
        finally:
            Path(temp_file).unlink()


class TestCICDGating:
    """Test CI/CD gating."""
    
    def test_pass_verdict(self):
        """Test PASS verdict."""
        aggregator = HistoricalAggregator(in_memory=True)
        engine = ContinuousScoringEngine()
        gating = CICDGating(aggregator)
        
        # Low score findings
        findings = [
            Finding(id="V1", type="info", severity="low", confidence=0.5, source="static"),
        ]
        
        score = engine.compute_threat_score("asset-1", findings)
        result = gating.check_asset("asset-1", score)
        
        assert result.verdict == Verdict.PASS
        assert not gating.should_block_deployment(result)
    
    def test_fail_verdict_high_score(self):
        """Test FAIL verdict for high score."""
        aggregator = HistoricalAggregator(in_memory=True)
        engine = ContinuousScoringEngine()
        gating = CICDGating(aggregator)
        
        # High score findings
        findings = [
            Finding(id="V1", type="sqli", severity="critical", confidence=0.95, source="static"),
            Finding(id="V2", type="xss", severity="critical", confidence=0.90, source="static"),
            Finding(id="V3", type="cmd_inject", severity="high", confidence=0.88, source="runtime"),
        ]
        
        score = engine.compute_threat_score("asset-1", findings)
        result = gating.check_asset("asset-1", score)
        
        assert result.verdict == Verdict.FAIL
        assert gating.should_block_deployment(result)
    
    def test_fail_verdict_regression(self):
        """Test FAIL verdict for critical regression."""
        aggregator = HistoricalAggregator(in_memory=True)
        engine = ContinuousScoringEngine()
        gating = CICDGating(aggregator)
        
        # Store baseline
        baseline = [
            Finding(id="V1", type="sqli", severity="low", confidence=0.5, source="static"),
        ]
        score_v1 = engine.compute_threat_score("asset-1", baseline)
        aggregator.store_score(score_v1)
        
        # Create regression
        regression = [
            Finding(id="V1", type="sqli", severity="critical", confidence=0.95, source="static"),
            Finding(id="V2", type="cmd_inject", severity="critical", confidence=0.90, source="runtime"),
        ]
        score_v2 = engine.compute_threat_score("asset-1", regression)
        
        result = gating.check_asset("asset-1", score_v2)
        
        assert result.verdict == Verdict.FAIL
        assert result.regression_count > 0
        assert gating.should_block_deployment(result)
    
    def test_deterministic_hash(self):
        """Test CI/CD check hash is deterministic."""
        aggregator = HistoricalAggregator(in_memory=True)
        engine = ContinuousScoringEngine()
        gating = CICDGating(aggregator)
        
        findings = [
            Finding(id="V1", type="sqli", severity="medium", confidence=0.7, source="static"),
        ]
        
        score = engine.compute_threat_score("asset-1", findings, timestamp="2026-01-01T00:00:00")
        
        result1 = gating.check_asset("asset-1", score)
        result2 = gating.check_asset("asset-1", score)
        
        # Hashes should match (deterministic)
        assert result1.hash == result2.hash


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
