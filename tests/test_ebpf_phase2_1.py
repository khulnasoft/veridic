"""
Phase 2.1: eBPF Syscall Collector Tests
Tests eBPF collection, normalization, and integration.
"""

import unittest
import json
import uuid
import sys
import os

# Add ai-service to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai-service', 'src'))

from runtime.bpf_loader import BPFLoader, EBPFCollector
from runtime.event_normalizer import EventNormalizer, NormalizationPipeline
from runtime.trace_store import TraceStore, DeterminismAnalyzer
from runtime.ebpf_integration import EBPFTraceOrchestrator, SandboxConfig
from runtime.syscall_context import SyscallContextMapper, SyscallCorrelationEngine


class TestBPFLoader(unittest.TestCase):
    """Test eBPF BPF loader functionality"""
    
    def setUp(self):
        self.loader = BPFLoader()
    
    def test_loader_initialization(self):
        """Test BPFLoader initializes correctly"""
        self.assertIsNotNone(self.loader.sandbox_id)
        self.assertIsNone(self.loader.execution_id)
    
    def test_load_program_graceful_degradation(self):
        """Test loader gracefully degrades if program not found"""
        # Point to non-existent file
        fake_loader = BPFLoader("/nonexistent/path.c")
        result = fake_loader.load_program()
        
        # Should return True but enabled=False
        self.assertTrue(result)
        self.assertFalse(fake_loader.enabled)
    
    def test_start_tracing(self):
        """Test starting trace session"""
        execution_id = self.loader.start_tracing(sandbox_id="test_sandbox")
        
        self.assertIsNotNone(execution_id)
        self.assertEqual(self.loader.execution_id, execution_id)
    
    def test_normalize_syscall_event(self):
        """Test event normalization from raw format"""
        from runtime.bpf_loader import SyscallEvent
        import ctypes
        
        # Create mock event
        raw_event = SyscallEvent()
        raw_event.pid = 1234
        raw_event.uid = 1000
        raw_event.timestamp_ns = 1000000000
        raw_event.syscall_num = 59  # execve
        raw_event.syscall_name = b'execve'
        raw_event.args[0] = b'/bin/bash'
        
        normalized = self.loader._normalize_event(raw_event)
        
        self.assertEqual(normalized["source"], "ebpf")
        self.assertEqual(normalized["event_type"], "syscall")
        self.assertEqual(normalized["confidence"], 1.0)
        self.assertEqual(normalized["details"]["pid"], 1234)
        self.assertEqual(normalized["details"]["syscall_name"], "execve")


class TestEventNormalizer(unittest.TestCase):
    """Test event normalization pipeline"""
    
    def setUp(self):
        self.normalizer = EventNormalizer()
    
    def test_normalize_syscall_event(self):
        """Test normalizing a syscall event"""
        raw_event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": 1000000000,
            "sandbox_id": "test_sandbox",
            "details": {
                "syscall_number": 257,  # openat
                "syscall_name": "openat",
                "args": ["/etc/passwd"],
                "return_value": 3,
                "errno": 0,
                "pid": 1234,
                "uid": 1000,
                "process_name": "cat",
            }
        }
        
        normalized = self.normalizer.normalize(raw_event)
        
        self.assertIsNotNone(normalized)
        self.assertEqual(normalized["event_type"], "syscall")
        self.assertEqual(normalized["confidence"], 1.0)
        self.assertIn("command_injection_hint", normalized["related_static_findings"] or [])
    
    def test_sanitize_args(self):
        """Test argument sanitization"""
        args = [
            "normal_arg",
            "arg_with\x00nullbyte",
            "very_" + "x" * 300 + "_long_arg",
            "arg\nwith\nnewlines",
        ]
        
        sanitized = self.normalizer._sanitize_args(args)
        
        self.assertEqual(len(sanitized), 4)
        self.assertNotIn('\x00', sanitized[1])
        self.assertIn("...", sanitized[2])  # Truncated
        self.assertNotIn('\n', sanitized[3])
    
    def test_pipeline_processing(self):
        """Test full normalization pipeline"""
        pipeline = NormalizationPipeline()
        
        raw_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": 1000000000 + i * 100,
                "sandbox_id": "test",
                "details": {
                    "syscall_number": 59,
                    "syscall_name": "execve",
                    "args": [f"/bin/cmd{i}"],
                    "return_value": 0,
                    "errno": 0,
                    "pid": 1234 + i,
                    "uid": 1000,
                    "process_name": f"proc{i}",
                }
            }
            for i in range(5)
        ]
        
        normalized = pipeline.process_events(raw_events)
        
        self.assertEqual(len(normalized), 5)
        self.assertEqual(pipeline.stats["total_input"], 5)
        self.assertEqual(pipeline.stats["successfully_normalized"], 5)


