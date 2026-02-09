"""
Patch Synthesizer

Generates minimal, deterministic code patches (diffs) for vulnerabilities.
Uses pattern-based templates for critical vulnerabilities (OWASP/CWE).
"""

import hashlib
import json
from typing import Dict, Any, List

class PatchSynthesizer:
    """
    Synthesizes patches for known vulnerability patterns.
    Outputs a unified diff format.
    """

    def synthesize_fix(self, vuln_type: str, context: Dict[str, Any]) -> str:
        """
        Generates a patch string based on the vulnerability type and code context.
        """
        v_type = vuln_type.lower()
        
        if "sql" in v_type:
            return self._generate_sql_fix(context)
        elif "xss" in v_type:
            return self._generate_xss_fix(context)
        elif "path" in v_type or "traversal" in v_type:
            return self._generate_path_fix(context)
        
        return "# Unrecognized vulnerability type for autopatch"

    def _generate_sql_fix(self, context: Dict[str, Any]) -> str:
        line = context.get("line_content", "")
        # Very simple replacement logic for demonstration
        if "query =" in line and "+" in line:
            return line.replace("+", ",").replace("query =", "query_params =") # Placeholder
        return "/* Suggested fix: Use parameterized queries */"

    def _generate_xss_fix(self, context: Dict[str, Any]) -> str:
        return "/* Suggested fix: Use output encoding / sanitization library */"

    def _generate_path_fix(self, context: Dict[str, Any]) -> str:
        return "/* Suggested fix: Validate path using os.path.basename() */"

    def get_patch_hash(self, patch: str) -> str:
        """Deterministic hash of the generated patch."""
        return hashlib.sha256(patch.encode()).hexdigest()
