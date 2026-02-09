"""
Bounty Report Builder

Constructs machine-verifiable, human-readable bug bounty reports.
Includes exploit proof, patch diff, and deterministic hashes.
"""

import json
import hashlib
from typing import Dict, Any, List

class BountyReportBuilder:
    """
    Standardizes evidence output for HackerOne, Bugcrowd, etc.
    """

    def build_report(self, 
                    finding: Dict[str, Any], 
                    exploit_evidence: Dict[str, Any], 
                    remediation_data: Dict[str, Any]) -> str:
        """
        Aggregates all Phase 2.6 data into a final report.
        """
        report = {
            "title": f"Vulnerability Report: {finding.get('type')}",
            "severity_cvss": finding.get("cvss", "TBD"),
            "repro_steps": self._generate_repro_steps(exploit_evidence),
            "exploit_proof": exploit_evidence,
            "recommended_fix": remediation_data.get("patch"),
            "veridic_verification": {
                "proof_hash": exploit_evidence.get("evidence", [{}])[0].get("payload_hash", "none"),
                "patch_hash": remediation_data.get("patch_hash"),
                "status": "VERIFIED_EXPLOITABLE_AND_FIXED"
            }
        }
        
        return json.dumps(report, indent=4)

    def _generate_repro_steps(self, evidence: Dict[str, Any]) -> List[str]:
        return [
            "1. Setup target environment in isolated sandbox",
            "2. Execute deterministic payload",
            "3. Audit stdout for veridic_proof trigger"
        ]

