# Phase 1 Validation Execution Playbook

## Overview
This guide walks you through executing the Phase 1 validation pipeline end-to-end, producing determinism checks, tool attribution metrics, and final verdicts.

**Estimated Time:** 20-30 minutes (includes Docker build)  
**Prerequisites:** Rust toolchain, Python 3.11+, Docker, OPENAI_API_KEY

---

## Pre-Execution Checklist

- [ ] `.env` file created with `OPENAI_API_KEY=your_key`
- [ ] `rustup` and stable Rust toolchain installed
- [ ] Python 3.11+ available
- [ ] Docker daemon running
- [ ] `make` available in PATH
- [ ] 2GB+ free disk space (Docker images)
- [ ] 30+ minutes available (first run includes compilation)

---

## Step 1: Environment Setup (5 minutes)

```bash
# Clone/navigate to project
cd mcp-bug-bounty

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...

# Verify setup
make help | grep validate
```

**Expected Output:**
```
make validate-unified   - Run unified Phase 1 validation harness (8 steps)
make report-determinism - Generate determinism validation report
...
```

---

## Step 2: Build Infrastructure (8-10 minutes)

```bash
# Install Rust dependencies
make install-rust

# Install Python dependencies
make install-python

# Generate gRPC protobuf files
make proto

# Build Docker images
make build
```

**Troubleshooting:**
- If `cargo build` fails: Run `rustup update` and retry
- If `pip install` fails: Create new venv with `python3 -m venv venv && source venv/bin/activate`
- If Docker build fails: Ensure Docker daemon is running (`docker ps`)

---

## Step 3: Health Check (2 minutes)

```bash
# Start services in background
make run &

# Wait 10 seconds for services to initialize
sleep 10

# Check gRPC server health
grpcurl -plaintext localhost:50051 mcp.MCP/Health

# Check Python AI service
curl -s http://localhost:8000/health | python3 -m json.tool

# Stop services
make stop
```

**Expected Output:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Step 4: Run Unified Validation (15 minutes)

```bash
# Execute the full 8-step validation harness
make validate-unified
```

**What This Does:**

1. **Proto Compilation** - Verify gRPC definitions compile
2. **Docker Build Verification** - Check image sizes and dependencies
3. **Service Health** - Verify both services start and communicate
4. **Static Analysis** - Run CodeQL and Semgrep independently
5. **AST Extraction** - Test all 4 language parsers
6. **End-to-End Pipeline** - Send code through complete analysis chain
7. **Determinism Checks** - Run 3 iterations and verify consistency
8. **Final Verdict** - Generate PASS/WARN/FAIL report

**Expected Flow:**
```
[STEP 1] Protocol Compilation...
✓ PASS - Proto files compiled successfully

[STEP 2] Docker Build Verification...
⚠ WARN - Build took 95s (expected <120s)

[STEP 3] Service Health Check...
✓ PASS - Both services healthy

[STEP 4] Static Analysis Tools...
✓ PASS - CodeQL found 3 issues, Semgrep found 5 issues

...

[FINAL] VERDICT: PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Detection Rate: 85% (17/20 vulnerabilities)
Determinism: 100% (3/3 runs identical)
Tool Complementarity: 45% (CodeQL+Semgrep overlap)
AI Value Score: 78/100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommendation: Proceed to Phase 2
```

---

## Step 5: Generate Detailed Reports (5 minutes)

```bash
# Generate all reports
make report-determinism
make report-attribution
make report-verdict
make report-aggregated

# Reports are saved in tests/reports/ directory
ls -la tests/reports/
```

**Output Files:**
- `determinism_report.json` - 3-run consistency analysis
- `attribution_report.json` - Tool source attribution
- `verdict_report.json` - Final PASS/WARN/FAIL decisions
- `aggregated_metrics.json` - Combined metrics
- `aggregated_metrics.md` - Human-readable summary

---

## Step 6: Review Baseline Metrics

```bash
# View aggregated report in terminal
cat tests/reports/aggregated_metrics.md

# For JSON analysis
cat tests/reports/aggregated_metrics.json | python3 -m json.tool

# Copy baseline for Phase 2 comparison
cp tests/reports/aggregated_metrics.json \
   tests/reports/baseline_phase1_metrics.json
```

