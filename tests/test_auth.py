"""
E2E tests for Wash Connect authentication.

test_login_success:  Prompts interactively; caches the session for all other tests.
test_login_failure:  Uses bad credentials; verifies the API returns an error.
"""
import pytest
import pytest_asyncio

pytestmark = pytest.mark.enable_socket
from conftest import save_session

from wash_connect.api import WashConnectClient, AuthError


@pytest.mark.interactive
@pytest.mark.asyncio
async def test_login_success():
    """
    Interactive: prompts for credentials, logs in, caches the session.
    Run this test first (and alone) so the session cache is populated.
    """
    print("\n--- Wash Connect Login ---")
    email = input("Email: ")
    password = input("Password: ")
    srcode = input("Site code (e.g. W001274): ")

    client = WashConnectClient()
    session = await client.login(email, password)

    assert session["user_id"], "Expected a user_id in the login response"
    assert session["token"], "Expected a token in the login response"
    assert "last_uln" in session, "Expected last_uln in the login response"

    # Also look up the ULN for the requested site code
    location = await client.get_locations(srcode)
    assert location["uln"], "Expected a uln from the location lookup"

    # Persist everything the other tests need
    save_session(
        {
            "user_id": session["user_id"],
            "token": session["token"],
            "last_uln": session["last_uln"],
            "uln": location["uln"].strip(),
            "srcode": srcode,
            "email": email,
            "account_balance": session.get("account_balance"),
        }
    )
    print(f"\nLogged in as user_id={session['user_id']}, uln={location['uln'].strip()}")


@pytest.mark.asyncio
async def test_login_failure_bad_password():
    """Wrong password should raise AuthError (not a raw HTTP or JSON error)."""
    client = WashConnectClient()
    with pytest.raises(AuthError):
        await client.login("nobody@example.com", "definitely-wrong-password")


@pytest.mark.asyncio
async def test_login_failure_empty_credentials():
    """Empty credentials should raise AuthError."""
    client = WashConnectClient()
    with pytest.raises(AuthError):
        await client.login("", "")
