"""
Phase 2.6: Autonomous Remediation & Exploit Validation

This module moves Veridic from detection to active verification and remediation.
It provides tools for exploit simulation, safe auto-fixing, patch validation,
and bounty-grade reporting.

Key Components:
- Exploit Simulation: Validate vulnerabilities with proof.
- Auto-Fix Engine: Generate safe, deterministic patches.
- Patch Validation: Verify fixes block exploits without regressions.
- Evidence Reporting: Package findings for bug bounty programs.
"""

from .exploit.exploit_verifier import ExploitVerifier
from .remediation.autofix_engine import AutoFixEngine
from .sandbox.isolated_runner import IsolatedRunner
from .reporting.bounty_report_builder import BountyReportBuilder

__all__ = [
    "ExploitVerifier",
    "AutoFixEngine",
    "IsolatedRunner",
    "BountyReportBuilder",
]

__version__ = "2.6.0"
