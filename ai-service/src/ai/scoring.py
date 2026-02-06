"""
CVSS and severity scoring for vulnerabilities.
Integrates with GPT-4o for context-aware scoring.
"""

import logging
from typing import Dict, Any
from .gpt4o import GPT4oClient
from ..static_analysis.orchestrator import StaticFinding

logger = logging.getLogger(__name__)


# CWE to CVSS base score mapping
CWE_CVSS_MAP = {
    "CWE-89": 9.8,   # SQL Injection
    "CWE-79": 6.1,   # XSS
    "CWE-20": 9.8,   # Improper Input Validation
    "CWE-22": 9.1,   # Path Traversal
    "CWE-78": 9.8,   # OS Command Injection
    "CWE-502": 8.8,  # Insecure Deserialization
    "CWE-259": 7.5,  # Hardcoded Password
    "CWE-327": 9.1,  # Weak Cryptography
    "CWE-362": 5.5,  # Race Condition
    "CWE-772": 7.5,  # Missing Resource Release
}


class CVSSScorer:
    """Generate CVSS v3.1 scores for vulnerabilities."""
    
    def __init__(self, gpt_client: GPT4oClient):
        self.gpt = gpt_client
    
    async def score_finding(
        self,
        finding: StaticFinding,
        code_context: str,
    ) -> Dict[str, Any]:
        """
        Generate CVSS v3.1 score for a finding using context-aware reasoning.
        
        Args:
            finding: StaticFinding to score
            code_context: Surrounding code for context
            
        Returns:
            CVSS scoring details
        """
        logger.info(f"Scoring finding: {finding.type} at line {finding.line}")
        
        # Base score from CWE
        base_score = self._get_base_score(finding.type)
        
        # Use GPT-4o for context-aware adjustment
        try:
            adjustment = await self._get_gpt_adjustment(
                finding,
                code_context,
                base_score,
            )
        except Exception as e:
            logger.warning(f"GPT adjustment failed, using base score: {e}")
            adjustment = 0.0
        
        final_score = max(0.1, min(10.0, base_score + adjustment))
        
        return {
            "cwe": self._type_to_cwe(finding.type),
            "base_score": base_score,
            "context_adjustment": adjustment,
            "final_score": final_score,
            "severity": self._score_to_severity(final_score),
            "vector": self._generate_vector(finding, code_context),
        }
    
    async def _get_gpt_adjustment(
        self,
        finding: StaticFinding,
        code_context: str,
        base_score: float,
    ) -> float:
        """Use GPT-4o to determine CVSS score adjustment based on context."""
        prompt = f"""Given this security finding and code context, adjust the CVSS base score of {base_score}:

VULNERABILITY: {finding.type}
LINE: {finding.line}
MESSAGE: {finding.message}

CODE CONTEXT:
{code_context[:500]}

Consider:
- Is this in a high-privilege code path?
- Is user input directly used?
- Are there protective controls?
- Network accessibility?

Respond with ONLY a float between -2.0 and +2.0 representing the adjustment.
        """
        
        response = await self.gpt.call(prompt)
        
        try:
            adjustment = float(response.strip())
            return max(-2.0, min(2.0, adjustment))
        except ValueError:
            logger.warning(f"Invalid adjustment value: {response}")
            return 0.0
    
    def _get_base_score(self, vuln_type: str) -> float:
        """Get CVSS base score for vulnerability type."""
        type_map = {
            "sql_injection": 9.8,
            "xss": 6.1,
            "path_traversal": 5.3,
            "command_injection": 9.8,
            "insecure_deserialization": 8.8,
            "hardcoded_secret": 9.8,
            "weak_cryptography": 9.1,
            "race_condition": 5.5,
            "buffer_overflow": 9.8,
            "use_after_free": 8.1,
        }
        return type_map.get(vuln_type, 5.0)
    
    def _type_to_cwe(self, vuln_type: str) -> str:
        """Map vulnerability type to CWE."""
        type_cwe = {
            "sql_injection": "CWE-89",
            "xss": "CWE-79",
            "path_traversal": "CWE-22",
            "command_injection": "CWE-78",
            "insecure_deserialization": "CWE-502",
            "hardcoded_secret": "CWE-259",
            "weak_cryptography": "CWE-327",
            "race_condition": "CWE-362",
        }
        return type_cwe.get(vuln_type, "CWE-1025")
    
    def _score_to_severity(self, score: float) -> str:
        """Convert CVSS score to severity level."""
        if score >= 9.0:
            return "critical"
        elif score >= 7.0:
            return "high"
        elif score >= 4.0:
            return "medium"
        else:
            return "low"
    
    def _generate_vector(self, finding: StaticFinding, code: str) -> str:
        """Generate CVSS v3.1 vector string."""
        # Simplified vector generation
        av = "N" if self._is_network_accessible(finding, code) else "L"
        au = "N" if self._requires_auth(finding, code) else "R"
        
        return f"CVSS:3.1/AV:{av}/AT:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    
    def _is_network_accessible(self, finding: StaticFinding, code: str) -> bool:
        """Determine if vulnerability is network accessible."""
        network_keywords = ["http", "request", "api", "socket", "network", "web"]
        return any(kw in code.lower() for kw in network_keywords)
    
    def _requires_auth(self, finding: StaticFinding, code: str) -> bool:
        """Determine if vulnerability requires authentication."""
        auth_keywords = ["auth", "token", "jwt", "session", "permission", "role"]
        return any(kw in code.lower() for kw in auth_keywords)