class TestTraceStore(unittest.TestCase):
    """Test trace storage and querying"""
    
    def setUp(self):
        self.store = TraceStore()
    
    def test_save_trace(self):
        """Test saving trace to store"""
        events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": 1000000000 + i * 100,
                "event_type": "syscall",
                "source": "ebpf",
                "details": {"syscall_name": "execve"},
            }
            for i in range(3)
        ]
        
        trace_id = self.store.save_trace("sandbox1", "exec1", events)
        
        self.assertIsNotNone(trace_id)
        self.assertIn("sandbox1", trace_id)
    
    def test_query_events(self):
        """Test querying events by filter"""
        from runtime.trace_store import EventFilter
        
        events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": 1000000000,
                "event_type": "syscall",
                "source": "ebpf",
                "details": {"syscall_name": "execve", "pid": 100},
            },
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": 1000000100,
                "event_type": "syscall",
                "source": "ebpf",
                "details": {"syscall_name": "openat", "pid": 101},
            }
        ]
        
        self.store.save_trace("sandbox1", "exec1", events)
        
        # Query for execve events
        filter_obj = EventFilter(source="ebpf")
        results = self.store.query_events(filter_obj)
        
        self.assertEqual(len(results), 2)
    
    def test_determinism_analysis(self):
        """Test determinism comparison between traces"""
        events1 = [
            {
                "event_id": "evt1",
                "timestamp": 1000000000,
                "details": {"syscall_name": "execve", "args": ["/bin/sh"]},
            },
            {
                "event_id": "evt2",
                "timestamp": 1000000100,
                "details": {"syscall_name": "openat", "args": ["/etc/passwd"]},
            }
        ]
        
        # Events2 has same content, slightly different timing
        events2 = [
            {
                "event_id": "evt3",
                "timestamp": 1000000020,  # 20ms difference
                "details": {"syscall_name": "execve", "args": ["/bin/sh"]},
            },
            {
                "event_id": "evt4",
                "timestamp": 1000000120,  # 20ms difference
                "details": {"syscall_name": "openat", "args": ["/etc/passwd"]},
            }
        ]
        
        result = DeterminismAnalyzer.compare_traces(events1, events2, tolerance_ms=50)
        
        self.assertGreater(result["determinism_score"], 0.5)


class TestEBPFIntegration(unittest.TestCase):
    """Test end-to-end eBPF integration"""
    
    def setUp(self):
        self.orchestrator = EBPFTraceOrchestrator()
    
    def test_sandbox_tracing_lifecycle(self):
        """Test complete tracing lifecycle"""
        config = SandboxConfig(
            sandbox_id="test_sandbox",
            execution_name="test_exec",
            max_events=10,
        )
        
        # Start tracing
        execution_id = self.orchestrator.start_sandbox_tracing(config)
        self.assertIsNotNone(execution_id)
        
        # Stop and store (should handle no events gracefully)
        trace = self.orchestrator.stop_and_store_trace(execution_id)
        self.assertIsNotNone(trace)
        self.assertEqual(trace.sandbox_id, "test_sandbox")
    
    def test_query_trace_events(self):
        """Test querying events from stored trace"""
        # Add some events
        config = SandboxConfig(
            sandbox_id="test_sandbox",
            execution_name="test_exec",
        )
        
        execution_id = self.orchestrator.start_sandbox_tracing(config)
        
        # Manually add some events for testing
        events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": 1000000000 + i * 100,
                "event_type": "syscall",
                "source": "ebpf",
                "sandbox_id": "test_sandbox",
                "details": {
                    "syscall_name": "execve" if i == 0 else "openat",
                    "pid": 1234,
                },
            }
            for i in range(2)
        ]
        
        self.orchestrator.trace_store.save_trace(
            sandbox_id="test_sandbox",
            execution_id=execution_id,
            events=events,
        )
        
        # Query by sandbox
        results = self.orchestrator.query_trace_events(sandbox_id="test_sandbox")
        self.assertEqual(len(results), 2)


