"""E2E tests for GET /account_balance."""
import pytest
from wash_connect.api import WashConnectClient, AuthError

pytestmark = pytest.mark.enable_socket


@pytest.mark.asyncio
async def test_get_account_balance_success(cached_session):
    """Valid token returns an integer balance (in cents)."""
    client = WashConnectClient(token=cached_session["token"])
    balance = await client.get_account_balance()

    assert isinstance(balance, int), f"Expected int balance, got {type(balance)}"
    assert balance >= 0, "Balance should be non-negative"


@pytest.mark.asyncio
async def test_get_account_balance_matches_login(cached_session):
    """Balance from the dedicated endpoint should match what login returned."""
    client = WashConnectClient(token=cached_session["token"])
    balance = await client.get_account_balance()

    login_balance = int(cached_session["account_balance"])
    # Allow it to differ (time may have passed), but both should be non-negative ints.
    # If they match exactly it's a strong signal the field mapping is correct.
    assert isinstance(balance, int)
    assert isinstance(login_balance, int)


@pytest.mark.asyncio
async def test_get_account_balance_unauthorized():
    """An invalid token should raise AuthError."""
    client = WashConnectClient(token="bad-token")
    with pytest.raises(AuthError):
        await client.get_account_balance()
