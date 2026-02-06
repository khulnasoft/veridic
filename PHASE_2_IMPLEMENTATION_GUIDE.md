# Phase 2.0 Implementation Guide

## Overview

Phase 2.0 scaffolding is **skeleton-first**: interface contracts and architecture defined, no premature engine coupling. This enables clean separation of concerns and parallel development.

## What's Complete (Phase 2.0 Skeleton)

### ✅ Interface Contracts
- **runtime_interface.proto** (206 lines) - gRPC service boundaries for runtime analysis
  - SandboxConfig/SandboxSession lifecycle
  - RuntimeEvent schema with confidence/collector_version/sandbox_id
  - CorrelationRequest/CorrelatedFindings
  - ConflictRequest/ResolutionVerdict

### ✅ Event Schema
- **events_schema.json** (224 lines) - Unified format for all collectors
  - SyscallEvent, NetworkEvent, FileAccessEvent, MemoryEvent
  - Confidence scoring, collector versioning, sandbox tracking
  - Determinism metadata (ordering buckets, hash)

### ✅ Sandbox Management (No Coupling)
- **sandbox.py** (150 lines) - Execution lifecycle
  - SandboxManager: start/stop/fail sessions
  - CollectorInterface: Abstract collector interface
  - No dependencies on specific collectors (eBPF, mitmproxy)

### ✅ Trace Storage (Decoupled)
- **trace_store.py** (171 lines) - Event storage and querying
  - In-memory storage (Phase 2.1: PostgreSQL backend)
  - Efficient indexing by sandbox_id and finding_id
  - DeterminismAnalyzer: ±50ms ordering tolerance

### ✅ Correlation Model (Stateless)
- **correlator.py** (219 lines) - Static-to-runtime mapping
  - CorrelationModel: Maps events to findings
  - Exploitability scoring (0-100) based on event evidence
  - No state — pure transformation logic

### ✅ Resolution Rules (With Guardrail)
- **resolution_rules.py** (220 lines) - Verdict engine
  - **APPROVED RULE**: Runtime can upgrade severity freely
  - **GUARDRAIL**: Runtime can downgrade only with negative proof
  - Examples: permission_denied, sanitized, out_of_bounds
  - Prevents false safety downgrades

### ✅ Rust gRPC Handler
- **runtime_handler.rs** (185 lines) - Protocol bridge
  - Implements RuntimeAnalysis service
  - Routes to Python backend (Phase 2.1)
  - No business logic coupling

### ✅ Phase 2 Determinism
- **phase2_determinism.py** (187 lines) - Reproducibility validation
  - Trace comparison with ±50ms tolerance
  - Correlation stability checks
  - Pass threshold: ≥95%

### ✅ CI/CD Regression Detection
- **phase2_regression_detection.yml** (255 lines) - GitHub Actions workflow
  - Validates all components
  - Compares against Phase 1 baseline
  - Auto-FAIL if detection rate drops >5%
  - Auto-WARN if determinism <90%

## Architecture (No Premature Coupling)

```
Collectors (Phase 2.1+)
├── eBPF (Linux) — FIRST
├── mitmproxy (Network) — SECOND
└── DTrace/ETW — LATER

    ↓ Independent attachment to sandbox

Sandbox + Trace Store
├── Session lifecycle management
└── Event capture and indexing

    ↓ Stateless processing

Correlation Model
├── Maps events → findings
└── Scores exploitability

    ↓

Resolution Rules Engine
├── Upgrade freely
├── Downgrade with guardrail
└── Flag for review if uncertain

    ↓ Final verdict
```

## Phase 2.1 Implementation (Next Steps)

### Week 1: eBPF Collector
- [ ] Implement eBPF program for syscall tracing
- [ ] Attach to sandbox session
- [ ] Capture file access, network, process execution
- [ ] Test on Linux fixtures

### Week 2: mitmproxy Integration
- [ ] Deploy mitmproxy proxy
- [ ] Intercept HTTP/HTTPS traffic
- [ ] Link network events to static findings
- [ ] Test SSRF, injection detection

### Week 3: Correlation + Resolution
- [ ] Wire correlator to collectors
- [ ] Test resolution rules with real events
- [ ] Validate downgrade guardrail
- [ ] Generate Phase 2 baseline

### Week 4: Polish & CI/CD
- [ ] DTrace/ETW stubs → real implementations
- [ ] Performance optimization
- [ ] Regression detection tuning
- [ ] Release Phase 2.1

## Testing Strategy

### Unit Tests (Already Passable)
```bash
cd tests
python -m pytest test_phase2_*.py -v
```

All components are testable without running collectors:
- Sandbox manager: session lifecycle
- Correlation model: static → events → scores
- Resolution rules: verdict generation
- Determinism validator: trace comparison

### Integration Tests (Phase 2.1)
- Sandbox + collector attachment
- Event capture → correlation → verdict
- Regression detection vs Phase 1 baseline

## Key Design Decisions (Locked)

1. **eBPF Priority** (not parallel)
   - Focus on single collector at a time
   - Ensures deterministic event capture
   - Easier debugging and validation

2. **Dynamic Precedence Model**
   - Runtime evidence weights equally with static
   - Upgrade freely, downgrade with negative proof
   - Prevents false safety claims

3. **±50ms Ordering Tolerance**
   - Accounts for kernel scheduling variance
   - Prevents spurious determinism failures
   - Validated in Phase 2 determinism checks

4. **Stateless Correlation**
   - All state in trace_store
   - Enables replay and auditability
   - Simplifies parallelization in Phase 2.1+

5. **GitHub Actions + SARIF**
   - Native IDE integration
   - Enterprise-friendly
   - Regression gating automated

## Success Criteria (Phase 2.0)

- ✅ All interface contracts defined and documented
- ✅ Event schema finalized with schema validation
- ✅ Sandbox lifecycle working end-to-end
- ✅ Trace storage query-able and indexed
- ✅ Correlation model producing scores
- ✅ Resolution rules with guardrail functional
- ✅ CI/CD regression detection wired
- ✅ All components unit-testable
- ✅ No premature engine coupling

## File Reference

| Component | Files | Lines |
|-----------|-------|-------|
| Contracts | runtime_interface.proto | 206 |
| Event Schema | events_schema.json | 224 |
| Sandbox | sandbox.py | 150 |
| Storage | trace_store.py | 171 |
| Correlation | correlator.py | 219 |
| Resolution | resolution_rules.py | 220 |
| Handler | runtime_handler.rs | 185 |
| Determinism | phase2_determinism.py | 187 |
| CI/CD | phase2_regression_detection.yml | 255 |
| **Total** | **9 files** | **1,817 lines** |

## Next Meeting Agenda

1. Confirm Phase 2.0 skeleton is ready for Phase 2.1
2. Prioritize eBPF vs mitmproxy (recommend eBPF first)
3. Review collector interface details
4. Plan Phase 2.1 implementation sprint
