# Phase 1 Determinism & Tool Attribution Guide

Complete documentation for enhanced test infrastructure with determinism checks, tool attribution metrics, and PASS/WARN/FAIL reporting.

## Overview

This guide covers the complete Phase 1 validation infrastructure with three core components:

1. **Determinism Checks** - Ensures consistent, repeatable results
2. **Tool Attribution Metrics** - Proves AI value and tool complementarity
3. **PASS/WARN/FAIL Reporting** - Decision-grade verdict system

## 1. Determinism Checks

### Purpose
Validate that the same code produces consistent vulnerability detection across multiple runs.

### What Gets Tested

| Metric | Threshold | Status |
|--------|-----------|--------|
| Finding fingerprint | 100% match | PASS/FAIL |
| Finding count variance | 0 | PASS/FAIL |
| CVSS score delta | ≤ ±0.3 | PASS/WARN |
| Exploit chain consistency | Same nodes | PASS/WARN |

### How It Works

The `tests/determinism.py` module:

1. Runs analysis 3 times on same code
2. Fingerprints each report (SHA256 of normalized findings)
3. Compares fingerprints, CVSS scores, finding counts
4. Returns PASS/WARN/FAIL status

### Fingerprinting Logic

```python
normalized = {
    "findings": [
        {
            "type": finding["type"],
            "line": finding["line"],
            "cwe": finding["cwe"],
            "severity": finding["severity"],
        }
        for finding in report["findings"]
    ]
}
fingerprint = sha256(json.dumps(normalized))
```

This excludes timestamps and IDs to focus on actual findings.

### Status Classification

```
FAIL:   Fingerprints don't match OR finding counts vary
WARN:   CVSS variance > 0.3 OR exploit chains inconsistent
PASS:   Perfect reproducibility
```

### Running Determinism Checks

```bash
# Generate determinism report
make report-determinism

# Expected output:
# {
#   "status": "PASS",
#   "metrics": {
#     "fingerprint_match": true,
#     "finding_count_variance": 0,
#     "cvss_delta": 0.12,
#     "exploit_chain_consistent": true
#   }
# }
```

## 2. Tool Attribution Metrics

### Purpose
Quantify the value AI adds and how tools complement each other.

### Attribution Categories

| Category | Meaning |
|----------|---------|
| `codeql_only` | Found only by CodeQL |
| `semgrep_only` | Found only by Semgrep |
| `static_both` | Found by both CodeQL and Semgrep |
| `ai_correlated` | Linked by AI reasoning (e.g., vulnerability chains) |
| `ai_only` | Pure AI inference (no static tool found it) |

### Finding Schema

```json
{
  "id": "VULN-001",
  "type": "sql_injection",
  "tools": ["codeql"],
  "ai_enhanced": true,
  "confidence": 0.91
}
```

**Key Fields:**
- `tools`: List of which tools detected this
- `ai_enhanced`: Whether AI correlated/refined this finding
- `confidence`: Confidence score (0-1)

### Attribution Examples

**Example 1: Static Tool Detection**
```
Finding: SQL Injection on line 42
Tools: ["codeql"]
Result: codeql_only += 1
```

**Example 2: Both Tools Agree**
```
Finding: XSS on line 105
Tools: ["codeql", "semgrep"]
Result: static_both += 1
```

**Example 3: AI Correlation**
```
Finding: Race Condition
Tools: []
ai_enhanced: true
Result: ai_only += 1 (if found by no static tool)
        ai_correlated += 1 (if enhanced by AI)
```

### Complementarity Analysis

Measures tool overlap and independence:

```python
redundancy_ratio = static_both / total_findings * 100

high_overlap (>50%):   Tools are redundant
balanced (25-50%):     Tools complement well
low_overlap (<25%):    Tools find very different things
```

### Running Tool Attribution

```bash
# Generate tool attribution report
make report-attribution

# Expected output:
# {
#   "total_findings": 16,
#   "attribution": {
#     "codeql_only": 4,
#     "semgrep_only": 2,
#     "static_both": 3,
#     "ai_correlated": 5,
#     "ai_only": 2
#   },
#   "coverage": {
#     "static_tools_coverage": 56.3,
#     "ai_added_findings": 12.5,
#     "ai_enhanced_findings": 31.3
#   }
# }
```

## 3. PASS/WARN/FAIL Reporting

### Classification Rules

#### ✅ PASS
- Detection rate ≥ 80%
- Results are deterministic
- CVSS variance ≤ ±0.3
- No gRPC errors
- AI confidence ≥ 0.60

#### ⚠️ WARN
- Detection rate 70-80%
- CVSS variance > 0.3
- Tool runtime > 15s
- False positive rate > 25%
- AI confidence 0.5-0.6

#### ❌ FAIL
- Detection rate < 70%
- Non-deterministic results
- gRPC crashes
- Tool timeout > 15s
- Critical failures

### Final Verdict Engine

The `tests/final_verdict.py` module evaluates all metrics:

```python
def compute_final_verdict(metrics):
    if metrics["detection_rate"] < 0.70:
        return "FAIL"
    if not metrics["deterministic"]:
        return "FAIL"
    if metrics["cvss_variance"] > 0.3:
        return "WARN"
    return "PASS"
```

### Running Final Verdict