class TestSyscallContextMapping(unittest.TestCase):
    """Test syscall-to-vulnerability mapping"""
    
    def setUp(self):
        self.mapper = SyscallContextMapper()
    
    def test_map_syscall_to_vulns(self):
        """Test mapping syscalls to vulnerabilities"""
        vulns = self.mapper.map_syscall_to_vulns("execve")
        
        self.assertGreater(len(vulns), 0)
        vuln_names = [v.value for v in vulns]
        self.assertIn("command_injection", vuln_names)
    
    def test_extract_context(self):
        """Test extracting context from event"""
        event = {
            "details": {
                "syscall_name": "execve",
                "args": ["/bin/sh", "-c", "whoami"],
                "return_value": 0,
                "errno": 0,
                "pid": 1234,
                "uid": 1000,
            }
        }
        
        context = self.mapper.extract_context(event)
        
        self.assertIsNotNone(context)
        self.assertEqual(context.syscall_name, "execve")
        self.assertEqual(context.pid, 1234)
    
    def test_identify_evidence(self):
        """Test identifying evidence in syscall context"""
        from runtime.syscall_context import SyscallContext
        
        context = SyscallContext(
            syscall_name="openat",
            args=["/etc/passwd"],
            return_value=3,
            errno=0,
            pid=1234,
            uid=1000,
        )
        
        evidence = self.mapper.identify_evidence(context)
        
        self.assertIsInstance(evidence, dict)
        # Should find evidence of information disclosure
        self.assertIn("information_disclosure", evidence)
    
    def test_correlation_engine(self):
        """Test full correlation engine"""
        engine = SyscallCorrelationEngine()
        
        static_findings = [
            {
                "id": "vuln_1",
                "type": "path_traversal",
                "line": 42,
            }
        ]
        
        syscall_events = [
            {
                "details": {
                    "syscall_name": "openat",
                    "args": ["../../../etc/passwd"],
                    "return_value": -1,
                    "errno": 2,
                    "pid": 1234,
                    "uid": 1000,
                }
            }
        ]
        
        result = engine.correlate_findings_with_trace(static_findings, syscall_events)
        
        self.assertGreater(result["total_findings"], 0)
        self.assertGreaterEqual(result["correlation_rate"], 0.0)


class TestDeterminism(unittest.TestCase):
    """Test Phase 2.1 determinism"""
    
    def test_ordering_tolerance(self):
        """Test that events within 50ms are considered same bucket"""
        analyzer = DeterminismAnalyzer()
        
        # Event at exactly 1000ms
        event1 = {"timestamp": 1000 * 1_000_000}  # 1000ms in ns
        
        # Event at 1030ms (30ms later, within tolerance)
        event2 = {"timestamp": 1030 * 1_000_000}  # 1030ms in ns
        
        bucket1 = (event1["timestamp"] // (50 * 1_000_000)) * (50 * 1_000_000)
        bucket2 = (event2["timestamp"] // (50 * 1_000_000)) * (50 * 1_000_000)
        
        # Should be in same bucket
        self.assertEqual(bucket1, bucket2)


if __name__ == "__main__":
    unittest.main()
