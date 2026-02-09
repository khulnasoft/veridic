# Phase 1 Validation Quick Start

## Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ with pytest
- Rust 1.70+
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)

## Setup (2-3 minutes)

```bash
# Clone/navigate to project root
cd mcp-bug-bounty

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Generate protobuf files
make proto

# Build Docker images (10-15 minutes, one-time)
make build
```

## Run Full Validation (15-20 minutes)

```bash
# Execute all 8 validation steps with comprehensive reporting
make validate

# Output appears in:
# - Terminal (real-time)
# - tests/validation_reports/validation_<timestamp>.json
# - tests/validation_reports/validation_<timestamp>.md
```

## Interpret Results

### All Steps PASS ✅

```
OVERALL: PASS
```

Next steps:
- Review baseline metrics: `cat tests/phase1_baseline_metrics.json`
- Proceed to Phase 2 preparation
- Start Phase 2 scaffolding

### Some Steps WARN ⚠️

```
Status: WARN
```

Investigate warnings:
1. Check the specific WARN step in the report
2. Review error message
3. Manually test the component (e.g., `make test-phase1` for pipeline tests)
4. Fix issues
5. Re-run `make validate`

Common warnings:
- **Docker Build**: Timeout (increase timeout, retry)
- **Service Health**: Slow startup (normal if first run, just need patience)
- **Static Analysis**: Tool not found (install manually: `pip install semgrep`)

### Any Step FAIL ❌

```
Status: FAIL
```

Immediate action:
1. Find the FAIL step in the report
2. Check error details in the JSON report
3. Troubleshoot using the decision tree in PHASE_1_VALIDATION_ROADMAP.md

Common failures:
- **Proto Compilation**: Check `mcp-server/proto/*.proto` syntax
- **Docker Build**: Missing dependencies, check Dockerfile
- **Service Health**: Check logs with `make logs`
- **AI Service**: Verify `OPENAI_API_KEY` environment variable
- **E2E Pipeline**: Check gRPC connectivity between services

## Run Individual Steps

```bash
# Step 1: Proto compilation only
make proto

# Step 2: Docker build only
make build

# Step 3: Start services
make run
# (in another terminal)
make logs

# Step 4-8: Run integration tests
make test-phase1

# Generate baseline metrics
make metrics

# Run determinism validation
make test-determinism
```

## View Reports

After validation completes:

```bash
# View JSON report
cat tests/validation_reports/validation_*.json | jq .

# View Markdown report
cat tests/validation_reports/validation_*.md

# View terminal output (if missed)
# Re-run: make validate
```

## Analyze Tool Attribution

Tool effectiveness metrics:

```bash
cd tests
python3 -c "
from tool_attribution import ToolAttributionAnalyzer
analyzer = ToolAttributionAnalyzer()
# Load findings from validation output
report = analyzer.generate_report()

print('=== Tool Attribution Report ===')
print(f'Total Findings: {report[\"summary\"][\"total_findings\"]}')
print(f'Tools Used: {report[\"summary\"][\"tools_used\"]}')
print(f'Average Tool Agreement: {report[\"summary\"][\"average_tool_agreement\"]:.1%}')
print()
print('Complementarity (unique findings per tool):')
for tool, score in report['tools_complementarity'].items():
    print(f'  {tool}: {score:.1%}')
"
```

## Cleanup

```bash
# Stop services
make stop

# Remove containers and volumes
make clean

# Remove validation reports (if needed)
rm -rf tests/validation_reports/
```

## Next Steps After Successful Validation

1. **Review Metrics**
   - Check baseline metrics for detection rates
   - Verify tool coverage (CodeQL, Semgrep, AST)
   - Record metrics for future Phase comparison

2. **Prepare Phase 2**
   - Read PHASE_2_ARCHITECTURE.md
   - Review component contracts
   - Plan OS insights integration (eBPF/DTrace/ETW)

3. **Document Findings**
   - Note any Phase 1 limitations discovered
   - Identify patterns that benefit from dynamic analysis
   - Plan Phase 2 priorities

## Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :50051  # gRPC server
lsof -i :8000   # AI service

# Kill processes on those ports if needed
kill -9 <PID>

# Try again
make stop && make run
```

### Docker out of space
```bash
# Clean up Docker
docker system prune -a

# Retry build
make clean && make build
```

### OPENAI_API_KEY not found
```bash
# Verify environment variable
echo $OPENAI_API_KEY

# If empty, set it
export OPENAI_API_KEY="sk-..."

# Or add to .env file permanently
echo 'OPENAI_API_KEY=sk-...' >> .env

# Reload environment
source .env
```

### Proto compilation fails
```bash
# Check proto syntax
cd mcp-server
protoc --version
cargo build
```

### AI service returns errors
```bash
# Check logs
make logs

# Verify AI service is running
docker ps | grep ai-service

# Test AI endpoint manually
curl -X GET http://localhost:8000/health
```

## Performance Notes

- **First run**: 15-20 minutes (Docker build, service startup)
- **Subsequent runs**: 5-10 minutes (containers cached)
- **Per fixture analysis**: 1-3 seconds (CodeQL slower than Semgrep)
- **AI reasoning**: 2-5 seconds per finding group

## Support & Debugging

If validation fails unexpectedly:

1. Check logs: `make logs`
2. Review report JSON: `tests/validation_reports/validation_*.json`
3. Run individual components manually
4. Check documentation: `PHASE_1_VALIDATION_ROADMAP.md`
5. Review architecture: `ARCHITECTURE.md`, `MCP_PROTOCOL.md`

