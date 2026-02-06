.PHONY: help build run test clean install-rust install-python proto test-phase1 metrics validate report-determinism report-complementarity

help:
	@echo "MCP Bug Bounty Server - Development Commands"
	@echo "==========================================="
	@echo "Setup & Infrastructure:"
	@echo "  make install-rust       - Install Rust dependencies"
	@echo "  make install-python     - Install Python dependencies"
	@echo "  make proto              - Generate gRPC protobuf files"
	@echo "  make setup              - Complete development setup"
	@echo ""
	@echo "Build & Run:"
	@echo "  make build              - Build Docker images"
	@echo "  make run                - Start services with docker-compose"
	@echo "  make stop               - Stop running services"
	@echo "  make logs               - View service logs"
	@echo ""
	@echo "Testing & Validation:"
	@echo "  make test               - Run test suite"
	@echo "  make test-phase1        - Run Phase 1 integration tests"
	@echo "  make test-determinism   - Run determinism validation tests"
	@echo "  make validate           - Run full Phase 1 validation (all 8 steps)"
	@echo ""
	@echo "Reporting:"
	@echo "  make metrics            - Generate Phase 1 baseline metrics"
	@echo "  make report-determinism - Generate determinism report"
	@echo "  make report-complementarity - Generate tool complementarity report"
	@echo ""
	@echo "Other:"
	@echo "  make clean              - Remove build artifacts and containers"

install-rust:
	cd mcp-server && cargo build

install-python:
	python3 -m venv venv
	. venv/bin/activate && pip install -r ai-service/requirements.txt

proto:
	@echo "Generating gRPC protobuf files..."
	bash scripts/generate_proto.sh

build:
	docker-compose build

run:
	docker-compose up

stop:
	docker-compose down

test:
	@echo "Running test suite..."
	cd tests && python3 -m pytest -v

test-phase1:
	@echo "Running Phase 1 integration tests..."
	cd tests && python3 -m pytest test_phase1_integration.py -v

test-determinism:
	@echo "Running determinism validation tests..."
	cd tests && python3 -m pytest test_determinism.py -v

metrics:
	@echo "Generating Phase 1 baseline metrics..."
	cd tests && python3 generate_phase1_metrics.py

validate:
	@echo "Running full Phase 1 validation (all 8 steps)..."
	cd tests && python3 run_validation.py

report-determinism:
	@echo "Generating determinism validation report..."
	cd tests && python3 determinism_validator.py

report-complementarity:
	@echo "Generating tool complementarity analysis report..."
	cd tests && python3 tool_complementarity.py

report-enhanced:
	@echo "Generating enhanced PASS/WARN/FAIL report..."
	cd tests && python3 enhanced_reporter.py

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	cd mcp-server && cargo clean

setup: install-rust install-python proto build
	@echo "Development environment setup complete!"
	@echo "Run 'make run' to start services"
