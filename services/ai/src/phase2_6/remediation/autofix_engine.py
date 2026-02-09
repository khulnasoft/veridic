"""
Auto-Fix Engine

Manages the process of generating, applying, and validating patches.
Ensures fixes are deterministic and auditable.
"""

from typing import Dict, Any, List, Optional
from .patch_synthesizer import PatchSynthesizer
from .patch_validator import PatchValidator
from ..sandbox.isolated_runner import IsolatedRunner

class AutoFixEngine:
    """
    The brain of autonomous remediation.
    Links synthesis with validation.
    """

    def __init__(self, synthesizer: Optional[PatchSynthesizer] = None, validator: Optional[PatchValidator] = None):
        self.synthesizer = synthesizer or PatchSynthesizer()
        self.validator = validator or PatchValidator()

    def remediate(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for fixing a finding.
        """
        vuln_type = finding.get("type", "unknown")
        context = finding.get("context", {})
        
        # 1. Synthesize patch
        patch = self.synthesizer.synthesize_fix(vuln_type, context)
        patch_hash = self.synthesizer.get_patch_hash(patch)
        
        # 2. Validate patch (in sandbox)
        validation_result = self.validator.validate(patch, finding)
        
        return {
            "vuln_id": finding.get("id"),
            "patch": patch,
            "patch_hash": patch_hash,
            "validation": validation_result,
            "status": "APPLIED" if validation_result.get("passed") else "FAILED_VALIDATION"
        }
