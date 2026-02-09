"""
Isolated Runner (Updated)

Provides a secure, sandboxed environment to execute exploit simulations
and test patches using the Docker backend.
"""

import os
from typing import Dict, Any, List, Optional
from .docker_backend.sandbox_manager import SandboxManager
from .docker_backend.container_profile import DEFAULT_PROFILES

class IsolatedRunner:
    """
    High-level runner that uses SandboxManager for isolation.
    """

    def __init__(self, use_mock: bool = True):
        backend_type = "mock" if use_mock else "docker"
        self.manager = SandboxManager(backend_type=backend_type)

    def run_exploit(self, target_id: str, payload_str: str) -> Dict[str, Any]:
        """Runs an exploit payload in the sandbox."""
        profile = DEFAULT_PROFILES.get("security_test")
        command = f"python3 exploit_payload.py"
        
        result = self.manager.run_isolated(
            profile=profile,
            command=command,
            input_data=payload_str
        )
        
        return {
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "exit_code": result.get("exit_code"),
            "evidence_hash": result.get("hash")
        }

    def test_patch(self, patch: str, test_suite: str) -> Dict[str, Any]:
        """Applies patch and runs test suite in the sandbox."""
        profile = DEFAULT_PROFILES.get("build_test")
        
        return self.manager.run_isolated(
            profile=profile,
            command=f"pytest {test_suite}",
            input_data=patch
        )
