# Phase 2: Dynamic & Runtime Analysis AI Architecture

## Overview

Phase 2 complements Phase 1 (static analysis) with runtime behavior analysis. By combining static findings with dynamic traces, we achieve "real exploitability" assessment rather than theoretical vulnerability scoring.

```
Phase 1 Output (static findings + AI reasoning)
        ↓
Phase 2 Layer (dynamic analysis):
├── OS Syscall Hooks (eBPF/DTrace/ETW)
├── Network Traffic Interception (mitmproxy / Rust proxy)
├── Memory Safety Monitoring (Valgrind patterns)
└── Behavioral Pattern Detection
        ↓
AI Correlation (static + dynamic context)
        ↓
Enhanced Report (behavior-aware exploitability + attack scenarios)
```

---

## Component Architecture

### 1. OS Insights Module

**Purpose**: Capture runtime syscalls, file I/O, network operations, and memory patterns.

#### Linux: eBPF (Extended Berkeley Packet Filter)

```
User Space:
  - Rust daemon listening for eBPF events
  - Collects syscall traces, file access logs
  - Aggregates into JSON events

Kernel Space:
  - eBPF programs attached to syscalls:
    - execve (process execution)
    - openat (file access)
    - sendto/recvfrom (network ops)
    - mmap (memory allocation)
    - copy_from_user (kernel buffer ops)
  - Minimal overhead (~1-5% CPU)
```

**Rust eBPF Wrapper** (`os_insights/ebpf.rs`):
```rust
pub struct EBPFCollector {
    syscall_log: Vec<SyscallEvent>,
    file_access_log: Vec<FileAccessEvent>,
    network_log: Vec<NetworkEvent>,
}

impl EBPFCollector {
    pub fn attach_to_process(pid: u32) -> Result<Self>;
    pub fn collect_events(duration_ms: u32) -> Result<Vec<TraceEvent>>;
    pub fn export_json() -> String;
}
```

#### macOS: DTrace

```
DTrace Scripts (in Rust via system calls):
  - Trace syscalls via dtrace probes
  - Monitor process creation, file access
  - Less overhead than eBPF but similar coverage
```

**Rust DTrace Wrapper** (`os_insights/dtrace.rs`):
```rust
pub struct DTraceCollector {
    script_path: String,
    trace_file: String,
}

impl DTraceCollector {
    pub fn compile_script(probes: &[&str]) -> Result<Self>;
    pub fn run_on_process(pid: u32, duration_ms: u32) -> Result<Vec<TraceEvent>>;
}
```

#### Windows: ETW (Event Tracing for Windows)

```
ETW Providers:
  - Microsoft-Windows-Kernel-Process (process events)
  - Microsoft-Windows-Kernel-File (file I/O)
  - Microsoft-Windows-TCPIP (network events)

Rust Consumer (via etw-rs crate):
  - Subscribe to real-time event streams
  - Parse kernel events
```

---

### 2. Traffic Interception Layer

**Purpose**: Capture and analyze HTTP/HTTPS requests/responses for injection points and sensitive data.

#### Option A: mitmproxy Integration

```
Architecture:
┌─────────────────────────────────────────┐
│  Code Under Test (Java/Python/Node)     │
└──────────────┬──────────────────────────┘
               │ HTTP/HTTPS (via proxy)
┌──────────────▼──────────────────────────┐
│  mitmproxy Server (Python)              │
│  - Intercepts requests/responses        │
│  - Records payloads, headers, cookies   │
│  - Detects: SQL injection params,       │
│    XSS vectors, file path traversal     │
└──────────────┬──────────────────────────┘
               │ JSON events
┌──────────────▼──────────────────────────┐
│  Rust Analysis Engine                   │
│  - Correlates with static findings      │
│  - Scores exploitability                │
└──────────────────────────────────────────┘
```

**Rust mitmproxy Client** (`traffic_interception/mitmproxy.rs`):
```rust
pub struct MitmproxyInterceptor {
    server_addr: String,
    port: u16,
}

impl MitmproxyInterceptor {
    pub async fn start_capture() -> Result<Self>;
    pub async fn capture_session(duration_ms: u32) -> Result<Vec<HttpEvent>>;
    pub async fn extract_injection_points() -> Vec<InjectionPoint>;
    pub async fn stop_capture();
}
```

#### Option B: Rust TCP Proxy

```
Lightweight alternative to mitmproxy for gRPC/HTTP/HTTPS passthrough:
- Raw TCP interception (no SSL decryption needed for analysis)
- Low latency (<10ms overhead)
- Suitable for black-box testing
```

**Rust TCP Proxy** (`traffic_interception/tcp_proxy.rs`):
```rust
pub struct TcpProxyListener {
    listen_port: u16,
    target_addr: String,
}

impl TcpProxyListener {
    pub async fn start() -> Result<Self>;
    pub async fn capture_traffic() -> Result<Vec<TrafficFlow>>;
}
```

---

### 3. Memory Safety Monitor

**Purpose**: Detect buffer overflows, use-after-free, and memory corruption patterns.

**Tools**:
- **Valgrind** (Linux): Detailed memory instrumentation
- **ASAN/MSAN** (Compiler): Address Sanitizer / Memory Sanitizer
- **Dr. Memory** (Windows): Dynamic memory checker

