# Phase 1 Validation Testing Guide

Complete guide for running Phase 1 validation, determinism checks, and tool complementarity analysis.

## Overview

The Phase 1 validation infrastructure consists of three core modules:

1. **Determinism Validator** - Ensures analysis is consistent across multiple runs
2. **Tool Complementarity Analyzer** - Measures how CodeQL, Semgrep, and AST extraction work together
3. **Enhanced Reporter** - Generates PASS/WARN/FAIL reports with rich formatting

## Quick Start

```bash
# Setup (one-time)
make setup

# Run individual tests
make test-determinism          # Run 3 iterations per fixture
make report-complementarity    # Analyze tool overlap
make report-enhanced           # Generate formatted report

# Full validation (all 8 steps)
make validate

# View all test commands
make help
```

## Detailed Test Descriptions

### 1. Determinism Validation

**What it tests:** Consistency of vulnerability detection across multiple runs

**Command:**
```bash
make test-determinism
```

**Or directly:**
```bash
cd tests && python3 determinism_validator.py
```

**How it works:**
1. Takes each vulnerable fixture file
2. Analyzes it 3 times with the same configuration
3. Compares:
   - Finding hashes (exact match)
   - CVSS scores (consistency)
   - Finding order (stability)
   - Vulnerability types (pattern consistency)
   - Severity levels (accuracy consistency)

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║          PHASE 1 DETERMINISM VALIDATION REPORT             ║
╚════════════════════════════════════════════════════════════╝

Total Tests:     4
✓ PASS:          3
⚠ WARN:          1
✗ FAIL:          0

✓ vulnerable_typescript.ts
   Runs:                    3
   Hash Consistency:        Yes
   CVSS Consistency:        Yes
   Ordering Consistency:    Yes
   Type Consistency:        100.0%
   Severity Consistency:    100.0%

⚠ vulnerable_python.py
   Runs:                    3
   Hash Consistency:        No
   CVSS Consistency:        No
   Ordering Consistency:    No
   Type Consistency:        85.7%
   Severity Consistency:    85.7%
```

**Success Criteria:**
- ✓ PASS: All metrics 100% consistent (exact same findings across runs)
- ⚠ WARN: Type/severity consistency ≥80% (findings mostly consistent)
- ✗ FAIL: Consistency <80% (non-deterministic analysis)

**When it matters:**
- CI/CD reproducibility (same code = same results)
- Regression detection (changes only from actual code changes)
- Baseline comparison (Phase 2 vs Phase 1)

---

### 2. Tool Complementarity Analysis

**What it tests:** How well CodeQL, Semgrep, and AST extraction complement each other

**Command:**
```bash
make report-complementarity
```

**Or directly:**
```bash
cd tests && python3 tool_complementarity.py
```

**How it works:**
1. Collects findings from each tool
2. Normalizes to (vulnerability_type, line_number) tuples
3. Calculates:
   - **Coverage:** Which tool detects which vulnerability types
   - **Overlap:** Duplicate findings across tools
   - **Uniqueness:** Findings only one tool catches
   - **Accuracy:** True positives vs false positives
   - **Redundancy:** Total findings vs unique findings

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║      TOOL COMPLEMENTARITY & ATTRIBUTION REPORT            ║
╚════════════════════════════════════════════════════════════╝

Fixture: vulnerable_typescript.ts
Total Findings:        9
Unique Findings:       8
Overlap:               1
Redundancy Ratio:      11.1%
Effectiveness Score:   88.9%

Per-Tool Metrics:
────────────────────────────────────────────────────────────
codeql          | Findings:  3 | Accuracy: 100.0% | FP Rate:  0.0%
semgrep         | Findings:  6 | Accuracy:  83.3% | FP Rate: 16.7%

Coverage Matrix (vulnerability types per tool):
────────────────────────────────────────────────────────────
codeql         : sql_injection, unsafe_memory_access, race_condition
semgrep        : sql_injection, xss, hardcoded_credentials

Recommendations:
────────────────────────────────────────────────────────────
• MEDIUM: Consider disabling overlapping rules
• LOW: Semgrep configuration has 16.7% false positive rate
```

**Key Metrics:**

| Metric | Meaning | Good Range |
|--------|---------|-----------|
| Total Findings | Sum across all tools | - |
| Unique Findings | Finding overlap removed | - |
| Overlap | Duplicate detections | <15% |
| Redundancy Ratio | (Total - Unique) / Total | <20% |
| Effectiveness Score | 1.0 - Redundancy | >80% |
| Accuracy | True Positives / Total | >85% |
| False Positive Rate | False Positives / Total | <15% |

**When it matters:**
- Tool selection (do we need both CodeQL AND Semgrep?)
- Rule optimization (disable conflicting patterns)
- CI/CD speed (remove redundant analysis)
- Report clarity (avoid duplicate findings)

---

### 3. Enhanced PASS/WARN/FAIL Reporter

**What it tests:** Overall validation status with color-coded terminal output

**Command:**
```bash
make report-enhanced
```

**Or directly:**
```bash
cd tests && python3 enhanced_reporter.py
```

**How it works:**
1. Aggregates all validation step results
2. Colors output: ✓ GREEN (PASS), ⚠ YELLOW (WARN), ✗ RED (FAIL)
3. Exports to JSON and Markdown
4. Provides decision tree for remediation

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║          PHASE 1 VALIDATION REPORT                        ║
╚════════════════════════════════════════════════════════════╝

Overall Status: ✓ PASS

Total Steps:   8
✓ PASS:        7
⚠ WARN:        1
✗ FAIL:        0

