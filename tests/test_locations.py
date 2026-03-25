"""E2E tests for the /locations endpoint."""
import pytest
from wash_connect.api import WashConnectClient, ApiError

pytestmark = pytest.mark.enable_socket


@pytest.mark.asyncio
async def test_get_locations_success(cached_session):
    """A valid srcode returns a location dict with the expected fields."""
    client = WashConnectClient()
    location = await client.get_locations(cached_session["srcode"])

    assert location["uln"], "Expected a non-empty uln"
    assert location["location_name"], "Expected a non-empty location_name"
    assert location["location_id"], "Expected a location_id"


@pytest.mark.asyncio
async def test_get_locations_uln_matches_login(cached_session):
    """ULN from /locations lookup should match what login returned."""
    client = WashConnectClient()
    location = await client.get_locations(cached_session["srcode"])

    assert location["uln"].strip() == cached_session["uln"], (
        f"ULN mismatch: locations={location['uln'].strip()!r} "
        f"vs login={cached_session['uln']!r}"
    )


@pytest.mark.asyncio
async def test_get_locations_invalid_srcode():
    """An invalid srcode should raise ApiError."""
    client = WashConnectClient()
    with pytest.raises(ApiError):
        await client.get_locations("INVALID000")
