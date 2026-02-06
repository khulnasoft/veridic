# MCP Bug Bounty Server - Phase 0 Foundations

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Client (Web Dashboard / VS Code Extension)             │
│                                                         │
└─────────────────────┬───────────────────────────────────┘
                      │ gRPC / WebSocket / REST
                      │
        ┌─────────────▼─────────────┐
        │  Rust MCP Server          │
        │  (Tonic + Tokio)          │
        │  - gRPC Interface         │
        │  - Proto: mcp.proto       │
        │  - Handlers               │
        │  - AI Client              │
        └─────────────┬─────────────┘
                      │ gRPC
        ┌─────────────▼─────────────┐
        │  Python AI Service        │
        │  (FastAPI + Pydantic)     │
        │  - OpenAI GPT-4o          │
        │  - NetworkX Graph         │
        │  - Prompt Templates       │
        │  - Embedding Cache        │
        └───────────────────────────┘
```

## Project Structure

```
mcp-bug-bounty/
├── mcp-server/                    # Rust gRPC Server
│   ├── Cargo.toml                # Rust dependencies
│   ├── build.rs                  # Proto compilation
│   ├── Dockerfile                # Multi-stage build
│   ├── proto/
│   │   ├── mcp.proto             # MCP service definition
│   │   └── ai_service.proto      # AI service definition
│   └── src/
│       ├── main.rs               # Server entry point
│       ├── models.rs             # Data structures
│       ├── handlers.rs           # Request handlers
│       └── ai_client.rs          # gRPC client to AI service
│
├── ai-service/                   # Python AI Service
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Docker image
│   └── src/
│       ├── main.py               # FastAPI app
│       ├── config.py             # Configuration (pydantic-settings)
│       ├── ai/
│       │   └── gpt4o.py          # GPT-4o client
│       ├── graph/
│       │   └── kg.py             # NetworkX knowledge graph
│       ├── prompts/
│       │   ├── __init__.py       # Prompt loader
│       │   ├── code_vulnerability_detection.json
│       │   ├── severity_classification.json
│       │   ├── auto_fix_suggestion.json
│       │   └── os_insights_reasoning.json
│       └── embeddings/
│           └── cache.py          # In-memory embedding cache
│
├── tests/                        # Test Suite
│   ├── fixtures/                 # Vulnerable code samples
│   │   ├── vulnerable_typescript.ts
│   │   ├── vulnerable_python.py
│   │   ├── vulnerable_go.go
│   │   └── vulnerable_rust.rs
│   ├── test_harness.py           # Fixture validation
│   └── test_integration.py       # Integration tests
│
├── docker-compose.yml            # Local development setup
├── Makefile                      # Development commands
├── .github/
│   └── workflows/
│       └── ci.yml                # CI/CD pipeline
├── .env.example                  # Environment template
└── README.md                     # Project documentation
```

## Key Components

### 1. Rust MCP Server (`mcp-server/`)
- **Framework**: Tonic (gRPC) + Tokio (async runtime)
- **Responsibilities**:
  - Exposes gRPC service for code analysis
  - Routes requests to Python AI service
  - Maintains health checks
  - Handles streaming responses
- **Proto Files**:
  - `mcp.proto`: Main MCP service (AnalyzeCode, GetVulnerabilities, Health)
  - `ai_service.proto`: AI service interface (CodeAnalysisRequest/Response)
- **Ports**: 50051 (gRPC)

### 2. Python AI Service (`ai-service/`)
- **Framework**: FastAPI + Uvicorn
- **Dependencies**:
  - OpenAI API (GPT-4o)
  - NetworkX (knowledge graph)
  - Pydantic (validation)
  - gRPC (async client)
- **Responsibilities**:
  - Analyzes code using GPT-4o
  - Manages knowledge graph of vulnerabilities
  - Caches embeddings
  - Provides REST endpoints for debugging
- **Ports**: 8000 (REST/FastAPI)

### 3. gRPC Integration (`mcp-server/src/ai_client.rs` ↔ `ai-service/`)
- Rust server connects to Python service via gRPC
- Handles connection pooling and retries
- Converts between gRPC messages and business logic
- Graceful degradation if AI service is unavailable

### 4. Test Suite (`tests/`)
- **Fixtures**: 4 vulnerable code samples (TypeScript, Python, Go, Rust)
- **Harness**: Validates detection across fixtures
- **Integration**: Tests end-to-end flow (MCP → AI Service)

### 5. Infrastructure
- **Docker Compose**: Orchestrates Rust + Python services
- **Makefile**: Local dev commands (build, run, test, clean)
- **GitHub Actions CI/CD**: Build, lint, test, integration tests on push

## Environment Variables

```env
# Required for AI Service
OPENAI_API_KEY=your-api-key-here

# Optional
AI_SERVICE_PORT=8000
AI_SERVICE_HOST=0.0.0.0
RUST_LOG=info
```

## Setup Instructions

### Quick Start (with Docker)
```bash
# Clone and setup
git clone <repo>
cd mcp-bug-bounty
cp .env.example .env
# Add OPENAI_API_KEY to .env

# Build and run
make build
make run

# In another terminal, run tests
make test
```

### Local Development (without Docker)
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Python 3.11+
python3.11 -m venv venv
source venv/bin/activate

# Build Rust server
cd mcp-server && cargo build && cd ..

# Install Python dependencies
pip install -r ai-service/requirements.txt

# Start AI service (Terminal 1)
python -m uvicorn ai-service.src.main:app --reload --port 8000

# Start Rust server (Terminal 2)
cd mcp-server && cargo run

# Run tests (Terminal 3)
python tests/test_harness.py
python tests/test_integration.py
```

## Next Steps (Phase 1+)

1. **Phase 1 - Static Analysis**: Expand code analysis patterns
2. **Phase 2 - Auth**: Add user authentication and RBAC
3. **Phase 3 - Dynamic Analysis**: Add runtime vulnerability detection
4. **Phase 4 - Multi-Modal Reasoning**: Integrate Neo4j knowledge graph
5. **Phase 5 - OS Insights**: Add OS-level security analysis
6. **Phase 6 - Auto-Fix**: Implement automated vulnerability fixing
7. **Phase 7 - Report Generation**: Create professional bug bounty reports

## References

- [Tonic gRPC Book](https://docs.rs/tonic/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [NetworkX Documentation](https://networkx.org/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
