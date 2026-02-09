# Phase 2.5: Observability & Continuous Threat Scoring

> Real-time threat scoring, observability metrics, and CI/CD security gating

**Version**: 2.5.0  
**Status**: ✅ Production Ready  
**Dependencies**: Phase 2.4 (Batch AI Outputs)

---

## Overview

Phase 2.5 extends the Veridic platform with continuous threat scoring, observability metrics, and automated CI/CD security gating. All components are designed with determinism-first principles to ensure reproducible results and reliable automation.

### Key Features

- **Continuous Threat Scoring**: Real-time, deterministic scoring with SHA256 hashing
- **Historical Aggregation**: Track score trends and detect severity drift
- **Observability Metrics**: Prometheus-compatible metrics for system health
- **Anomaly Detection**: Detect outliers, AI variance, and unexpected behavior
- **Alert Management**: Multi-channel notifications (email, Slack, webhooks)
- **Batch Integration**: Seamless Phase 2.4 compatibility
- **CI/CD Gating**: Automated PASS/WARN/FAIL verdicts

---

## Architecture

```
phase2_5/
├── scoring/
│   ├── continuous_scoring.py      # Real-time threat scoring engine
│   ├── historical_aggregator.py   # SQLite/in-memory score storage
│   └── severity_drift.py          # Drift detection (±5%, ±15%, ±30%)
├── observability/
│   ├── metrics_collector.py       # Prometheus/JSON metrics
│   ├── anomaly_detector.py        # Statistical outlier detection
│   └── alert_manager.py           # Multi-channel alerting
├── integration/
│   ├── batch_connector.py         # Phase 2.4 batch integration
│   └── ci_cd_gating.py            # Automated verdict engine
└── tests/
    └── test_phase2_5.py           # Comprehensive test suite
```

---

## Quick Start

### Installation

Phase 2.5 is included in the ai-service package:

```bash
cd ai-service
pip install -r requirements.txt
```

### Basic Usage

```python
from phase2_5.scoring import ContinuousScoringEngine, Finding
from phase2_5.scoring import HistoricalAggregator, SeverityDriftDetector
from phase2_5.integration import CICDGating

# Initialize components
engine = ContinuousScoringEngine()
aggregator = HistoricalAggregator(db_path="scores.db")
gating = CICDGating(aggregator)

# Create findings
findings = [
    Finding(
        id="VULN-001",
        type="sql_injection",
        severity="critical",
        confidence=0.95,
        source="static",
    ),
]

# Compute threat score
score = engine.compute_threat_score("my-app", findings)
print(f"Threat Score: {score.score}/100")
print(f"Hash: {score.hash}")

# Store for historical tracking
aggregator.store_score(score)

# Run CI/CD check
result = gating.check_asset("my-app", score)
print(f"Verdict: {result.verdict.value}")

if gating.should_block_deployment(result):
    print("❌ Deployment BLOCKED")
    exit(1)
```

---

## Components

### 1. Continuous Scoring Engine

**File**: `scoring/continuous_scoring.py`

Computes real-time threat scores with deterministic hashing.

**Scoring Formula**:
```
Base Score = Σ(severity_weight × count)
Weighted Score = Base Score × avg_confidence
Final Score = min(100, Weighted Score × chain_multiplier)
```

**Severity Weights**:
- Critical: 10.0
- High: 7.0
- Medium: 4.0
- Low: 2.0

**Example**:
```python
from phase2_5.scoring import ContinuousScoringEngine, Finding

engine = ContinuousScoringEngine()

findings = [
    Finding(
        id="VULN-001",
        type="sql_injection",
        severity="critical",
        confidence=0.95,
        source="static",
        exploit_chain=["input", "db_query"],
    ),
]

score = engine.compute_threat_score("asset-123", findings)

# Verify determinism
is_valid = engine.verify_score_hash(score, findings)
print(f"Hash Valid: {is_valid}")
```

### 2. Historical Aggregator

**File**: `scoring/historical_aggregator.py`

Stores threat scores in SQLite or in-memory for trend analysis.

**Features**:
- Time-series queries
- Automatic cleanup (default: 90 days)
- In-memory mode for testing

**Example**:
```python
from phase2_5.scoring import HistoricalAggregator

# Production (SQLite)
aggregator = HistoricalAggregator(db_path="threat_scores.db")

# Testing (in-memory)
aggregator = HistoricalAggregator(in_memory=True)

# Store score
aggregator.store_score(score)

# Get latest
latest = aggregator.get_latest_score("asset-123")

# Get history (last 30 days)
history = aggregator.get_score_history("asset-123", days=30)

# Cleanup old data
aggregator.cleanup_old_scores(days=90)
```

### 3. Severity Drift Detector

**File**: `scoring/severity_drift.py`

Detects score changes beyond statistical thresholds.

