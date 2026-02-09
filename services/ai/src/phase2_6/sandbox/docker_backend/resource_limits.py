"""
Resource Limits

Enforces CPU, memory, and disk constraints on sandbox execution.
"""

from dataclasses import dataclass

@dataclass
class ResourceLimits:
    """Hard constraints for sandbox containers."""
    cpu_shares: int
    memory_limit_mb: int
    pids_limit: int
    disk_limit_mb: int

STRICT_LIMITS = ResourceLimits(
    cpu_shares=128,
    memory_limit_mb=256,
    pids_limit=32,
    disk_limit_mb=50
)

MEDIUM_LIMITS = ResourceLimits(
    cpu_shares=512,
    memory_limit_mb=1024,
    pids_limit=128,
    disk_limit_mb=200
)
