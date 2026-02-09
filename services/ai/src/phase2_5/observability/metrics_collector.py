"""
Metrics Collector for Observability

Collects and exposes metrics for monitoring system health, 
AI reasoning variance, processing time, and verdict counts.

Supports Prometheus exposition format and JSON export.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_prometheus(self) -> str:
        """Convert to Prometheus exposition format."""
        if self.labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
            return f'{self.name}{{{label_str}}} {self.value}'
        return f'{self.name} {self.value}'


class MetricsCollector:
    """
    Collects and manages application metrics.
    
    Metrics tracked:
    - threat_score_total: Counter of threat scores computed
    - threat_score_value: Gauge of current threat scores
    - processing_time_seconds: Histogram of processing times
    - ai_reasoning_variance: Gauge of AI output variance
    - verdict_count: Counter by verdict type (PASS/WARN/FAIL)
    - drift_detection_total: Counter of drift detections
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.start_time = time.time()
    
    # Counter methods
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Increment value
            labels: Optional labels
        """
        key = self._make_key(name, labels or {})
        self.counters[key] += value
        
        metric = Metric(
            name=name,
            value=self.counters[key],
            labels=labels or {},
        )
        self.metrics[name].append(metric)
    
    # Gauge methods
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Set a gauge metric.
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels
        """
        key = self._make_key(name, labels or {})
        self.gauges[key] = value
        
        metric = Metric(
            name=name,
            value=value,
            labels=labels or {},
        )
        self.metrics[name].append(metric)
    
    # Histogram methods
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Observe a value for histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels
        """
        key = self._make_key(name, labels or {})
        self.histograms[key].append(value)
        
        metric = Metric(
            name=name,
            value=value,
            labels=labels or {},
        )
        self.metrics[name].append(metric)
    
    # Convenience methods for specific metrics
    def record_threat_score(self, asset_id: str, score: float):
        """Record a threat score computation."""
        self.increment_counter("threat_score_total")
        self.set_gauge("threat_score_value", score, {"asset_id": asset_id})
    
    def record_processing_time(self, operation: str, duration: float):
        """Record processing time for an operation."""
        self.observe_histogram(
            "processing_time_seconds",
            duration,
            {"operation": operation},
        )
    
    def record_ai_variance(self, variance: float):
        """Record AI reasoning variance."""
        self.set_gauge("ai_reasoning_variance", variance)
    
    def record_verdict(self, verdict: str):
        """Record a verdict (PASS/WARN/FAIL)."""
        self.increment_counter("verdict_count", labels={"verdict": verdict})
    
    def record_drift_detection(self, severity: str):
        """Record a drift detection."""
        self.increment_counter(
            "drift_detection_total",
            labels={"severity": severity},
        )
    
    # Query methods
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = self._make_key(name, labels or {})
        return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value."""
        key = self._make_key(name, labels or {})
        return self.gauges.get(key)
    
    def get_histogram_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, float]:
        """Get histogram statistics (min, max, avg, p50, p95, p99)."""
        key = self._make_key(name, labels or {})
        values = self.histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": self._percentile(sorted_values, 50),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
        }
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key for metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    # Export methods
    def export_prometheus(self) -> str:
        """
        Export all metrics in Prometheus exposition format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        # Add metadata
        lines.append("# HELP threat_score_total Total number of threat scores computed")
        lines.append("# TYPE threat_score_total counter")
        
        # Export counters
        for key, value in self.counters.items():
            name, labels = self._parse_key(key)
            metric = Metric(name=name, value=value, labels=labels)
            lines.append(metric.to_prometheus())
        
        # Export gauges
        for key, value in self.gauges.items():
            name, labels = self._parse_key(key)
            metric = Metric(name=name, value=value,labels=labels)
            lines.append(metric.to_prometheus())
        
        # Export histogram summaries
        for key, values in self.histograms.items():
            name, labels = self._parse_key(key)
            stats = self.get_histogram_stats(name, labels)
            
            for stat_name, stat_value in stats.items():
                metric = Metric(
                    name=f"{name}_{stat_name}",
                    value=stat_value,
                    labels=labels,
                )
                lines.append(metric.to_prometheus())
        
        return "\n".join(lines)
    
    def export_json(self) -> Dict[str, Any]:
        """
        Export all metrics as JSON.
        
        Returns:
            Dictionary of all metrics
        """
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                key: self.get_histogram_stats(name, labels)
                for key in self.histograms
                for name, labels in [self._parse_key(key)]
            },
            "uptime_seconds": time.time() - self.start_time,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _parse_key(self, key: str) -> tuple[str, Dict[str, str]]:
        """Parse metric key into name and labels."""
        if "{" not in key:
            return key, {}
        
        name, label_str = key.split("{", 1)
        label_str = label_str.rstrip("}")
        
        labels = {}
        if label_str:
            for pair in label_str.split(","):
                k, v = pair.split("=", 1)
                labels[k] = v
        
        return name, labels
    
    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.start_time = time.time()


# Example usage
if __name__ == "__main__":
    collector = MetricsCollector()
    
    # Record some metrics
    collector.record_threat_score("asset-1", 75.5)
    collector.record_threat_score("asset-2", 42.3)
    collector.record_processing_time("scoring", 0.245)
    collector.record_processing_time("scoring", 0.198)
    collector.record_verdict("PASS")
    collector.record_verdict("WARN")
    collector.record_ai_variance(0.05)
    
    # Export as JSON
    print("JSON Export:")
    import json
    print(json.dumps(collector.export_json(), indent=2))
    
    print("\nPrometheus Export:")
    print(collector.export_prometheus())
