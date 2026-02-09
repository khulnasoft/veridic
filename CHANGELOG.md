
## [2.5.0] - 2026-02-10

### Phase 2.5: Observability & Continuous Threat Scoring

#### Added

**Continuous Scoring**
- Deterministic threat scoring engine with SHA256 hashing
- Severity-weighted scoring (Critical: 10.0, High: 7.0, Medium: 4.0, Low: 2.0)
- Confidence-based weighting
- Exploit chain multipliers
- Batch scoring support

**Historical Tracking**
- SQLite-based historical aggregator
- In-memory mode for testing
- Time-series score queries
- Automatic cleanup (90-day retention)
- Trend analysis support

**Drift Detection**
- Severity drift detector with three levels:
  - Minor: ±5% drift
  - Major: ±15% drift
  - Critical: ±30% drift
- Regression identification
- Batch drift analysis
- Comprehensive drift reporting

**Observability**
- Prometheus-compatible metrics collector
- Counter, Gauge, and Histogram support
- JSON export for dashboards
- Metrics for:
  - Threat scores
  - Processing times
  - AI variance
  - Verdict distribution
  - Drift detections

**Anomaly Detection**
- Statistical outlier detection (3σ threshold)
- AI variance monitoring (>10% CV)
- Negative proof detection
- Critical regression flagging
- Comprehensive anomaly reporting

**Alert Management**
- Multi-channel alert system
- Support for: Email, Slack, Webhooks, Logging
- Regression alerts
- Anomaly alerts
- CI/CD failure alerts
- Alert filtering and querying

**Integration**
- Phase 2.4 batch connector
- Batch finding conversion
- Multi-batch aggregation
- Batch format export

**CI/CD Gating**
- Automated PASS/WARN/FAIL verdicts
- Threshold-based gating:
  - FAIL: score ≥ 70 OR critical regression >30%
  - WARN: score ≥ 50 OR major regression >15%
  - PASS: score < 50 AND no regressions
- Deterministic hash verification
- Multi-asset aggregation
- Deployment blocking logic

#### Technical Details

- 8 new Python modules (2,500+ lines of code)
- Comprehensive test suite (300+ tests)
- Full documentation with examples
- Prometheus integration
- SQLite persistence
- SHA256 hash-based determinism

#### Testing & Validation

- Unit tests for all components
- integration tests for batch processing
- Determinism validation tests
- CI/CD gating scenario tests
- 100% test coverage on core logic

---

## [2.6.0] - 2026-02-10

### Phase 2.6: Autonomous Remediation & Exploit Validation

#### Added

**Exploit Validation**
- Deterministic payload generator for SQLi, XSS, Path Traversal, and Command Injection
- Exploit simulation engine with non-destructive verification
- Fingerprint-based validation (proof-of-concept verification)
- Machine-verifiable reproducibility scores

**Autonomous Remediation**
- Pattern-based patch synthesizer for critical vulnerabilities
- Isolated patch validation engine
- Automated regression testing support
- Deterministic patch hashing (SHA256)

**Reporting & Evidence**
- "Bounty-Grade" report builder (standardized for HackerOne/Bugcrowd)
- Unified git diff generator for remediation
- Machine-verifiable evidence packaging
- Exploit chain visualization support

**Infrastructure**
- Isolated sandbox runner for safe exploit/patch testing
- Rollback manager for state restoration
- Remediation consistency validator (deterministic checks)

#### Technical Details
- 9 new Python modules in `phase2_6`
- Circular import fix: Renamed internal `ast` module to `ast_engine`
- End-to-end lifecycle tests
- Proof hashes for all verified exploits

#### Dependencies
- Enhanced `dataclasses` usage
- Integration with existing AI reasoning engine

---

## [2.7.0-preview] - 2026-02-10

### Phase 2.7: Continuous Red-Team AI (Preview)

#### Added
- Autonomous attack planner with severity-based prioritization
- Deterministic strategy mutator (URL encoding, case swapping, null prefixes)
- Security coverage analyzer ("Dark Spot" detection in AST)
- Central Red-Team loop with safety kill-switch
- Machine-verifiable attack strategies

#### Improvements
- Enhanced `IsolatedRunner` with Docker-based sandbox backend (mocked for scaffolding)
- LLM-aided patch synthesis logic with temperature-0 enforcement
- Unified `vulnerability_patterns.yaml` for deterministic remediation

---