```bash
# Generate final verdict
make report-verdict

# Expected output:
# {
#   "status": "PASS",
#   "summary": "Phase 1 Validation: 8 PASS, 2 WARN, 0 FAIL",
#   "recommendation": "Phase 1 validation PASSED. Proceed to Phase 2..."
# }
```

## 4. Unified Validation Harness

The `scripts/validate_phase1_unified.sh` script orchestrates all 8 validation steps:

1. **Protocol Compilation** - `make proto`
2. **Docker Build** - `make build`
3. **Service Health Check** - `docker-compose up && health check`
4. **Static Analysis Validation** - CodeQL + Semgrep tests
5. **AST Extraction Validation** - All 4 languages
6. **End-to-End Pipeline** - Full analysis flow
7. **Determinism Checks** - 3 runs consistency
8. **Tool Attribution & Final Verdict** - Complete analysis

### Running Unified Validation

```bash
# Single command runs all 8 steps
make validate-unified

# Expected output:
# ═════════════════════════════════
#   Phase 1 Unified Validation
# ═════════════════════════════════
# ✓ Step 1/8: Protocol compilation successful
# ✓ Step 2/8: Docker build successful
# ✓ Step 3/8: Services are healthy
# ✓ Step 4/8: Static analysis tools validated
# ✓ Step 5/8: AST extractors validated
# ✓ Step 6/8: E2E pipeline test successful
# ✓ Step 7/8: Determinism validation passed
# ✓ Step 8/8: Final verdict computed: PASS
# ═════════════════════════════════
#   Validation Summary
# ═════════════════════════════════
# Detection Rate:        87%
# False Positives:       9%
# Deterministic:         YES
# Tool Attribution:
# - CodeQL Only:         4
# - Semgrep Only:        2
# - Static Both:         3
# - AI Correlated:       5
# - AI Only:             2
# FINAL RESULT: PASS
# ═════════════════════════════════
```

## 5. Metrics Aggregator

The `tests/phase1_metrics_aggregator.py` combines all metrics into unified reports:

### Running Aggregated Report

```bash
# Generate comprehensive Phase 1 report
make report-aggregated

# Outputs:
# - phase1_metrics.json   (JSON export)
# - phase1_report.md      (Markdown report)
# - Console summary
```

### Example Aggregated Output

```json
{
  "timestamp": "2026-02-06T10:30:45.123456",
  "summary": {
    "detection_rate": "87%",
    "false_positive_rate": "9%",
    "total_vulnerabilities": 16,
    "determinism_status": "PASS",
    "tool_attribution": {
      "codeql_only": 4,
      "semgrep_only": 2,
      "static_both": 3,
      "ai_only": 2,
      "ai_correlated": 5
    },
    "final_verdict": "PASS",
    "recommendation": "Phase 1 validation PASSED. Proceed to Phase 2..."
  }
}
```

## Quick Reference Commands

```bash
# Individual Checks
make report-determinism      # Determinism checks only
make report-attribution      # Tool attribution only
make report-verdict          # Final verdict only

# Complete Reports
make report-aggregated       # All metrics combined
make validate-unified        # Full 8-step validation

# Debugging
make test-phase1             # Integration tests
make test-determinism        # Determinism tests
make logs                    # View service logs
```

## Decision Tree

```
Run: make validate-unified
         ↓
    Did it PASS?
    ├── YES → Proceed to Phase 2
    ├── WARN → Acceptable with caution (monitor metrics)
    └── FAIL → Fix issues and rerun
```

## Integration with CI/CD

To gate Phase 2 on Phase 1 validation:

```yaml
# .github/workflows/phase1-gate.yml
jobs:
  validate-phase1:
    runs-on: ubuntu-latest
    steps:
      - run: make setup
      - run: make validate-unified
      - name: Check Verdict
        run: |
          VERDICT=$(make report-verdict | grep "status" | cut -d'"' -f4)
          if [ "$VERDICT" = "FAIL" ]; then exit 1; fi
```

## Troubleshooting

### Determinism Mismatch
**Issue:** Different results on consecutive runs
**Solution:** Check for:
- Timestamp exclusion in fingerprinting
- Random seed initialization
- External API rate limits
- System resource constraints

### High False Positives
**Issue:** Many low-confidence findings
**Solution:**
- Review confidence thresholds
- Update Semgrep rule set
- Fine-tune AI prompts
- Run remediation suggestions through manual review

### CVSS Variance
**Issue:** CVSS scores vary > 0.3
**Solution:**
- Check for non-deterministic AI reasoning
- Lock LLM parameters (temperature=0)
- Review scoring logic for conditional branches

## Next Steps

1. **Lock Prompts**: Once Phase 1 PASSES, version control all AI prompts
2. **Scale Testing**: Run on real OSS repositories
3. **Monitor Metrics**: Track detection rate + false positives over time
4. **Phase 2 Planning**: Use these baselines for dynamic analysis
5. **Investor Ready**: Use these metrics to demonstrate security capability

## Files Reference

| File | Purpose |
|------|---------|
| `tests/determinism.py` | Fingerprinting and consistency checks |
| `tests/tool_attribution_metrics.py` | Tool coverage and complementarity analysis |
| `tests/final_verdict.py` | PASS/WARN/FAIL classification engine |
| `tests/phase1_metrics_aggregator.py` | Unified metrics aggregation |
| `scripts/validate_phase1_unified.sh` | Master validation orchestrator |

---

**For detailed implementation, see individual module docstrings and example usage sections.**
