"""
Verification suite for Phase 2.6

Tests the end-to-end integration:
Finding -> Exploit Validation -> Auto-Fix -> Patch Validation -> Report
"""

import pytest
from ..exploit.exploit_verifier import ExploitVerifier
from ..remediation.autofix_engine import AutoFixEngine
from ..reporting.bounty_report_builder import BountyReportBuilder

def test_phase2_6_lifecycle():
    """
    Superficial check of the phase logic.
    """
    # 1. Setup
    verifier = ExploitVerifier()
    fix_engine = AutoFixEngine()
    reporter = BountyReportBuilder()
    
    mock_finding = {
        "id": "FINDING-SQLI-01",
        "type": "sqli",
        "context": {"line_content": "query = 'SELECT * FROM users WHERE id = ' + user_id"}
    }
    
    # 2. Verify Exploit
    print("\n[Test] Verifying Exploit...")
    exploit_result = verifier.verify_vulnerability(
        mock_finding["id"], 
        mock_finding["type"], 
        "mock_target_db"
    )
    assert exploit_result["is_exploitable"] == True
    
    # 3. Remediation
    print("[Test] Generating Remediation...")
    remediation_result = fix_engine.remediate(mock_finding)
    assert remediation_result["status"] == "APPLIED"
    
    # 4. Reporting
    print("[Test] Building Bounty Report...")
    report = reporter.build_report(mock_finding, exploit_result, remediation_result)
    assert "repro_steps" in report
    assert "veridic_verification" in report
    print("[Test] Success!")

if __name__ == "__main__":
    test_phase2_6_lifecycle()
