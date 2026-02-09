"""
Container Profile

Defines the security and runtime parameters for a sandbox container.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ContainerProfile:
    """Security profile for ephemeral sandbox containers."""
    name: str
    image: str  # Must use sha256 digest for determinism
    read_only: bool = True
    network_enabled: bool = False
    resource_limits_id: str = "default"
    seccomp_profile: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    mounts: Optional[List[Dict[str, str]]] = None

DEFAULT_PROFILES = {
    "security_test": ContainerProfile(
        name="security_test",
        image="alpine@sha256:beef...", # Placeholder
        read_only=True,
        network_enabled=False
    ),
    "build_test": ContainerProfile(
        name="build_test",
        image="python:3.11-slim@sha256:cafe...", # Placeholder
        read_only=False,
        network_enabled=False
    )
}
