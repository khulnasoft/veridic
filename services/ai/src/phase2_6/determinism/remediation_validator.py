"""
Remediation Validator

Enforces the central rule: If inputs are the same, 
exploit proofs and patches must be identical.
"""

import hashlib
from typing import List, Dict, Any

class RemediationValidator:
    """
    Validates that remediation steps are consistent across multiple runs.
    """

    def verify_consistency(self, patch_history: List[str]) -> bool:
        """
        Fails if the patch generator produces variance for the same input.
        """
        if not patch_history:
            return True
            
        hashes = [hashlib.sha256(p.encode()).hexdigest() for p in patch_history]
        return all(h == hashes[0] for h in hashes)

    def generate_determinism_report(self, run_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes variance across multiple automated remediation attempts.
        """
        consistent = self.verify_consistency([r.get("patch", "") for r in run_results])
        return {
            "is_deterministic": consistent,
            "variance_detected": not consistent,
            "runs_evaluated": len(run_results)
        }
