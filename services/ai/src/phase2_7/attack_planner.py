"""
Attack Planner

Develops deterministic attack strategies based on existing vulnerabilities
and discovered coverage gaps.
"""

import hashlib
from typing import List, Dict, Any

class AttackPlanner:
    """
    The orchestrator of red-team attack strategies.
    Determines WHICH vulnerabilities to target and HOW.
    """

    def plan_attack(self, target_id: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Creates a prioritized list of attack vectors.
        """
        plans = []
        for finding in findings:
            strategy = self._derive_strategy(finding)
            plans.append({
                "target": target_id,
                "vector": strategy,
                "priority": finding.get("severity_score", 5.0),
                "plan_hash": hashlib.sha256(f"{target_id}:{strategy}".encode()).hexdigest()
            })
        
        # Sort by priority desc
        plans.sort(key=lambda x: x["priority"], reverse=True)
        return plans

    def _derive_strategy(self, finding: Dict[str, Any]) -> str:
        """Determines the specific attack method."""
        v_type = finding.get("type", "generic")
        return f"exploit_simulation:{v_type}_mutation"
