.PHONY: help build run test clean install-rust install-python

help:
	@echo "MCP Bug Bounty Server - Development Commands"
	@echo "==========================================="
	@echo "make install-rust       - Install Rust dependencies"
	@echo "make install-python     - Install Python dependencies"
	@echo "make build              - Build Docker images"
	@echo "make run                - Start services with docker-compose"
	@echo "make stop               - Stop running services"
	@echo "make test               - Run test suite"
	@echo "make logs               - View service logs"
	@echo "make clean              - Remove build artifacts and containers"
	@echo "make setup              - Complete development setup"

install-rust:
	cd mcp-server && cargo build

install-python:
	python3 -m venv venv
	. venv/bin/activate && pip install -r ai-service/requirements.txt

build:
	docker-compose build

run:
	docker-compose up

stop:
	docker-compose down

test:
	@echo "Running test suite..."
	cd tests && python3 -m pytest -v

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	cd mcp-server && cargo clean

setup: install-rust install-python build
	@echo "Development environment setup complete!"
	@echo "Run 'make run' to start services"