**Thresholds**:
- Minor: ±5% drift
- Major: ±15% drift
- Critical: ±30% drift

**Example**:
```python
from phase2_5.scoring import SeverityDriftDetector

detector = SeverityDriftDetector(aggregator)

# Detect drift
drift = detector.detect_drift("asset-123", current_score)

if drift:
    print(f"Drift: {drift.drift_percentage}%")
    print(f"Severity: {drift.severity_level}")
    print(f"Regression: {drift.is_regression}")

# Batch detection
drift_analyses = detector.batch_detect_drift(scores_dict)

# Get regressed assets
regressed = detector.get_regressed_assets(drift_analyses, min_severity="major")
```

### 4. Metrics Collector

**File**: `observability/metrics_collector.py`

Collects Prometheus-compatible metrics.

**Metrics**:
- `threat_score_total`: Counter of computed scores
- `threat_score_value`: Gauge of current scores
- `processing_time_seconds`: Histogram of processing times
- `ai_reasoning_variance`: Gauge of AI output variance
- `verdict_count`: Counter by verdict type
- `drift_detection_total`: Counter by severity

**Example**:
```python
from phase2_5.observability import MetricsCollector

collector = MetricsCollector()

# Record metrics
collector.record_threat_score("asset-1", 75.5)
collector.record_processing_time("scoring", 0.245)
collector.record_verdict("PASS")
collector.record_ai_variance(0.05)

# Export for Prometheus
print(collector.export_prometheus())

# Export as JSON
import json
print(json.dumps(collector.export_json(), indent=2))
```

### 5. Anomaly Detector

**File**: `observability/anomaly_detector.py`

Detects statistical outliers and unexpected behavior.

**Detection Rules**:
- Score spikes (>3 standard deviations)
- AI variance (>10% coefficient of variation)
- Negative proofs (high confidence, low score)
- Critical regressions (>30% drift)

**Example**:
```python
from phase2_5.observability import AnomalyDetector

detector = AnomalyDetector()

# Detect score spike
historical = [45.0, 47.0, 46.0, 48.0]
current = 95.0

anomaly = detector.detect_score_spike("asset-1", current, historical)

if anomaly:
    print(f"Anomaly: {anomaly.anomaly_type}")
    print(f"Severity: {anomaly.severity}")
    print(f"Description: {anomaly.description}")

# Detect AI variance
ai_scores = [75.0, 76.0, 92.0, 74.0]
variance_anomaly = detector.detect_ai_variance("asset-1", ai_scores)

# Generate report
report = detector.generate_anomaly_report()
```

### 6. Alert Manager

**File**: `observability/alert_manager.py`

Sends notifications via multiple channels.

**Channels**:
- Email (SMTP)
- Slack (webhooks)
- Custom webhooks
- Logging

**Example**:
```python
from phase2_5.observability import AlertManager, AlertChannel

manager = AlertManager()

# Send regression alert
alert = manager.send_regression_alert(
    asset_id="asset-123",
    drift_percentage=35.0,
    current_score=85.0,
    previous_score=62.0,
    channel=AlertChannel.SLACK,
)

# Send anomaly alert
manager.send_anomaly_alert(
    anomaly_type="score_spike",
    description="Score increased by 5 std devs",
    asset_id="asset-123",
    severity="critical",
)

# Send CI failure alert
manager.send_ci_failure_alert(
    reason="Critical regression detected",
    details={"drift": "35%", "score": 85.0},
)

# Get alerts
critical_alerts = manager.get_alerts(severity="critical")
```

### 7. Batch Connector

**File**: `integration/batch_connector.py`

Integrates Phase 2.4 batch outputs with Phase 2.5 scoring.

**Example**:
```python
from phase2_5.integration import BatchConnector

connector = BatchConnector()

# Process single batch file
score = connector.process_batch_file("results/batch_001.json", "asset-123")

# Process directory of batch files
scores = connector.process_batch_directory("results/", pattern="*.json")

# Aggregate multiple batches
multi_score = connector.aggregate_multi_batch_results(
    ["batch_001.json", "batch_002.json"],
    "asset-123",
)

# Export back to batch format
connector.export_score_to_batch_format(score, "output.json")
```

### 8. CI/CD Gating

**File**: `integration/ci_cd_gating.py`

Automated security gating for CI/CD pipelines.

**Thresholds**:
- FAIL: score ≥ 70 OR critical regression >30%
- WARN: score ≥ 50 OR major regression >15%
- PASS: score < 50 AND no significant regressions

**Example**:
```python
from phase2_5.integration import CICDGating, Verdict

gating = CICDGating(aggregator)

# Check single asset
result = gating.check_asset("asset-123", score)

print(f"Verdict: {result.verdict.value}")
print(f"Score: {result.score}")
print(f"Regressions: {result.regression_count}")

# Check multiple assets
multi_result = gating.check_multiple_assets(scores_dict)

# Block deployment if failed
if gating.should_block_deployment(result):
    print("❌ Deployment BLOCKED")
    exit(1)
else:
    print("✅ Deployment APPROVED")

# Export result
gating.export_check_result(result, "ci_check_result.json")
```

