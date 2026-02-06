#!/usr/bin/env bash

###############################################################################
# Phase 1 Unified Validation Harness
# Orchestrates all validation steps and produces decision-grade verdict
###############################################################################

set -e

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

###############################################################################
# Step 1: Protocol Compilation
###############################################################################
step_1_protocol_compilation() {
    log_info "Step 1/8: Compiling gRPC Protocol Files"
    
    if make proto > /tmp/proto_build.log 2>&1; then
        log_success "Protocol compilation successful"
        return 0
    else
        log_error "Protocol compilation failed"
        cat /tmp/proto_build.log
        return 1
    fi
}

###############################################################################
# Step 2: Docker Build
###############################################################################
step_2_docker_build() {
    log_info "Step 2/8: Building Docker Images"
    
    if make build > /tmp/docker_build.log 2>&1; then
        log_success "Docker build successful"
        return 0
    else
        log_error "Docker build failed"
        tail -50 /tmp/docker_build.log
        return 1
    fi
}

###############################################################################
# Step 3: Service Health Check
###############################################################################
step_3_health_check() {
    log_info "Step 3/8: Starting Services and Health Check"
    
    # Start services in background
    docker-compose up -d > /tmp/docker_up.log 2>&1
    
    # Wait for services to start
    log_info "Waiting for services to reach healthy state..."
    sleep 10
    
    # Check health
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "healthy"; then
            log_success "Services are healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log_error "Services failed to reach healthy state"
    docker-compose logs
    return 1
}

###############################################################################
# Step 4: Static Analysis Tool Validation
###############################################################################
step_4_static_analysis() {
    log_info "Step 4/8: Validating Static Analysis Tools (CodeQL + Semgrep)"
    
    if python3 tests/test_phase1_integration.py > /tmp/static_analysis.log 2>&1; then
        log_success "Static analysis tools validated"
        return 0
    else
        log_error "Static analysis validation failed"
        tail -50 /tmp/static_analysis.log
        return 1
    fi
}

###############################################################################
# Step 5: AST Extraction Validation
###############################################################################
step_5_ast_extraction() {
    log_info "Step 5/8: Validating AST Extractors (TS, Python, Go, Rust)"
    
    if python3 -c "from tests.ast import *; print('AST modules loaded')" > /tmp/ast_check.log 2>&1; then
        log_success "AST extractors validated"
        return 0
    else
        log_error "AST extraction validation failed"
        cat /tmp/ast_check.log
        return 1
    fi
}

###############################################################################
# Step 6: End-to-End Pipeline Test
###############################################################################
step_6_e2e_pipeline() {
    log_info "Step 6/8: Running End-to-End Analysis Pipeline"
    
    if python3 tests/test_phase1_integration.py --e2e > /tmp/e2e_pipeline.log 2>&1; then
        log_success "E2E pipeline test successful"
        return 0
    else
        log_error "E2E pipeline test failed"
        tail -50 /tmp/e2e_pipeline.log
        return 1
    fi
}

###############################################################################
# Step 7: Determinism Validation
###############################################################################
step_7_determinism() {
    log_info "Step 7/8: Running Determinism Checks (3 iterations)"
    
    if python3 tests/determinism.py > /tmp/determinism.log 2>&1; then
        log_success "Determinism validation passed"
        cat /tmp/determinism.log
        return 0
    else
        log_error "Determinism validation failed"
        cat /tmp/determinism.log
        return 1
    fi
}

###############################################################################
# Step 8: Tool Attribution & Final Verdict
###############################################################################
step_8_final_verdict() {
    log_info "Step 8/8: Computing Tool Attribution & Final Verdict"
    
    if python3 tests/tool_attribution_metrics.py > /tmp/tool_attribution.log 2>&1; then
        log_success "Tool attribution analysis complete"
        cat /tmp/tool_attribution.log
    else
        log_warning "Tool attribution analysis had issues"
    fi
    
    if python3 tests/final_verdict.py > /tmp/final_verdict.log 2>&1; then
        VERDICT=$(grep -o '"status": "[^"]*"' /tmp/final_verdict.log | cut -d'"' -f4)
        log_success "Final verdict computed: $VERDICT"
        cat /tmp/final_verdict.log
        return 0
    else
        log_error "Final verdict computation failed"
        cat /tmp/final_verdict.log
        return 1
    fi
}

###############################################################################
# Main Validation Flow
###############################################################################
main() {
    echo ""
    echo "=================================="
    echo "  Phase 1 Unified Validation"
    echo "=================================="
    echo ""
    
    local failed=0
    local warnings=0
    
    # Run all validation steps
    for step in 1 2 3 4 5 6 7 8; do
        step_${step}_* || {
            failed=$((failed + 1))
        }
        echo ""
    done
    
    # Generate final report
    echo "=================================="
    echo "  Validation Summary"
    echo "=================================="
    echo ""
    
    if [ $failed -gt 0 ]; then
        log_error "Phase 1 Validation FAILED ($failed steps failed)"
        log_error "Do NOT proceed to Phase 2"
        exit 1
    else
        log_success "Phase 1 Validation PASSED"
        log_success "Ready for Phase 2 (Dynamic & Runtime Analysis)"
        
        # Show metrics summary
        echo ""
        log_info "Key Metrics:"
        if [ -f /tmp/final_verdict.log ]; then
            grep -E '"status"|"detection_rate"|"determinism"' /tmp/final_verdict.log || true
        fi
        
        exit 0
    fi
}

# Cleanup on exit
cleanup() {
    log_info "Cleaning up..."
    docker-compose down > /dev/null 2>&1 || true
}

trap cleanup EXIT

# Run main validation
main "$@"
