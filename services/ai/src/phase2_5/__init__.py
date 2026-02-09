"""
Phase 2.5: Observability & Continuous Threat Scoring

This module provides real-time threat scoring, observability metrics,
and CI/CD integration for continuous security monitoring.

Key Components:
- Continuous Scoring Engine
- Historical Aggregation
- Severity Drift Detection
- Observability Metrics
- Anomaly Detection
- CI/CD Gating
"""

from .scoring.continuous_scoring import ContinuousScoringEngine
from .scoring.historical_aggregator import HistoricalAggregator
from .scoring.severity_drift import SeverityDriftDetector
from .observability.metrics_collector import MetricsCollector
from .observability.anomaly_detector import AnomalyDetector
from .observability.alert_manager import AlertManager
from .integration.batch_connector import BatchConnector
from .integration.ci_cd_gating import CICDGating

__all__ = [
    "ContinuousScoringEngine",
    "HistoricalAggregator",
    "SeverityDriftDetector",
    "MetricsCollector",
    "AnomalyDetector",
    "AlertManager",
    "BatchConnector",
    "CICDGating",
]

__version__ = "2.5.0"