**Key Metrics to Verify:**
- **Detection Rate:** ≥80% (should catch most intentional vulnerabilities)
- **Determinism:** 100% (same results across 3 runs)
- **False Positive Rate:** <20% (too many false positives = noisy)
- **AI Confidence:** >70% (AI should be confident in findings)
- **Tool Complementarity:** 30-50% overlap (should be complementary)

---

## Step 7: Decision Tree

Based on VERDICT status, follow this tree:

```
┌─ VERDICT: PASS
│  └─ Detection Rate >85%
│     └─ Determinism 100%
│        └─ AI Confidence >75%
│           └─ ✓ Phase 1 Ready for Production
│              └─ Proceed to Phase 2 Scaffolding
│
├─ VERDICT: WARN
│  └─ Detection Rate 70-85%
│     OR Determinism 95-100%
│     OR AI Confidence 60-75%
│        └─ ⚠ Phase 1 Partially Ready
│           └─ Tune prompts / retrain models
│           └─ Rerun validation after tuning
│
└─ VERDICT: FAIL
   └─ Detection Rate <70%
      OR Determinism <95%
      OR AI Confidence <60%
         └─ ✗ Phase 1 Needs Fixes
            └─ Debug specific issues
            └─ Review error logs
            └─ Rerun validation
```

---

## Step 8: Document Results

Create a Phase 1 Validation Report:

```bash
# Generate summary report
cat > tests/reports/PHASE_1_VALIDATION_SUMMARY.md << 'EOF'
# Phase 1 Validation Summary

**Date:** $(date)
**Verdict:** [PASS/WARN/FAIL]
**Detection Rate:** X%
**Determinism:** Y%
**AI Confidence:** Z/100

## Findings

### Strengths
- [List what worked well]

### Areas for Improvement
- [List issues to address]

### Recommended Next Steps
- [List Phase 2 priorities]

## Detailed Metrics
See `aggregated_metrics.json` for complete breakdown.
EOF

# Commit to version control
git add tests/reports/
git commit -m "Phase 1 validation baseline metrics"
```

---

## Troubleshooting Guide

### Issue: "OPENAI_API_KEY not set"
```bash
# Check if .env file exists
ls -la .env

# If missing, create it
cp .env.example .env
# Then edit and add your key
```

### Issue: "Docker build timeout"
```bash
# Increase timeout
export DOCKER_BUILDKIT=1
make build
```

### Issue: "gRPC connection refused"
```bash
# Verify services started
docker-compose ps

# Check logs
docker-compose logs mcp-server
docker-compose logs ai-service

# Restart
make stop && make run
```

### Issue: "Determinism check failed"
```bash
# Check for non-deterministic elements
# Look for timestamps, random IDs, API response variance
# Review logs in tests/reports/determinism_report.json
cat tests/reports/determinism_report.json | python3 -m json.tool
```

### Issue: "Detection rate too low"
```bash
# Verify fixtures are vulnerable as expected
cat tests/fixtures/vulnerable_typescript.ts
cat tests/fixtures/vulnerable_python.py

# Check static analysis tool output
make report-attribution | grep "codeql_only\|semgrep_only"

# May need to adjust fixture expectations
vim tests/fixtures/fixture_expectations.json
```

---

## Next Steps After Validation

### If PASS:
1. Store baseline metrics: `cp tests/reports/aggregated_metrics.json tests/reports/baseline_phase1.json`
2. Begin Phase 2 scaffolding (Dynamic & Runtime Analysis)
3. Set up CI/CD integration for regression detection

### If WARN:
1. Review specific warnings in verdict_report.json
2. Adjust AI prompts if confidence is low
3. Retune thresholds if false positive rate is high
4. Rerun validation after changes

### If FAIL:
1. Review error logs: `docker-compose logs`
2. Check specific step failures in validate-unified output
3. Debug failing component (static analysis, AST, AI, gRPC)
4. Fix and rerun

---

## Example Output

See `/tests/reports/example_validation_output.txt` for complete sample output from a successful validation run.

---

## Questions?

Refer to:
- `DETERMINISM_TOOL_ATTRIBUTION_GUIDE.md` - Detailed validation methodology
- `PHASE_2_ARCHITECTURE.md` - What comes after Phase 1
- `MCP_PROTOCOL.md` - gRPC API details
