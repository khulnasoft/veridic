# MCP Bug Bounty Server - Documentation Index

## Quick Navigation

### Getting Started (5-10 minutes)
1. **[QUICK_START_VALIDATION.md](QUICK_START_VALIDATION.md)** - Setup & run Phase 1 validation
   - Prerequisites
   - 2-3 minute setup
   - Full validation in 15-20 minutes
   - Troubleshooting guide

### Understanding the Project
2. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Complete overview
   - What's been built (Phase 0 + Phase 1)
   - Architecture diagram
   - File structure
   - Success criteria
   - Next steps

3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Phase 0 system design
   - Component breakdown
   - Data flow
   - Technology stack
   - Infrastructure setup

### Phase 1: Validation & Results
4. **[PHASE_1_VALIDATION_ROADMAP.md](PHASE_1_VALIDATION_ROADMAP.md)** - Detailed validation strategy
   - 8-step validation process
   - Success criteria for each step
   - Report formats (JSON, Markdown, terminal)
   - Tool attribution metrics
   - Determinism validation
   - Phase 2 transition criteria
   - Decision tree for troubleshooting

### Phase 2: Planning
5. **[PHASE_2_ARCHITECTURE.md](PHASE_2_ARCHITECTURE.md)** - Dynamic analysis design
   - Component contracts (input/output)
   - OS Insights (eBPF/DTrace/ETW)
   - Traffic Interception (mitmproxy/Rust proxy)
   - Memory Safety monitoring
   - Behavioral pattern detection
   - Implementation roadmap (4 weeks)
   - Risk mitigation strategies

### Technical Specifications
6. **[MCP_PROTOCOL.md](MCP_PROTOCOL.md)** - gRPC API specification
   - Service definitions
   - Message formats
   - Error handling
   - Examples

---

## Execution Flow

```
START
  ↓
[QUICK_START_VALIDATION.md]
  ├─ Setup environment
  ├─ Build Docker images
  └─ Run: make validate
     ↓
[PHASE_1_VALIDATION_ROADMAP.md]
  ├─ Monitor 8-step validation
  ├─ Review reports
  ├─ Analyze metrics
  └─ Decision point:
     ├─ PASS → Proceed to Phase 2
     ├─ WARN → Fix issues, re-run
     └─ FAIL → Troubleshoot (decision tree)
     ↓
[PHASE_2_ARCHITECTURE.md]
  ├─ Understand component contracts
  ├─ Plan OS insights integration
  ├─ Setup Phase 2 environment
  └─ Begin Phase 2 scaffolding
     ↓
[IMPLEMENTATION_SUMMARY.md]
  └─ Track overall progress, metrics
```

---

## Commands Cheat Sheet

### Setup & Build
```bash
make help                    # Show all available commands
make setup                   # One-time setup (Rust + Python + proto + build)
make proto                   # Generate gRPC protobuf files
make build                   # Build Docker images
```

### Validation
```bash
make validate               # Run full Phase 1 validation (all 8 steps)
make test-phase1           # Run E2E integration tests
make test-determinism      # Run consistency validation
make metrics               # Generate baseline metrics
```

### Operations
```bash
make run                    # Start services (docker-compose up)
make stop                   # Stop services
make logs                   # View service logs (follow mode)
make test                   # Run all tests
make clean                  # Remove containers, images, artifacts
```

---

## Phase 1 Validation: 8 Steps

| # | Step | Command | Success Criteria |
|---|------|---------|------------------|
| 1 | gRPC Proto Compilation | `make proto` | All `.proto` files compile |
| 2 | Docker Build | `make build` | Both images build, <2GB |
| 3 | Service Health | `make run` | Both services healthy |
| 4 | Static Analysis Tools | CLI test | CodeQL + Semgrep functional |
| 5 | AST Extraction | `pytest test_ast` | All 4 languages extract AST |
| 6 | E2E Pipeline | `make test-phase1` | ≥80% detection, <10s/fixture |
| 7 | AI Reasoning | `pytest test_ai` | CVSS accurate ±0.5 |
| 8 | Baseline Metrics | `make metrics` | Metrics generated + exported |

**Run all 8 steps**: `make validate`

---

## Key Files

