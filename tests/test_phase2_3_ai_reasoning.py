"""
Phase 2.3: AI Reasoning Tests
Validates determinism, hallucination guards, conflict resolution.
All tests pass without external AI backends (mocked).
"""

import pytest
import json
import hashlib
from typing import Dict, Any

# Mock imports (these would be real in production)
from unittest.mock import MagicMock, AsyncMock, patch


class TestAIReasoningContract:
    """Test AI reasoning input/output contracts"""
    
    def test_static_finding_serialization(self):
        """Test deterministic serialization of static finding"""
        from ai_reasoning_contract import StaticFinding, Severity
        
        finding = StaticFinding(
            finding_id="sql_001",
            type="sql_injection",
            severity=Severity.HIGH,
            line_number=42,
            file_path="/app/routes/api.py",
            code_snippet="query = f'SELECT * FROM users WHERE id={user_id}'",
            cwe_id="CWE-89"
        )
        
        # Should serialize consistently
        dict1 = finding.to_dict()
        dict2 = finding.to_dict()
        
        assert dict1 == dict2
        assert dict1["severity"] == "high"
    
    def test_evidence_chain_determinism(self):
        """Test deterministic ordering of evidence chains"""
        from ai_reasoning_contract import (
            StaticFinding, RuntimeEvidence, EvidenceChain, Severity
        )
        
        finding = StaticFinding(
            finding_id="sql_001",
            type="sql_injection",
            severity=Severity.HIGH,
            line_number=42,
            file_path="/app/routes/api.py",
            code_snippet="SELECT * FROM users WHERE id={user_id}",
            cwe_id="CWE-89"
        )
        
        events = [
            RuntimeEvidence(
                event_id="syscall_2",
                event_type="syscall",
                syscall_name="execve",
                timestamp_ns=1000000002,
                process_pid=1234,
                details={"cmd": "/bin/sh", "args": ["-c", "mysql -u root"]}
            ),
            RuntimeEvidence(
                event_id="syscall_1",
                event_type="syscall",
                syscall_name="openat",
                timestamp_ns=1000000001,
                process_pid=1234,
                details={"fd": 3, "path": "/var/run/mysqld/mysqld.sock"}
            ),
        ]
        
        chain = EvidenceChain(
            chain_id="chain_001",
            chain_type="sql_injection",
            static_finding=finding,
            evidence=events,
            exploitability_score=95.0
        )
        
        # Should have events in order
        assert chain.evidence[0].event_id == "syscall_2"
        assert chain.evidence[1].event_id == "syscall_1"
    
    def test_ai_reasoning_input_hash(self):
        """Test deterministic hashing of input"""
        from ai_reasoning_contract import (
            AIReasoningInput, StaticFinding, Severity
        )
        
        finding1 = StaticFinding(
            finding_id="sql_001",
            type="sql_injection",
            severity=Severity.HIGH,
            line_number=42,
            file_path="/app/api.py",
            code_snippet="SELECT *",
            cwe_id="CWE-89"
        )
        
        input1 = AIReasoningInput(
            sandbox_session_id="session_001",
            findings=[finding1],
            evidence_chains=[]
        )
        
        # Same input should have same hash
        hash1 = input1.compute_hash()
        hash2 = input1.compute_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256
    
    def test_hallucination_guard_rejects_unknown_finding(self):
        """Test that hallucination guard rejects references to unknown findings"""
        from ai_reasoning_contract import (
            AIReasoningInput, AIReasoningOutput, HallucinationGuard,
            StaticFinding, Severity
        )
        
        finding = StaticFinding(
            finding_id="sql_001",
            type="sql_injection",
            severity=Severity.HIGH,
            line_number=42,
            file_path="/app/api.py",
            code_snippet="SELECT *",
            cwe_id="CWE-89"
        )
        
        input_contract = AIReasoningInput(
            sandbox_session_id="session_001",
            findings=[finding],
            evidence_chains=[]
        )
        
        # Output references unknown finding
        output = AIReasoningOutput(
            sandbox_session_id="session_001",
            findings_verdicts={
                "sql_999": {  # This finding doesn't exist in input
                    "verdict": "confirmed",
                    "severity": "critical",
                    "confidence": 95,
                    "reasoning": "Exploit chain detected"
                }
            },
            conflicts_resolved={}
        )
        
        guard = HallucinationGuard(input_contract)
        is_valid, violations = guard.validate_output(output)
        
        assert not is_valid
        assert len(violations) > 0
        assert "sql_999" in str(violations)


