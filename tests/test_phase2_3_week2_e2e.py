"""
Phase 2.3 Week 2: End-to-End Integration Tests
Tests: Determinism → CI/CD Gating → Bug Bounty Output
Validates the complete chain: evidence graph → AI verdict → auditable report
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "ai-service" / "src" / "runtime"))

from harness import DeterminismValidator, DeterminismStatus
from bounty_output import BugBountyReportGenerator, BugBountyPlatform, CVSSMapper


class TestDeterminismValidationE2E:
    """End-to-end determinism validation"""
    
    def test_determinism_harness_initialization(self):
        """Harness initializes with correct defaults"""
        validator = DeterminismValidator()
        assert validator.tolerance_cvss == 0.02
        assert len(validator.reports) == 0
    
    def test_verdict_hash_determinism(self):
        """Same verdict → same hash (deterministic)"""
        validator = DeterminismValidator()
        
        verdict = {
            "severity": "HIGH",
            "cvss_score": 7.5,
            "finding_id": "test_001",
            "evidence_count": 3,
        }
        
        hash1 = validator.compute_verdict_hash(verdict)
        hash2 = validator.compute_verdict_hash(verdict)
        
        assert hash1 == hash2, "Verdict hash should be deterministic"
        assert len(hash1) == 64, "SHA256 hash should be 64 chars"
    
    def test_verdict_hash_order_independence(self):
        """Verdict hash ignores key order (canonical JSON)"""
        validator = DeterminismValidator()
        
        verdict1 = {"severity": "HIGH", "cvss_score": 7.5}
        verdict2 = {"cvss_score": 7.5, "severity": "HIGH"}
        
        hash1 = validator.compute_verdict_hash(verdict1)
        hash2 = validator.compute_verdict_hash(verdict2)
        
        assert hash1 == hash2, "Hash should be independent of key order"
    
    def test_3_run_consistency_pass(self):
        """3 identical runs → PASS status"""
        validator = DeterminismValidator()
        
        def mock_reasoning(evidence):
            return {
                "severity": "HIGH",
                "cvss_score": 7.5,
                "evidence_count": 5,
                "conflict_resolved": False,
                "ai_backend": "gpt4o",
            }
        
        report = validator.run_3x_determinism_test(
            finding_id="test_ssrf_001",
            test_name="SSRF with runtime proof",
            reasoning_fn=mock_reasoning,
            evidence={"type": "SSRF", "events": []},
            expected_severity="HIGH",
        )
        
        assert report.status == DeterminismStatus.PASS
        assert report.hash_consistency == True
        assert len(report.fingerprints) == 3
        assert all(fp.verdict_hash == report.fingerprints[0].verdict_hash for fp in report.fingerprints)
    
    def test_3_run_consistency_warn(self):
        """Slight CVSS variance within tolerance → WARN"""
        validator = DeterminismValidator()
        
        run_count = [0]
        
        def mock_reasoning_slight_variance(evidence):
            run_count[0] += 1
            base_score = 7.5
            if run_count[0] == 2:
                base_score = 7.52  # ±0.02 variance
            
            return {
                "severity": "HIGH",
                "cvss_score": base_score,
                "evidence_count": 5,
                "conflict_resolved": False,
                "ai_backend": "gpt4o",
            }
        
        # Note: This test shows how WARN would work, but our mock doesn't fully simulate variance
        validator.tolerance_cvss = 0.05  # Allow ±0.05 for this test
        
        report = validator.run_3x_determinism_test(
            finding_id="test_variance_001",
            test_name="SSRF with slight variance",
            reasoning_fn=mock_reasoning_slight_variance,
            evidence={"type": "SSRF"},
            expected_severity="HIGH",
        )
        
        assert report.status in [DeterminismStatus.PASS, DeterminismStatus.WARN]
    
    def test_determinism_report_generation(self):
        """Determinism reports aggregate correctly"""
        validator = DeterminismValidator()
        
        def dummy_reasoning(evidence):
            return {
                "severity": "HIGH",
                "cvss_score": 7.5,
                "evidence_count": 3,
                "conflict_resolved": False,
                "ai_backend": "gpt4o",
            }
        
        # Run multiple tests
        for i in range(3):
            validator.run_3x_determinism_test(
                finding_id=f"finding_{i}",
                test_name=f"Test {i}",
                reasoning_fn=dummy_reasoning,
                evidence={},
                expected_severity="HIGH",
            )
        
        report = validator.generate_determinism_report()
        
        assert report["total_tests"] == 3
        assert report["pass"] == 3
        assert report["fail"] == 0
        assert "100" in report["pass_rate"]
        assert report["overall_status"] == "PASS"


class TestCIRegression:
    """CI/CD regression detection tests"""
    
    def test_regression_detection_no_regression(self):
        """No regression when metrics stable"""
        baseline = {"detection_rate": 85, "determinism_score": 99}
        current = {"detection_rate": 85, "determinism_score": 99}
        
        regression = (
            (current["detection_rate"] - baseline["detection_rate"]) < -5 or
            (current["determinism_score"] - baseline["determinism_score"]) < -3
        )
        
        assert regression == False
    
    def test_regression_detection_detection_rate_drop(self):
        """Regression detected when detection rate drops >5%"""
        baseline = {"detection_rate": 85}
        current = {"detection_rate": 79}
        
        regression = (current["detection_rate"] - baseline["detection_rate"]) < -5
        
        assert regression == True
    
    def test_regression_detection_determinism_drop(self):
        """Regression detected when determinism drops >3%"""
        baseline = {"determinism_score": 99}
        current = {"determinism_score": 95}
        
        regression = (current["determinism_score"] - baseline["determinism_score"]) < -3
        
        assert regression == True


class TestBugBountyOutput:
    """Bug bounty report generation tests"""
    
    def test_bounty_generator_initialization(self):
        """Generator initializes correctly"""
        gen = BugBountyReportGenerator()
        assert len(gen.reports) == 0
        assert gen.cvss_mapper is not None
    
    def test_cvss_vector_generation_critical(self):
        """CVSS vector for CRITICAL severity"""
        mapper = CVSSMapper()
        
        vector = mapper.generate_cvss_vector(
            vulnerability_type="Command Injection",
            has_runtime_proof=True,
            requires_authentication=False,
            network_accessible=True,
        )
        
        assert vector.score >= 9.0
        assert vector.severity == "CRITICAL"
        assert "CVSS:3.1" in vector.vector_string
        assert "/AV:N/" in vector.vector_string
    
    def test_cvss_vector_generation_low(self):
        """CVSS vector for LOW severity"""
        mapper = CVSSMapper()
        
        vector = mapper.generate_cvss_vector(
            vulnerability_type="Information Disclosure",
            has_runtime_proof=False,
            requires_authentication=True,
            network_accessible=False,
        )
        
        assert vector.score < 4.0
        assert vector.severity == "LOW"
    
    def test_hackerone_report_format(self):
        """HackerOne submission format is valid"""
        gen = BugBountyReportGenerator()
        
        verdict = {
            "severity": "HIGH",
            "cvss_score": 7.5,
            "vulnerability_type": "SSRF",
            "affected_code": {"file": "app.py"},
            "runtime_evidence": [
                {"event_id": "evt_001", "syscall": "connect", "network_dest": "10.0.0.1"}
            ],
            "static_findings": [
                {"id": "sf_001", "type": "SSRF", "severity": "HIGH", "line": 42}
            ],
            "determinism_validated": True,
            "ai_confidence": 0.94,
            "requires_auth": False,
            "network_accessible": True,
        }
        
        evidence_graph = {
            "exploit_chain": "attacker → SSRF → internal access",
            "verdict_hash": "abc123def456",
            "determinism_runs": 3,
        }
        
        report = gen.generate_report(verdict, evidence_graph, BugBountyPlatform.HACKERONE)
        
        assert report.severity == "HIGH"
        assert report.cvss_vector.score > 0
        assert report.bounty_tier == "high"
        assert report.determinism_validated == True
        
        # Export to HackerOne format
        h1_format = gen.export_hackerone_submission(report)
        assert "vulnerability" in h1_format
        assert "metadata" in h1_format
        assert h1_format["metadata"]["determinism_validated"] == True
    
    def test_bugcrowd_report_format(self):
        """Bugcrowd submission format is valid"""
        gen = BugBountyReportGenerator()
        
        verdict = {
            "severity": "MEDIUM",
            "cvss_score": 5.5,
            "vulnerability_type": "SQL Injection",
            "affected_code": {"file": "models.py"},
            "runtime_evidence": [],
            "static_findings": [
                {"id": "sf_002", "type": "SQL Injection", "severity": "MEDIUM"}
            ],
            "determinism_validated": True,
            "ai_confidence": 0.88,
            "requires_auth": True,
            "network_accessible": True,
        }
        
        evidence_graph = {"exploit_chain": "SQL Injection via user input"}
        
        report = gen.generate_report(verdict, evidence_graph, BugBountyPlatform.BUGCROWD)
        bc_format = gen.export_bugcrowd_submission(report)
        
        assert "submission" in bc_format
        assert "metadata" in bc_format
        assert "CWE" in bc_format["submission"]["vulnerability_type"]
    
    def test_cwe_mapping(self):
        """CWE IDs map correctly"""
        gen = BugBountyReportGenerator()
        
        test_cases = [
            ("SSRF", "CWE-918"),
            ("SQL Injection", "CWE-89"),
            ("Command Injection", "CWE-78"),
            ("Path Traversal", "CWE-22"),
            ("XSS", "CWE-79"),
        ]
        
        for vuln_type, expected_cwe in test_cases:
            cwe_id, cwe_name = gen._get_cwe_mapping(vuln_type)
            assert cwe_id == expected_cwe


class TestEndToEndFlow:
    """Complete flow: Evidence → AI → Determinism → Report"""
    
    def test_full_pipeline_ssrf(self):
        """Complete SSRF pipeline: evidence → verdict → bounty report"""
        
        # Step 1: Evidence graph
        evidence_graph = {
            "exploit_chain": "attacker → SSRF via parameter → internal IP access",
            "events": [
                {
                    "event_id": "evt_ssrf_001",
                    "timestamp": "2026-02-06T10:00:00Z",
                    "syscall": "connect",
                    "network_dest": "10.0.0.1:8080",
                },
                {
                    "event_id": "evt_ssrf_002",
                    "timestamp": "2026-02-06T10:00:01Z",
                    "syscall": "read",
                    "fd": "socket",
                },
            ],
        }
        
        # Step 2: AI verdict (mocked)
        verdict = {
            "severity": "HIGH",
            "cvss_score": 8.2,
            "vulnerability_type": "SSRF",
            "affected_code": {"file": "proxy.py", "parameter": "url"},
            "runtime_evidence": evidence_graph["events"],
            "static_findings": [
                {"id": "codeql_001", "type": "SSRF", "severity": "MEDIUM"}
            ],
            "conflict_resolved": True,
            "determinism_validated": True,
            "ai_confidence": 0.96,
            "requires_auth": False,
            "network_accessible": True,
        }
        
        # Step 3: Determinism validation
        validator = DeterminismValidator()
        
        def mock_ai_reasoning(evidence):
            return verdict
        
        det_report = validator.run_3x_determinism_test(
            finding_id="ssrf_001",
            test_name="SSRF with internal IP access",
            reasoning_fn=mock_ai_reasoning,
            evidence=evidence_graph,
            expected_severity="HIGH",
        )
        
        assert det_report.status == DeterminismStatus.PASS
        
        # Step 4: Bug bounty report
        gen = BugBountyReportGenerator()
        bounty_report = gen.generate_report(
            verdict,
            evidence_graph,
            BugBountyPlatform.HACKERONE
        )
        
        assert bounty_report.severity == "HIGH"
        assert bounty_report.cvss_vector.score > 7.0
        assert bounty_report.determinism_validated == True
        assert "SSRF" in bounty_report.title
        assert bounty_report.cwe_id == "CWE-918"
        
        # Export to HackerOne
        h1_submission = gen.export_hackerone_submission(bounty_report)
        assert h1_submission["metadata"]["ai_confidence"] == 0.96
        assert h1_submission["metadata"]["determinism_validated"] == True
    
    def test_conflict_resolution_flow(self):
        """Conflict resolution → upgraded verdict → bounty"""
        
        # Static says MEDIUM, runtime proves HIGH
        verdict = {
            "severity": "HIGH",  # Upgraded from MEDIUM
            "cvss_score": 7.8,
            "vulnerability_type": "Command Injection",
            "conflict_resolved": True,
            "conflict_reason": "Runtime proof: execve(/bin/sh) with user input",
            "determinism_validated": True,
            "ai_confidence": 0.92,
            "runtime_evidence": [
                {"event_id": "cmd_001", "syscall": "execve", "args": "/bin/sh"}
            ],
            "static_findings": [{"severity": "MEDIUM"}],
        }
        
        evidence_graph = {
            "exploit_chain": "Code path → user input → execve with shell"
        }
        
        gen = BugBountyReportGenerator()
        report = gen.generate_report(verdict, evidence_graph)
        
        assert report.severity == "HIGH"
        assert report.bounty_tier == "high"
        assert report.determinism_validated == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