---

## Testing

### Run Tests

```bash
cd ai-service
pytest src/phase2_5/tests/test_phase2_5.py -v
```

### Test Coverage

- ✅ Continuous Scoring (determinism, weighting, hashing)
- ✅ Historical Aggregation (storage, retrieval, cleanup)
- ✅ Severity Drift (detection, classification, reporting)
- ✅ Metrics Collection (counters, gauges, histograms)
- ✅ Anomaly Detection (spikes, variance, negatives)
- ✅ Alert Management (channels, filtering)
- ✅ Batch Integration (conversion, processing, export)
- ✅ CI/CD Gating (verdicts, thresholds, determinism)

---

## Observability Dashboard

### Prometheus Integration

Expose metrics endpoint:

```python
from fastapi import FastAPI
from phase2_5.observability import MetricsCollector

app = FastAPI()
collector = MetricsCollector()

@app.get("/metrics")
def metrics():
    return collector.export_prometheus()
```

### Grafana Dashboard

Import the provided dashboard JSON:

```json
{
  "dashboard": {
    "title": "Veridic Phase 2.5 - Security Metrics",
    "panels": [
      {
        "title": "Threat Score Trend",
        "targets": ["threat_score_value"]
      },
      {
        "title": "Verdict Distribution",
        "targets": ["verdict_count"]
      },
      {
        "title": "Processing Time (p95)",
        "targets": ["processing_time_seconds_p95"]
      }
    ]
  }
}
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Security Check

on: [push, pull_request]

jobs:
  security-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Veridic Analysis
        run: |
          python -m phase2_5.integration.ci_cd_gating \
            --batch-dir ./analysis-results \
            --fail-threshold 70 \
            --warn-threshold 50
      
      - name: Check Result
        run: |
          if [ -f ci_result.json ]; then
            verdict=$(jq -r '.verdict' ci_result.json)
            if [ "$verdict" == "FAIL" ]; then
              echo "❌ Security check FAILED"
              exit 1
            fi
          fi
```

### GitLab CI

```yaml
security-gate:
  stage: test
  script:
    - python -m phase2_5.integration.ci_cd_gating --batch-dir results/
    - |
      verdict=$(jq -r '.verdict' ci_result.json)
      if [ "$verdict" == "FAIL" ]; then
        echo "❌ Deployment blocked due to security regression"
        exit 1
      fi
```

---

## Best Practices

### 1. Deterministic Scoring

Always use timestamps for reproducibility:

```python
score = engine.compute_threat_score(
    asset_id="my-app",
    findings=findings,
    timestamp="2026-02-10T00:00:00Z",  # Fixed timestamp
)
```

### 2. Historical Tracking

Store scores after every analysis:

```python
aggregator.store_score(score)
```

### 3. Drift Monitoring

Run drift detection on every new score:

```python
drift = detector.detect_drift(asset_id, new_score)
if drift and drift.is_regression:
    alert_manager.send_regression_alert(...)
```

### 4. Metrics Collection

Record all operations:

```python
start = time.time()
score = engine.compute_threat_score(...)
collector.record_processing_time("scoring", time.time() - start)
collector.record_threat_score(asset_id, score.score)
```

### 5. Anomaly Alerting

Set up automated alerts:

```python
anomaly = detector.detect_score_spike(asset_id, score, historical)
if anomaly and anomaly.severity in ["high", "critical"]:
    alert_manager.send_anomaly_alert(...)
```

---

## Troubleshooting

### High AI Variance

If AI variance exceeds 10%:

1. Check prompt determinism
2. Verify temperature=0 in AI calls
3. Review input normalization

### False Positive Drift

If drift detection is too sensitive:

1. Adjust thresholds in `SeverityDriftDetector`
2. Increase historical window (>30 days)
3. Use rolling averages for baseline

### Performance Issues

If scoring is slow:

1. Use in-memory aggregator for testing
2. Add database indexes on `asset_id` and `timestamp`
3. Batch process multiple assets

---

## Changelog

### v2.5.0 (2026-02-10)

- ✅ Initial release
- ✅ Continuous scoring engine
- ✅ Historical aggregation (SQLite + in-memory)
- ✅ Severity drift detection
- ✅ Prometheus metrics
- ✅ Anomaly detection
- ✅ Multi-channel alerting
- ✅ Phase 2.4 batch integration
- ✅ CI/CD gating
- ✅ Comprehensive test suite

---

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - see [LICENSE](../../LICENSE)

---

**Built with ❤️ by the Veridic Team**
