# Phase 1 Validation - Quick Reference Card

## One-Command Validation

```bash
make validate
```

Runs all 8 validation steps and generates comprehensive report.

---

## Individual Test Commands

| Command | Purpose | Runtime |
|---------|---------|---------|
| `make test-determinism` | Check consistency (3 runs) | 5-10m |
| `make report-complementarity` | Tool overlap analysis | <1m |
| `make report-enhanced` | PASS/WARN/FAIL report | <1m |
| `make test-phase1` | E2E pipeline test | 10-15m |
| `make metrics` | Generate baselines | 5m |

---

## What Gets Tested

### Determinism Validator (3 iterations per fixture)
- ✓ Finding hashes identical
- ✓ CVSS scores consistent
- ✓ Ordering stable
- ✓ Types/severities repeatable

**Status:** PASS (100%) → WARN (80-99%) → FAIL (<80%)

---

### Tool Complementarity (CodeQL + Semgrep + AST)
- Coverage: Which tools find what
- Overlap: Duplicate detections
- Accuracy: True positives vs false positives
- Redundancy: Total findings vs unique

**Goal:** Redundancy <15%, Accuracy >85%

---

### Enhanced Reporter
- 8 validation steps (proto → docker → health → static → AST → E2E → AI → metrics)
- Per-step duration and status
- Metrics: Detection rate, FP rate, CVSS accuracy, analysis time
- Recommendations: HIGH/MEDIUM/LOW priority items

**Output Formats:** Terminal (color), JSON, Markdown

---

## Success Criteria

| Metric | PASS | WARN | FAIL |
|--------|------|------|------|
| Determinism | 100% | 80-99% | <80% |
| Tool Redundancy | <15% | 15-25% | >25% |
| Detection Rate | >85% | 70-85% | <70% |
| False Positive | <10% | 10-20% | >20% |
| CVSS Accuracy | >85% | 70-85% | <70% |

---

## Report Outputs

### Terminal Report
```
✓ PASS: 7 steps
⚠ WARN: 1 step
✗ FAIL: 0 steps

Overall: ✓ PASS
```

### JSON Export
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "summary": {"total_steps": 8, "passed": 7, "warned": 1},
  "steps": [...],
  "metrics": {...}
}
```

### Markdown Export
```markdown
# Phase 1 Validation Report
## Summary
| Metric | Count |
|--------|-------|
| Total Steps | 8 |
| PASS | 7 |
```

---

## Decision Tree

```
RESULT: PASS
├─ ✓ All validation steps successful
├─ ✓ Ready for Phase 1 end-to-end testing
└─ Next: make test-phase1

RESULT: WARN
├─ ⚠ Some warnings but no failures
├─ ⚠ Phase 1 functional with caveats
└─ Next: Review remediation items, then proceed

RESULT: FAIL
├─ ✗ Critical failures detected
├─ ✗ Phase 1 not ready for production
└─ Next: Run `make logs` and troubleshoot
```

---

## Common Issues & Fixes

| Issue | Command | Fix |
|-------|---------|-----|
| CodeQL slow | `make validate` | Expected, 120s+ is normal |
| gRPC fails | `make logs` | Check .env, restart services |
| Memory issues | `docker stats` | Increase Docker resources |
| False positives | See tool report | Tune Semgrep rules |
| Inconsistent results | `make test-determinism` | Check system load |

---

## File Locations

```
📁 Enhanced Infrastructure
├─ tests/
│  ├─ determinism_validator.py       (consistency checks)
│  ├─ tool_complementarity.py        (tool analysis)
│  ├─ enhanced_reporter.py           (PASS/WARN/FAIL)
│  └─ fixtures/
│     └─ fixture_expectations.json   (expected vulnerabilities)
├─ docs/
│  ├─ VALIDATION_TESTING_GUIDE.md    (complete guide)
│  ├─ ENHANCED_INFRASTRUCTURE_SUMMARY.md
│  └─ QUICK_REFERENCE.md             (this file)
└─ Makefile                          (all commands)
```

---

## Next Steps After Validation

### If PASS ✓
1. Archive baseline metrics
2. Review Phase 2 architecture
3. Plan OS hook integration

### If WARN ⚠
1. Address HIGH priority items
2. Proceed with caution to Phase 2
3. Monitor for regressions

### If FAIL ✗
1. Run: `make logs`
2. Use decision tree to troubleshoot
3. Fix infrastructure issues
4. Retry validation

---

## Key Metrics Explained

| Metric | What it measures | Good Range |
|--------|------------------|-----------|
| Determinism | Consistency across runs | >95% |
| Redundancy | Tool overlap | <15% |
| Accuracy | True positive rate | >85% |
| False Positives | Wrong detections | <10% |
| Detection Rate | Coverage of expected vulns | >80% |
| CVSS Accuracy | Severity scoring quality | >85% |
| Analysis Time | Total duration per fixture | <10s |

---

## Export Commands

```bash
# Save JSON report
cd tests && python3 enhanced_reporter.py | grep -A 1000 "JSON EXPORT" > report.json

# Save Markdown report
cd tests && python3 enhanced_reporter.py | grep -A 1000 "MARKDOWN EXPORT" > report.md

# Save determinism results
cd tests && python3 determinism_validator.py > determinism_report.txt

# Save complementarity analysis
cd tests && python3 tool_complementarity.py > complementarity_report.txt
```

---

## Estimated Runtime

| Command | Duration |
|---------|----------|
| `make test-determinism` | 5-10 min |
| `make report-complementarity` | <1 min |
| `make report-enhanced` | <1 min |
| `make validate` (all 8 steps) | 15-20 min |
| `make test-phase1` | 10-15 min |

**Total validation time:** ~30-35 minutes

---

## Support & Troubleshooting

See `VALIDATION_TESTING_GUIDE.md` for:
- Detailed step descriptions
- Expected outputs
- Troubleshooting procedures
- Fixture explanations
- Advanced configuration

---

## Quick Copy-Paste Commands

```bash
# Setup and validate
make setup
make validate

# Full test suite
make test-phase1
make test-determinism
make metrics

# All reports
make report-determinism
make report-complementarity
make report-enhanced

# View logs
make logs

# Cleanup
make clean
```
