"""
Shared fixtures for Wash Connect E2E tests.

Session caching strategy:
- test_login_success (in test_auth.py) prompts interactively and writes .test_session.json
- All other tests load from cache; they are skipped if no cache exists
"""
import json
import pytest
import pytest_asyncio
import aiohttp
from pathlib import Path

SESSION_CACHE = Path(__file__).parent.parent / ".test_session.json"

BASE_URL = "https://us-central1-washmobilepay.cloudfunctions.net"


def load_session():
    """Load cached session, or return None."""
    if SESSION_CACHE.exists():
        return json.loads(SESSION_CACHE.read_text())
    return None


def save_session(data: dict):
    """Persist session to cache file."""
    SESSION_CACHE.write_text(json.dumps(data, indent=2))


@pytest.fixture(scope="session")
def cached_session():
    """
    Load the cached session written by test_login_success.
    Tests that depend on this fixture are skipped if the cache is absent.
    """
    session = load_session()
    if session is None:
        pytest.skip("No cached session — run test_auth.py::test_login_success first")
    return session


@pytest_asyncio.fixture
async def http_session():
    """A bare aiohttp session for low-level / failure-path tests."""
    async with aiohttp.ClientSession() as session:
        yield session