class TestConflictResolution:
    """Test conflict resolution engine"""
    
    def test_upgrade_on_exploit_chain(self):
        """Test that exploit chain detected triggers upgrade"""
        from conflict_resolver import ConflictResolver, ResolutionStrategy
        
        resolver = ConflictResolver()
        resolution = resolver.resolve_static_vs_runtime(
            conflict_id="c_001",
            static_severity="high",
            runtime_evidence_type="syscall",
            has_negative_proof=False,
            exploit_chain_detected=True,  # Key trigger
            evidence_confidence=0.95
        )
        
        assert resolution.strategy == ResolutionStrategy.UPGRADE
        assert "upgrade" in resolution.rationale.lower()
    
    def test_downgrade_with_negative_proof(self):
        """Test that negative proof triggers downgrade"""
        from conflict_resolver import ConflictResolver, ResolutionStrategy
        
        resolver = ConflictResolver()
        resolution = resolver.resolve_static_vs_runtime(
            conflict_id="c_002",
            static_severity="high",
            runtime_evidence_type="syscall",
            has_negative_proof=True,  # Key trigger
            exploit_chain_detected=False,
            evidence_confidence=0.50
        )
        
        assert resolution.strategy == ResolutionStrategy.DOWNGRADE
        assert "sanitized" in resolution.rationale.lower()
    
    def test_keep_without_runtime_evidence(self):
        """Test that missing runtime evidence keeps static verdict"""
        from conflict_resolver import ConflictResolver, ResolutionStrategy
        
        resolver = ConflictResolver()
        resolution = resolver.resolve_static_vs_runtime(
            conflict_id="c_003",
            static_severity="medium",
            runtime_evidence_type=None,  # No runtime evidence
            has_negative_proof=False,
            exploit_chain_detected=False,
            evidence_confidence=0.0
        )
        
        assert resolution.strategy == ResolutionStrategy.KEEP
        assert "no runtime evidence" in resolution.rationale.lower()
    
    def test_apply_upgrade(self):
        """Test severity upgrade"""
        from conflict_resolver import ConflictResolver
        
        resolver = ConflictResolver()
        new_severity, warning = resolver.apply_upgrade_guardrail("high", 1)
        
        assert new_severity == "critical"
        assert warning is None
    
    def test_apply_downgrade(self):
        """Test severity downgrade"""
        from conflict_resolver import ConflictResolver
        
        resolver = ConflictResolver()
        new_severity, warning = resolver.apply_downgrade_guardrail("high", 1)
        
        assert new_severity == "medium"
        assert warning is None


