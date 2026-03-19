"""Pytest configuration and fixtures."""

import asyncio
import sys
from pathlib import Path

import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def vcr_config():
    """Configure VCR for recording HTTP interactions."""
    return {
        "filter_headers": ["authorization", "auth"],
        "record_mode": "none",
    }
