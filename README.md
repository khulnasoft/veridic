# MCP Bug Bounty Server

Automated vulnerability detection combining **static analysis AI** (Phase 1), **dynamic runtime analysis** (Phase 2), and **OS insights** (future phases).

## Quick Start (5 minutes)

```bash
# Clone the project
cd mcp-bug-bounty

# Setup (installs Rust, Python, builds Docker)
make setup

# Run full Phase 1 validation (15-20 min)
make validate

# View results
cat tests/validation_reports/validation_*.md
```

## What is This?

An MCP (Multi-Component Protocol) server for automated bug bounty vulnerability analysis:

1. **Phase 1: Static Analysis AI** ✅ Complete
   - CodeQL + Semgrep for pattern-based detection
   - AST extraction (TypeScript, Python, Go, Rust)
   - GPT-4o AI reasoning for correlation & severity scoring
   - Generates reports with CVSS scores & remediations

2. **Phase 2: Dynamic & Runtime Analysis** 📋 Planned
   - OS syscall tracing (eBPF/DTrace/ETW)
   - Traffic interception (mitmproxy)
   - Memory safety monitoring
   - Behavioral pattern detection

3. **Phases 3-7**: Knowledge graphs, multi-modal reasoning, automated fixes, etc.

## Architecture

```
Code Input
    ↓
[Rust MCP Server (gRPC)]
    ↓
[Python AI Service]
├─ Static Analysis (CodeQL + Semgrep)
├─ AST Extraction (Multi-language)
├─ AI Reasoning (GPT-4o correlation)
└─ Report Generation
    ↓
Vulnerability Report with CVSS Scores
```

## Commands

| Command | Purpose |
|---------|---------|
| `make help` | Show all available commands |
| `make setup` | One-time setup (everything) |
| `make validate` | Run Phase 1 validation (all 8 steps) |
| `make test-phase1` | Run integration tests |
| `make metrics` | Generate baseline metrics |
| `make run` | Start services locally |
| `make logs` | View service logs |
| `make clean` | Remove containers & artifacts |

## Validation Results

After running `make validate`, you'll see:

- **Terminal output**: Real-time validation progress
- **JSON report**: `tests/validation_reports/validation_*.json`
- **Markdown report**: `tests/validation_reports/validation_*.md`
- **Baseline metrics**: `tests/phase1_baseline_metrics.json`

### Success Criteria
- All 8 steps PASS or WARN (no FAIL)
- Detection rate ≥80% (8/10 fixtures)
- Response time <10s per fixture
- CVSS scoring within ±0.5 of expected

## Documentation

See [INDEX.md](INDEX.md) for complete documentation navigation.

**Key docs**:
- [QUICK_START_VALIDATION.md](QUICK_START_VALIDATION.md) - Setup guide
- [PHASE_1_VALIDATION_ROADMAP.md](PHASE_1_VALIDATION_ROADMAP.md) - Detailed validation strategy
- [PHASE_2_ARCHITECTURE.md](PHASE_2_ARCHITECTURE.md) - Dynamic analysis design
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Complete overview

## Requirements

- Docker & Docker Compose
- Python 3.11+
- Rust 1.70+
- OpenAI API key (for GPT-4o reasoning)

## Setup (Detailed)

```bash
# 1. Clone or navigate to project
cd mcp-bug-bounty

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...

# 4. Run full setup
make setup

# This will:
# - Install Rust dependencies
# - Create Python venv and install packages
# - Generate gRPC protobuf files
# - Build Docker images (~10-15 min)
```

## Run Validation

```bash
# Start services
make run

# In another terminal, run validation
make validate

# This runs all 8 steps:
# 1. Proto compilation
# 2. Docker build verification
# 3. Service health check
# 4. Static analysis tools (CodeQL + Semgrep)
# 5. AST extraction (TS, Python, Go, Rust)
# 6. End-to-end pipeline (all fixtures)
# 7. AI reasoning quality
# 8. Baseline metrics generation
```

## Interpret Results

### PASS ✅
All validation steps passed. Phase 1 is ready.
- Review baseline metrics
- Proceed to Phase 2 prep

### WARN ⚠️
Some warnings but overall acceptable.
- Check warning messages in report
- Investigate specific components (see decision tree)
- Re-run `make validate` after fixes

### FAIL ❌
Validation failed on one or more steps.
- Find the failed step in JSON report
- Follow troubleshooting guide (see docs)
- Fix and re-run

## Development

```bash
# Run specific tests
make test-phase1              # Integration tests
make test-determinism         # Consistency tests
make metrics                  # Baseline metrics

# View logs
make logs

# Stop services
make stop

# Clean up
make clean
```

## Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :50051  # gRPC
lsof -i :8000   # AI service

# Try again
make stop && make run
```

### Docker out of space
```bash
docker system prune -a
make clean && make build
```

### OPENAI_API_KEY not set
```bash
export OPENAI_API_KEY="sk-..."
# or add to .env permanently
echo 'OPENAI_API_KEY=sk-...' >> .env
```

See **[PHASE_1_VALIDATION_ROADMAP.md](PHASE_1_VALIDATION_ROADMAP.md)** for detailed troubleshooting.

## Project Structure

```
mcp-bug-bounty/
├── mcp-server/              # Rust gRPC server
├── ai-service/              # Python AI service
├── tests/                   # Tests & validation
├── scripts/                 # Setup & validation scripts
├── docker-compose.yml       # Local dev environment
├── Makefile                 # Common commands
├── QUICK_START_VALIDATION.md
├── PHASE_1_VALIDATION_ROADMAP.md
├── PHASE_2_ARCHITECTURE.md
├── IMPLEMENTATION_SUMMARY.md
├── INDEX.md                 # Documentation index
└── README.md               # This file
```

## Next Steps

1. **Run validation**: `make validate`
2. **Review reports**: `cat tests/validation_reports/validation_*.md`
3. **If PASS**: Proceed to Phase 2 planning
4. **If WARN/FAIL**: Follow troubleshooting guide

## Technology Stack

- **Rust**: MCP server, gRPC, infrastructure
- **Python**: AI service, static analysis, AST extraction
- **gRPC**: Inter-service communication
- **OpenAI GPT-4o**: Vulnerability reasoning
- **CodeQL**: Semantic analysis
- **Semgrep**: Pattern-based detection
- **Docker**: Containerization

## Status

- Phase 0 (Foundations) ✅ Complete
- Phase 1 (Static Analysis AI) ✅ Scaffolded, Ready for Validation
- Phase 2 (Dynamic Analysis) 📋 Planned
- Phases 3-7 🔜 Future

## Support

- Read documentation: [INDEX.md](INDEX.md)
- Check troubleshooting: [PHASE_1_VALIDATION_ROADMAP.md](PHASE_1_VALIDATION_ROADMAP.md)
- View logs: `make logs`
- Review validation report: `tests/validation_reports/`

## License

[Add your license here]

## Contact

[Add your contact info here]

---

**Ready to start?** Run `make setup && make validate` 🚀