**Rust Integration** (`memory_safety/valgrind.rs`):
```rust
pub struct ValgrindMonitor {
    process_pid: u32,
    log_file: String,
}

impl ValgrindMonitor {
    pub fn run_with_valgrind(cmd: &str) -> Result<Self>;
    pub fn parse_memory_errors() -> Vec<MemoryError>;
    pub fn export_json() -> String;
}
```

---

### 4. Behavioral Pattern Detection

**Purpose**: Identify runtime anomalies (race conditions, timing attacks, logic flaws).

#### Race Condition Detection

```
Pattern:
  1. Multiple threads access shared resource without lock
  2. Time window for concurrent access > 1ms
  3. Potential data corruption

Detection via:
  - Lock contention analysis (eBPF/DTrace)
  - Thread creation/join tracing
  - Memory write ordering verification
```

#### Timing Attack Detection

```
Pattern:
  1. Execution time varies based on input (e.g., password length)
  2. Time difference > 10ms / character
  3. Potential timing oracle

Detection via:
  - Syscall latency analysis
  - Branching path analysis
  - Constant-time comparison detection
```

#### TOCTOU (Time-of-Check-Time-of-Use)

```
Pattern:
  1. File stat() at time T1
  2. File open() at time T2 (T2 > T1 + delta)
  3. File may have changed between checks

Detection via:
  - File syscall sequence analysis
  - Time delta computation
  - Vulnerability flagging for predictable file paths
```

---

## Integration with Phase 1

### Data Flow

```
Code Snippet → Phase 1 (Static Analysis + AI) → Findings[]
                                    ↓
                       Run code with Dynamic Instrumentation
                                    ↓
         Collect: OS Events, Traffic, Memory Logs
                                    ↓
         Phase 2 AI: Correlate static + dynamic findings
                                    ↓
         Enhanced Report: Behavior-aware exploitability scores
```

### AI Enhancement Module

**Rust Handler** (`ai_integration/phase2_correlation.rs`):
```rust
pub async fn correlate_findings(
    static_findings: Vec<StaticFinding>,
    dynamic_trace: DynamicTrace,
    ai_client: &mut AIServiceClient,
) -> EnhancedVulnerabilityReport {
    // 1. Filter findings relevant to observed behavior
    let relevant_findings = filter_by_trace(&static_findings, &dynamic_trace);
    
    // 2. Call AI to reason about exploitability
    let context = format_trace_context(&dynamic_trace);
    let ai_response = ai_client.enhance_with_dynamic_context(
        relevant_findings,
        context,
    ).await;
    
    // 3. Generate behavior-aware report
    enhance_report(ai_response)
}
```

---

## Component Contracts

### Input Contracts

#### Phase 1 Input
```json
{
  "code_id": "code_12345",
  "language": "python",
  "static_findings": [
    {
      "type": "sql_injection",
      "line": 42,
      "severity": "high",
      "code_context": "db.query(user_input)"
    }
  ]
}
```

#### Phase 2 Dynamic Trace Input
```json
{
  "trace_type": "ebpf|dtrace|etw",
  "events": [
    {
      "timestamp": 1640123456789,
      "syscall": "openat",
      "args": ["/etc/passwd"],
      "pid": 1234,
      "uid": 0
    }
  ],
  "traffic": [
    {
      "method": "POST",
      "path": "/api/user",
      "body": "id=1' OR '1'='1",
      "response_code": 200
    }
  ]
}
```

### Output Contract

```json
{
  "code_id": "code_12345",
  "enhanced_vulnerabilities": [
    {
      "id": "vuln_1",
      "type": "sql_injection",
      "static_severity": "high",
      "dynamic_exploitability": 0.92,
      "observed_behavior": {
        "database_query_executed": true,
        "error_message_visible": false,
        "time_based_inference": true
      },
      "attack_scenario": "Attacker can inject SQL via id parameter...",
      "cvss_score": 8.6,
      "remediation": "Use parameterized queries"
    }
  ]
}
```

---

## Implementation Roadmap

### Week 1: OS Insights
- Implement eBPF syscall collector for Linux
- Rust wrapper with event aggregation
- Test on vulnerable Python fixtures

### Week 2: Traffic Interception
- Deploy mitmproxy or Rust TCP proxy
- Capture HTTP events and injection points
- Correlate with static findings

### Week 3: Memory & Behavioral
- Integrate Valgrind/ASAN
- Implement race condition detection
- Add timing attack analysis

### Week 4: AI Correlation & Integration
- Enhance Python AI service with Phase 2 context
- Build correlation logic
- Generate final behavior-aware reports

---

## Success Criteria

- **Runtime Overhead**: <5% CPU/memory increase
- **Latency**: <100ms per event collection
- **Accuracy**: Behavioral findings match static analysis ≥80%
- **Coverage**: Detect ≥90% of OWASP top 10 at runtime
- **False Positives**: <5% of reported findings are false positives

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| eBPF complexity | Hard to debug, kernel crashes | Use established eBPF libraries (libbpf), extensive testing |
| SSL/HTTPS interception | Cannot see encrypted traffic | Use mitmproxy CA or accept plaintext HTTP for testing |
| Performance overhead | Analysis too slow | Profile frequently, optimize hot paths |
| False positives in correlation | Noise in reports | AI filtering + human review threshold |