### Documentation
| File | Purpose |
|------|---------|
| `QUICK_START_VALIDATION.md` | 5-minute setup guide |
| `PHASE_1_VALIDATION_ROADMAP.md` | Detailed validation strategy |
| `PHASE_2_ARCHITECTURE.md` | Component contracts for Phase 2 |
| `IMPLEMENTATION_SUMMARY.md` | Complete overview |
| `ARCHITECTURE.md` | Phase 0 system design |
| `MCP_PROTOCOL.md` | gRPC API specification |

### Core Implementation
| Path | Purpose |
|------|---------|
| `mcp-server/src/main.rs` | Rust gRPC server (4-step orchestration) |
| `mcp-server/src/ai_client.rs` | gRPC client to Python AI |
| `mcp-server/proto/` | Protobuf definitions |
| `ai-service/src/grpc_server.py` | Python gRPC server |
| `ai-service/src/static_analysis/` | CodeQL + Semgrep integration |
| `ai-service/src/ast/` | AST extractors (TS, Python, Go, Rust) |
| `ai-service/src/ai/` | AI reasoning (correlation, scoring) |

### Tests & Validation
| Path | Purpose |
|------|---------|
| `tests/run_validation.py` | Orchestrated 8-step validator |
| `tests/test_phase1_integration.py` | E2E integration tests |
| `tests/test_determinism.py` | Consistency validation |
| `tests/tool_attribution.py` | Tool effectiveness metrics |
| `tests/validation_report.py` | Report generation |
| `tests/fixtures/` | Vulnerable code samples |

### Infrastructure
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Local dev environment |
| `Makefile` | Common commands |
| `.env.example` | Environment template |
| `scripts/validate_phase1.sh` | Validation harness |
| `scripts/generate_proto.sh` | Proto generation |

---

## Report Locations

After running `make validate`:

```
tests/validation_reports/
├── validation_2024-02-10T14-32-15.json    # Structured results
├── validation_2024-02-10T14-32-15.md      # Human-readable report
└── ...
```

Also generated:
```
tests/phase1_baseline_metrics.json          # Tool attribution metrics
tests/phase1_baseline_metrics.md            # Metrics report
```

---

## Success Scenarios

### All 8 Steps PASS ✅
→ Phase 1 validation complete
→ Proceed to Phase 2 preparation
→ Review baseline metrics for tool effectiveness

### Most Steps PASS, Some WARN ⚠️
→ Investigate WARN steps
→ Fix issues (usually infrastructure-related)
→ Re-run `make validate`
→ If still WARN but stable, proceed with caution

### Any Step FAIL ❌
→ Check error in JSON report
→ Follow decision tree in PHASE_1_VALIDATION_ROADMAP.md
→ Troubleshoot specific component
→ Fix and re-run `make validate`

---

## Phase 2 Preview

Once Phase 1 passes, Phase 2 adds:
- **OS Insights**: eBPF/DTrace/ETW syscall tracing
- **Traffic Interception**: mitmproxy for HTTP analysis
- **Memory Safety**: Valgrind/ASAN integration
- **Behavioral Detection**: Race conditions, timing attacks

**Est. effort**: 2-3 weeks
**Enhanced detection rate**: 80% → 90%+

---

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| Services won't start | Check ports 50051, 8000 free; verify OPENAI_API_KEY |
| Docker build fails | Check internet, disk space, tool availability |
| Proto compilation error | Review `.proto` file syntax |
| AI service errors | Check OpenAI API key; see `make logs` |
| Tests fail | Review test output; check gRPC connectivity |
| Validation takes >1 hour | Normal for first run; CodeQL DB init is slow |

See **PHASE_1_VALIDATION_ROADMAP.md** for detailed troubleshooting.

---

## Next Action

1. Read: **QUICK_START_VALIDATION.md** (5 min)
2. Setup: `make setup` (10-15 min)
3. Validate: `make validate` (15-20 min)
4. Review: Reports in `tests/validation_reports/`
5. Decide: PASS → Phase 2 prep, WARN/FAIL → troubleshoot

---

## Project Context

**Goal**: Automated bug bounty vulnerability detection combining:
- Static analysis (CodeQL + Semgrep)
- AI reasoning (GPT-4o)
- AST analysis (all languages)
- Dynamic tracing (Phase 2: eBPF/DTrace)
- Traffic interception (Phase 2: mitmproxy)

**Status**: 
- Phase 0 ✅ Complete (foundations)
- Phase 1 ✅ Scaffolded (static analysis)
- Phase 2 📋 Planned (dynamic analysis)
- Phases 3-7 🔜 Future

**Current focus**: Validate Phase 1 → Plan Phase 2

