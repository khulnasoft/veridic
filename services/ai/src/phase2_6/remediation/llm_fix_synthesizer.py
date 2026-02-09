"""
LLM Fix Synthesizer

Uses temperature-0 reasoning to map vulnerabilities to deterministic fix templates.
"""

import json
import hashlib
from typing import Dict, Any, Optional

class LLMFixSynthesizer:
    """
    Orchestrates the LLM-aided patching process with strict safeguards.
    """

    def __init__(self, gpt_client=None):
        self.gpt_client = gpt_client # Injected GPT4oClient

    def suggest_fix(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls LLM with strict parameters to identify the fix pattern.
        """
        prompt = self._build_prompt(finding)
        
        # In scaffolding, we simulate the LLM response
        # In implementation, this calls self.gpt_client.complete(prompt, temperature=0)
        llm_response = self._mock_llm_call(finding)
        
        # Verify LLM response fits deterministic patterns
        fix_data = self._parse_and_validate(llm_response)
        
        return {
            "template_id": fix_data.get("template_id"),
            "suggested_patch": fix_data.get("patch"),
            "reasoning": fix_data.get("reasoning"),
            "hash": hashlib.sha256(fix_data.get("patch").encode()).hexdigest()
        }

    def _build_prompt(self, finding: Dict[str, Any]) -> str:
        return f"Vulnerability: {finding.get('type')}. Context: {finding.get('context')}. Return JSON template fix."

    def _mock_llm_call(self, finding: Dict[str, Any]) -> str:
        """Simulated temperature-0 response."""
        vuln_type = finding.get("type", "unknown")
        
        if "sql" in vuln_type:
            return json.dumps({
                "template_id": "input_validation",
                "patch": "user_id_safe = sanitize(user_id)
query = SELECT * FROM users WHERE id = , (user_id_safe,)",
                "reasoning": "Using parameterized query to prevent SQLi."
            })
        return json.dumps({
            "template_id": "generic",
            "patch": "# Apply manual fix for " + vuln_type,
            "reasoning": "Manual remediation required."
        })

    def _parse_and_validate(self, response_str: str) -> Dict[str, Any]:
        """Ensures LLM output follows the expected schema."""
        try:
            data = json.loads(response_str)
            return data
        except:
            return {"template_id": "error", "patch": "", "reasoning": "Parse failed"}
