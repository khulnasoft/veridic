"""
PyTest configuration and fixtures for Phase 1 testing.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def fixtures_path():
    """Return path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def reset_gpt_cache():
    """Reset GPT client cache between tests."""
    # Prevent exhausting API quota during testing
    pass