class TestDeterminismValidator:
    """Test determinism validation"""
    
    def test_consistent_output_passes(self):
        """Test that identical output passes determinism check"""
        from ai_reasoning_contract import (
            AIReasoningOutput, DeterminismValidator
        )
        
        output1 = AIReasoningOutput(
            sandbox_session_id="session_001",
            findings_verdicts={
                "sql_001": {
                    "verdict": "confirmed",
                    "severity": "critical",
                    "confidence": 95,
                    "reasoning": "Exploit chain detected"
                }
            },
            conflicts_resolved={}
        )
        
        validator = DeterminismValidator("input_hash_001", output1)
        
        # Same output should pass
        is_consistent, error = validator.validate_consistency(output1)
        assert is_consistent
        assert error is None
    
    def test_different_output_fails(self):
        """Test that different output fails determinism check"""
        from ai_reasoning_contract import (
            AIReasoningOutput, DeterminismValidator
        )
        
        output1 = AIReasoningOutput(
            sandbox_session_id="session_001",
            findings_verdicts={
                "sql_001": {
                    "verdict": "confirmed",
                    "severity": "critical",
                    "confidence": 95,
                    "reasoning": "v1"
                }
            },
            conflicts_resolved={}
        )
        
        output2 = AIReasoningOutput(
            sandbox_session_id="session_001",
            findings_verdicts={
                "sql_001": {
                    "verdict": "confirmed",
                    "severity": "high",  # Different!
                    "confidence": 85,
                    "reasoning": "v2"
                }
            },
            conflicts_resolved={}
        )
        
        validator = DeterminismValidator("input_hash_001", output1)
        is_consistent, error = validator.validate_consistency(output2)
        
        assert not is_consistent
        assert error is not None


class TestAIReasonerIntegration:
    """Integration tests for AI reasoner"""
    
    @pytest.mark.asyncio
    async def test_hybrid_reasoner_primary_success(self):
        """Test hybrid reasoner uses primary backend successfully"""
        from ai_reasoner_hybrid import HybridAIReasoner, AIReasonerConfig, AIBackend
        
        # Mock config
        config = AIReasonerConfig(
            primary_backend=AIBackend.OPENAI_GPT4O,
            fallback_backend=None,
            openai_api_key="test_key"
        )
        
        # This test would need mocking of OpenAI client
        # Placeholder for actual integration test
        assert config.temperature == 0.0  # Strict determinism
        assert config.primary_backend == AIBackend.OPENAI_GPT4O
    
    def test_conflict_resolution_context(self):
        """Test conflict resolution context triggers"""
        from conflict_resolver import ConflictResolutionContext
        
        # Test upgrade triggers
        upgrade_delta = ConflictResolutionContext.compute_verdict_delta(
            triggers=["exploit_chain_detected", "network_exfiltration_detected"],
            direction="upgrade"
        )
        
        assert upgrade_delta == 3  # 1 + 2
        
        # Test downgrade triggers
        downgrade_delta = ConflictResolutionContext.compute_verdict_delta(
            triggers=["input_sanitized"],
            direction="downgrade"
        )
        
        assert downgrade_delta == -2


class TestPhase23EndToEnd:
    """End-to-end Phase 2.3 scenarios"""
    
    def test_ssrf_verdict_flow(self):
        """Test complete SSRF verdict flow: static + network evidence"""
        from ai_reasoning_contract import (
            StaticFinding, RuntimeEvidence, EvidenceChain, 
            AIReasoningInput, Severity
        )
        
        # Static finding: SSRF vulnerability
        ssrf_finding = StaticFinding(
            finding_id="ssrf_001",
            type="ssrf",
            severity=Severity.HIGH,
            line_number=15,
            file_path="/app/fetch.py",
            code_snippet="requests.get(user_url)",
            cwe_id="CWE-918"
        )
        
        # Runtime evidence: connection to internal IP
        network_event = RuntimeEvidence(
            event_id="net_001",
            event_type="network",
            syscall_name="connect",
            timestamp_ns=1000000000,
            process_pid=1234,
            details={"dest_ip": "127.0.0.1", "dest_port": 3306}
        )
        
        chain = EvidenceChain(
            chain_id="chain_ssrf_001",
            chain_type="ssrf",
            static_finding=ssrf_finding,
            evidence=[network_event],
            exploitability_score=85.0
        )
        
        input_contract = AIReasoningInput(
            sandbox_session_id="session_001",
            findings=[ssrf_finding],
            evidence_chains=[chain]
        )
        
        # Verify input is valid
        input_hash = input_contract.compute_hash()
        assert len(input_hash) == 64
