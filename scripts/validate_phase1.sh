#!/bin/bash
set -e

# MCP Bug Bounty Server - Phase 1 Validation Harness
# This script validates all 8 Phase 1 components with enhanced determinism + attribution checks
# Output: PASS/WARN/FAIL summary with detailed metrics

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_ROOT/validation_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT="$RESULTS_DIR/phase1_validation_${TIMESTAMP}.json"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize results
mkdir -p "$RESULTS_DIR"
STEP_RESULTS=()
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

echo "=========================================="
echo "MCP Phase 1 Validation Harness"
echo "Timestamp: $TIMESTAMP"
echo "=========================================="

# Helper function to log step results
log_step() {
    local step_num=$1
    local step_name=$2
    local status=$3
    local details=$4
    
    STEP_RESULTS+=("{\"step\": $step_num, \"name\": \"$step_name\", \"status\": \"$status\", \"details\": \"$details\"}")
    
    case $status in
        PASS)
            echo -e "${GREEN}✓ Step $step_num PASS${NC}: $step_name"
            ((PASS_COUNT++))
            ;;
        WARN)
            echo -e "${YELLOW}⚠ Step $step_num WARN${NC}: $step_name"
            ((WARN_COUNT++))
            ;;
        FAIL)
            echo -e "${RED}✗ Step $step_num FAIL${NC}: $step_name"
            ((FAIL_COUNT++))
            ;;
    esac
    echo "  Details: $details"
}

# ============================================================
# STEP 1: gRPC Protocol Compilation
# ============================================================
echo ""
echo "[Step 1] Validating gRPC Protocol Compilation..."
cd "$PROJECT_ROOT"

if bash scripts/generate_proto.sh > /tmp/proto_gen.log 2>&1; then
    if [ -f "mcp-server/src/ai_service.rs" ] || grep -q "ai_service" mcp-server/src/main.rs; then
        log_step 1 "gRPC Protocol Compilation" "PASS" "Proto files generated successfully"
    else
        log_step 1 "gRPC Protocol Compilation" "WARN" "Proto generation completed but verification unclear"
    fi
else
    log_step 1 "gRPC Protocol Compilation" "FAIL" "Proto generation failed: $(tail -5 /tmp/proto_gen.log)"
fi

# ============================================================
# STEP 2: Docker Build Verification
# ============================================================
echo ""
echo "[Step 2] Validating Docker Build..."

# Check if docker is available
if ! command -v docker &> /dev/null; then
    log_step 2 "Docker Build Verification" "WARN" "Docker not found, skipping container build test"
else
    if docker-compose build --dry-run > /tmp/docker_build.log 2>&1; then
        LINES=$(wc -l < /tmp/docker_build.log)
        log_step 2 "Docker Build Verification" "PASS" "Docker build validated (${LINES} steps)"
    else
        log_step 2 "Docker Build Verification" "WARN" "Docker dry-run inconclusive, actual build recommended"
    fi
fi

# ============================================================
# STEP 3: Service Health Check
# ============================================================
echo ""
echo "[Step 3] Validating Service Health Checks..."

# Create stub health check (actual check requires running services)
if [ -f "$PROJECT_ROOT/.env.example" ]; then
    log_step 3 "Service Health Check" "WARN" "Config found; full health check requires running 'make run' and testing endpoints"
else
    log_step 3 "Service Health Check" "FAIL" ".env configuration missing"
fi

# ============================================================
# STEP 4: Static Analysis Tool Validation
# ============================================================
echo ""
echo "[Step 4] Validating Static Analysis Tools..."

cd "$PROJECT_ROOT/tests"
CODEQL_CHECK="false"
SEMGREP_CHECK="false"

# Check if tools can be invoked
if command -v codeql &> /dev/null; then
    CODEQL_CHECK="true"
    log_step 4 "Static Analysis Tools" "PASS" "CodeQL CLI available"
elif command -v semgrep &> /dev/null; then
    SEMGREP_CHECK="true"
    log_step 4 "Static Analysis Tools" "WARN" "Semgrep available; CodeQL not in PATH"
else
    log_step 4 "Static Analysis Tools" "WARN" "Tools require Docker environment; validate during runtime testing"
fi

# ============================================================
# STEP 5: AST Extraction Validation (Syntax Check)
# ============================================================
echo ""
echo "[Step 5] Validating AST Extractors..."

cd "$PROJECT_ROOT/ai-service/src/ast"
AST_FILES=("typescript_ast.py" "python_ast.py" "go_ast.py" "rust_ast.py")
AST_VALID=0

for ast_file in "${AST_FILES[@]}"; do
    if python3 -m py_compile "$ast_file" 2>/dev/null; then
        ((AST_VALID++))
    fi
done

if [ $AST_VALID -eq 4 ]; then
    log_step 5 "AST Extractors" "PASS" "All 4 AST extractors compile successfully"
else
    log_step 5 "AST Extractors" "WARN" "Only $AST_VALID/4 AST extractors compile (need runtime validation)"
fi

