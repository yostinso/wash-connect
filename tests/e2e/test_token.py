"""
E2E tests for POST /get_token (session / user_token renewal).

The user_token returned here is used as the Bearer token for the
www.getwashconnect.com secondary API (account/auto-refill-settings, etc.).
A device UUID is required; we use a stable fake UUID for testing — the API
only uses it as an opaque identifier per the capture.
"""
import pytest
from wash_connect.api import WashConnectClient, AuthError, ApiError

pytestmark = pytest.mark.enable_socket

# Stable fake device UUID used in all token-renewal tests
FAKE_UUID = "ffffffff00000000"


@pytest.mark.asyncio
async def test_get_user_token_success(cached_session):
    """Valid user_id + token returns a non-empty user_token string."""
    client = WashConnectClient(token=cached_session["token"])
    user_token = await client.get_user_token(
        user_id=cached_session["user_id"],
        uuid=FAKE_UUID,
    )

    assert isinstance(user_token, str) and user_token, "Expected a non-empty user_token"


@pytest.mark.asyncio
async def test_get_user_token_is_different_from_session_token(cached_session):
    """The user_token should be distinct from the session Bearer token."""
    client = WashConnectClient(token=cached_session["token"])
    user_token = await client.get_user_token(
        user_id=cached_session["user_id"],
        uuid=FAKE_UUID,
    )

    assert user_token != cached_session["token"], (
        "user_token should be a different credential from the session token"
    )


@pytest.mark.asyncio
async def test_get_user_token_unauthorized():
    """Calling get_user_token without a valid Bearer token should raise AuthError."""
    client = WashConnectClient(token="bad-token")
    with pytest.raises(AuthError):
        await client.get_user_token(user_id="595122", uuid=FAKE_UUID)


@pytest.mark.asyncio
async def test_get_user_token_bad_user_id(cached_session):
    """A mismatched user_id with a valid token should raise ApiError or AuthError."""
    client = WashConnectClient(token=cached_session["token"])
    with pytest.raises((ApiError, AuthError)):
        await client.get_user_token(user_id="000000000000", uuid=FAKE_UUID)
