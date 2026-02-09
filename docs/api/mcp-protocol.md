# MCP Protocol Specification

## Overview
The MCP (Model Code Protection) protocol defines the interface between client applications and the bug bounty analysis server. It uses Protocol Buffers for schema definition and supports gRPC as the primary transport mechanism.

## Service Definition

### MCP Service (Rust gRPC Server)

#### RPC: AnalyzeCode
Analyzes a code snippet for security vulnerabilities.

**Request**:
```protobuf
message CodeSnippet {
    string language = 1;      // "typescript", "python", "go", "rust", etc.
    string code = 2;          // Source code to analyze
    string filename = 3;      // Original filename (optional, for context)
}
```

**Response**:
```protobuf
message VulnerabilityReport {
    string code_id = 1;                          // Unique identifier for this analysis
    repeated Vulnerability vulnerabilities = 2;  // List of detected vulnerabilities
    string analysis_timestamp = 3;               // RFC3339 timestamp
    string model_used = 4;                       // Model identifier (e.g., "gpt-4o")
}

message Vulnerability {
    string id = 1;              // Unique vulnerability ID
    string type = 2;            // "sql_injection", "xss", "idor", etc.
    string severity = 3;        // "critical", "high", "medium", "low"
    string description = 4;     // Human-readable description
    int32 line_number = 5;      // Line number where vulnerability occurs (0 if unknown)
    string remediation = 6;     // Recommended fix
    float confidence = 7;       // Confidence score (0.0 - 1.0)
}
```

#### RPC: GetVulnerabilities
Streams vulnerabilities matching a query filter.

**Request**:
```protobuf
message QueryRequest {
    string filter = 1;  // Filter criteria (JSON or simple string)
    int32 limit = 2;    // Maximum number of results
}
```

**Response**: Streaming `Vulnerability` messages

#### RPC: Health
Health check endpoint.

**Request**:
```protobuf
message Empty {}
```

**Response**:
```protobuf
message HealthResponse {
    string status = 1;    // "healthy", "degraded", "unhealthy"
    string version = 2;   // Server version
}
```

---

## AI Service Interface (Python gRPC)

### AIService (Python FastAPI + gRPC Client)

#### Endpoint: POST /analyze
HTTP wrapper for code analysis.

**Request**:
```json
{
    "language": "typescript",
    "code": "function test() { eval(userInput); }",
    "filename": "test.ts"
}
```

**Response**:
```json
{
    "code_id": "code_test.ts_abc123",
    "analysis": {
        "vulnerabilities": [
            {
                "type": "eval_injection",
                "severity": "critical",
                "description": "eval() with user input...",
                "line_number": 1,
                "remediation": "Replace eval() with...",
                "confidence": 0.95
            }
        ]
    },
    "cached": false
}
```

#### Endpoint: GET /health
Service health check.

**Response**:
```json
{
    "status": "healthy",
    "version": "0.1.0"
}
```

#### Endpoint: GET /graph
Export knowledge graph.

**Response**:
```json
{
    "nodes": [
        { "id": "code_1", "node_type": "code", "language": "typescript", "filename": "test.ts" },
        { "id": "vuln_1", "node_type": "vulnerability", "vuln_type": "eval_injection", "severity": "critical" }
    ],
    "edges": [
        { "source": "code_1", "target": "vuln_1", "relation_type": "contains" }
    ]
}
```

---

## Communication Flow

### Typical Request/Response Cycle

```
Client
  ↓ gRPC Request: CodeSnippet
Rust MCP Server
  ↓ gRPC Request: CodeAnalysisRequest
Python AI Service
  ├ Load GPT-4o prompt template
  ├ Call OpenAI API
  ├ Parse response
  ├ Add to NetworkX knowledge graph
  ├ Cache embeddings
  ↓ gRPC Response: CodeAnalysisResponse
Rust MCP Server
  ├ Convert gRPC to protobuf
  ├ Add to internal cache
  ↓ gRPC Response: VulnerabilityReport
Client
```

---

## Error Handling

### gRPC Status Codes

- **OK (0)**: Success
- **CANCELLED (1)**: Request cancelled
- **UNKNOWN (2)**: Unknown error
- **INVALID_ARGUMENT (3)**: Invalid code snippet or parameters
- **DEADLINE_EXCEEDED (4)**: Analysis took too long
- **NOT_FOUND (5)**: Resource not found
- **ALREADY_EXISTS (6)**: Duplicate analysis
- **PERMISSION_DENIED (7)**: Access denied
- **RESOURCE_EXHAUSTED (8)**: Quota exceeded
- **FAILED_PRECONDITION (9)**: Service dependency unavailable
- **ABORTED (10)**: Operation aborted
- **OUT_OF_RANGE (11)**: Parameter out of range
- **UNIMPLEMENTED (12)**: RPC not implemented
- **INTERNAL (13)**: Internal server error
- **UNAVAILABLE (14)**: Service unavailable
- **DATA_LOSS (15)**: Data loss or corruption
- **UNAUTHENTICATED (16)**: Authentication failed

### Example Error Response

```protobuf
rpc_error: code = INVALID_ARGUMENT
    detail = "Language not supported: objective-c"
    metadata = {
        "service": "mcp",
        "version": "0.1.0"
    }
```

---

## Protocol Versioning

**Current Version**: 0.1.0

Version compatibility will be maintained through:
- Semantic versioning (MAJOR.MINOR.PATCH)
- Backward-compatible field additions
- Deprecation warnings for field removals
- Migration guides for breaking changes

---

## Future Enhancements

- WebSocket streaming for long-running analyses
- REST API for simple client integration
- gRPC interceptors for authentication/authorization
- Metrics collection (Prometheus format)
- Request tracing (OpenTelemetry)