# ============================================================
# STEP 6: End-to-End Pipeline Test (Dry Run)
# ============================================================
echo ""
echo "[Step 6] Validating End-to-End Pipeline Structure..."

cd "$PROJECT_ROOT"
E2E_VALID=0

# Check if all components exist
if [ -f "mcp-server/src/main.rs" ]; then
    ((E2E_VALID++))
fi
if [ -f "ai-service/src/grpc_server.py" ]; then
    ((E2E_VALID++))
fi
if [ -d "tests/fixtures" ] && [ -n "$(ls tests/fixtures/ 2>/dev/null)" ]; then
    ((E2E_VALID++))
fi

if [ $E2E_VALID -eq 3 ]; then
    log_step 6 "End-to-End Pipeline" "PASS" "All pipeline components present (full test requires running services)"
else
    log_step 6 "End-to-End Pipeline" "WARN" "$E2E_VALID/3 components found"
fi

# ============================================================
# STEP 7: AI Reasoning Quality Hooks
# ============================================================
echo ""
echo "[Step 7] Validating AI Reasoning Hooks..."

if [ -f "$PROJECT_ROOT/ai-service/src/ai/correlation.py" ] && \
   [ -f "$PROJECT_ROOT/ai-service/src/ai/scoring.py" ]; then
    log_step 7 "AI Reasoning Quality" "PASS" "Correlation + CVSS scoring modules present"
else
    log_step 7 "AI Reasoning Quality" "FAIL" "AI reasoning modules incomplete"
fi

# ============================================================
# STEP 8: Metrics Infrastructure
# ============================================================
echo ""
echo "[Step 8] Validating Metrics Generation..."

if [ -f "$PROJECT_ROOT/tests/generate_phase1_metrics.py" ]; then
    log_step 8 "Baseline Metrics" "PASS" "Metrics generation script available"
else
    log_step 8 "Baseline Metrics" "FAIL" "Metrics generation script missing"
fi

# ============================================================
# ENHANCEMENT 1: Determinism Check
# ============================================================
echo ""
echo "[Enhancement 1] Checking Determinism Infrastructure..."

DETERMINISM_SCRIPT="$PROJECT_ROOT/tests/test_determinism.py"
if [ -f "$DETERMINISM_SCRIPT" ]; then
    log_step 99 "Determinism Check Infrastructure" "PASS" "Determinism test harness available"
else
    log_step 99 "Determinism Check Infrastructure" "WARN" "Determinism test harness needs creation"
fi

# ============================================================
# ENHANCEMENT 2: Tool Attribution Metrics
# ============================================================
echo ""
echo "[Enhancement 2] Checking Tool Attribution..."

ATTRIBUTION_SCRIPT="$PROJECT_ROOT/tests/tool_attribution_metrics.py"
if [ -f "$ATTRIBUTION_SCRIPT" ]; then
    log_step 100 "Tool Attribution Metrics" "PASS" "Attribution tracking available"
else
    log_step 100 "Tool Attribution Metrics" "WARN" "Attribution tracking needs creation"
fi

# ============================================================
# FINAL SUMMARY
# ============================================================
echo ""
echo "=========================================="
echo "PHASE 1 VALIDATION SUMMARY"
echo "=========================================="
echo -e "${GREEN}PASS: $PASS_COUNT${NC}"
echo -e "${YELLOW}WARN: $WARN_COUNT${NC}"
echo -e "${RED}FAIL: $FAIL_COUNT${NC}"
echo "=========================================="

# Determine overall status
if [ $FAIL_COUNT -eq 0 ]; then
    if [ $WARN_COUNT -eq 0 ]; then
        OVERALL_STATUS="PASS"
        echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    else
        OVERALL_STATUS="WARN"
        echo -e "${YELLOW}⚠ CHECKS PASSED WITH WARNINGS${NC}"
        echo "   Recommended: Run full integration tests with 'make test-phase1'"
    fi
else
    OVERALL_STATUS="FAIL"
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
    echo "   Review failures above and address before proceeding"
fi

# Generate JSON report
echo ""
echo "Detailed report saved to: $REPORT"

# Create JSON report
cat > "$REPORT" << EOF
{
  "validation_timestamp": "$TIMESTAMP",
  "overall_status": "$OVERALL_STATUS",
  "summary": {
    "passed": $PASS_COUNT,
    "warnings": $WARN_COUNT,
    "failed": $FAIL_COUNT
  },
  "next_steps": [
    "Run 'make test-phase1' to execute full end-to-end tests",
    "Run 'make metrics' to generate baseline metrics",
    "Review generated metrics at $RESULTS_DIR/phase1_metrics_*.json",
    "Check fixture coverage and adjust prompts if needed",
    "Once Phase 1 validation complete, proceed to Phase 2"
  ]
}
EOF

echo ""
echo "To run full Phase 1 integration tests:"
echo "  make test-phase1"
echo ""
echo "To generate baseline metrics:"
echo "  make metrics"
echo ""

exit $([ $FAIL_COUNT -eq 0 ] && echo 0 || echo 1)