────────────────────────────────────────────────────────────
VALIDATION STEPS:

✓ Step 1: gRPC Protocol Compilation
   Duration: 3.50s
   Proto files compiled successfully

✓ Step 2: Docker Build Verification
   Duration: 45.20s
   Both services built without errors

...

⚠ Step 4: Static Analysis Tool Validation
   Duration: 120.00s
   CodeQL compiled but slow. Semgrep found expected issues.
   → Remediation: Consider caching CodeQL databases

────────────────────────────────────────────────────────────
DECISION TREE:

✓ All Validation Steps Passed!
  ✓ Ready to proceed with Phase 1 end-to-end testing
  ✓ Run: make test-phase1
  ✓ Run: make metrics
```

**Export Formats:**

**JSON Export:**
```bash
cd tests && python3 enhanced_reporter.py | grep -A 1000 "JSON EXPORT" | tail -n +2 > validation_report.json
```

**Markdown Export:**
```bash
cd tests && python3 enhanced_reporter.py | grep -A 1000 "MARKDOWN EXPORT" | tail -n +2 > validation_report.md
```

---

## Full Validation Pipeline

**Command:**
```bash
make validate
```

Runs all 8 validation steps sequentially:

1. **gRPC Protocol Compilation** - Verify proto files compile
2. **Docker Build Verification** - Check image sizes and versions
3. **Service Health Check** - Confirm both services start
4. **Static Analysis Tool Validation** - CodeQL and Semgrep detection
5. **AST Extraction Validation** - Language-specific AST parsing
6. **End-to-End Pipeline Test** - Full Rust→Python→Report flow
7. **AI Reasoning Quality** - CVSS scoring accuracy
8. **Baseline Metrics Generation** - Store reference metrics

**Expected Runtime:** 15-20 minutes (CodeQL database compilation is slow)

**Output:** `validation_report_<timestamp>.json`

---

## Fixture Expectations

Expected vulnerabilities are defined in `tests/fixtures/fixture_expectations.json`:

```json
{
  "vulnerable_typescript.ts": {
    "expected_vulnerabilities": [
      {
        "type": "sql_injection",
        "line": 5,
        "severity": "critical",
        "cwe": "CWE-89",
        "expected_tools": ["semgrep", "codeql"]
      }
    ],
    "total_expected": 3,
    "minimum_detection_rate": 0.67
  }
}
```

**Interpretation:**
- `type`: Vulnerability class (sql_injection, xss, etc.)
- `line`: Expected line number
- `severity`: CVSS category (critical, high, medium, low)
- `cwe`: CWE identifier
- `expected_tools`: Which tools should detect this
- `minimum_detection_rate`: Acceptable detection ratio (e.g., 2/3 tools)

---

## Interpreting Results

### PASS Scenarios

✓ **All validation steps pass** - Phase 1 ready for production
- Determinism: 100% consistency
- Complementarity: <15% redundancy
- Reports: All metrics within acceptable ranges

Action: Proceed to Phase 2 planning

---

### WARN Scenarios

⚠ **Some warnings but no failures** - Phase 1 functional with caveats

**Common WARN cases:**
1. **Slow CodeQL startup** - Expected, acceptable
2. **High Semgrep false positive rate** - Tune rules before Phase 2
3. **CVSS scoring inconsistency** - Validate against real vulnerabilities
4. **Tool redundancy >20%** - Consider disabling overlapping rules

Action: Address remediation items before critical production deployment

---

### FAIL Scenarios

✗ **One or more critical failures** - Phase 1 not ready

**Common FAIL cases:**
1. **gRPC compilation fails** - Check proto syntax
2. **Docker build fails** - Verify dependencies installed
3. **Services won't start** - Check environment variables (.env)
4. **Pipeline timeout** - Increase resource limits
5. **AI service errors** - Verify OPENAI_API_KEY

Action: Run `make logs` and troubleshoot (see decision tree in report)

---

## Troubleshooting

### "CodeQL timeout (120s+)"
CodeQL databases are large and take time to compile on first run.
```bash
# Cache databases for faster iterations
export CODEQL_CACHE_DIR=/tmp/codeql_cache
make validate
```

### "gRPC connection refused"
Services not communicating.
```bash
make logs  # Check error messages
make stop && make run  # Restart services
```

### "OpenAI API errors"
Missing or invalid API key.
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Update if needed
echo "OPENAI_API_KEY=sk-..." >> .env
make run
```

### "Determinism FAIL - inconsistent findings"
Non-deterministic analysis indicates environmental issues.
```bash
# Check for system load
top  # Monitor CPU/memory

# Increase timeout
export ANALYSIS_TIMEOUT=30s
make test-determinism
```

---

## Next Steps

Once validation passes:

1. **Store baseline metrics**
   ```bash
   cp validation_report.json phase1_baseline_$(date +%s).json
   ```

2. **Proceed to Phase 2 planning**
   - Review `PHASE_2_ARCHITECTURE.md`
   - Plan OS hooks (eBPF, DTrace, ETW)
   - Set up traffic interception (mitmproxy)

3. **Run Phase 1 end-to-end tests**
   ```bash
   make test-phase1
   ```

4. **Archive validation reports**
   ```bash
   mkdir -p validation_reports
   mv validation_report*.json validation_reports/
   ```

---

## References

- `determinism_validator.py` - Implementation
- `tool_complementarity.py` - Implementation
- `enhanced_reporter.py` - Implementation
- `fixture_expectations.json` - Expected vulnerability definitions
- `run_validation.py` - Full 8-step orchestration
