"""E2E tests for GET /get_machine_status_v1."""
import pytest
from wash_connect.api import WashConnectClient

pytestmark = pytest.mark.enable_socket

EXPECTED_MACHINE_FIELDS = {"machine_number", "bt_name", "status", "type", "time_remaining", "start_time"}
VALID_STATUSES = {"available", "in_use", "out_of_service"}
VALID_TYPES = {"washer", "dryer"}


@pytest.mark.asyncio
async def test_get_machine_status_success(cached_session):
    """Valid token + uln returns a non-empty floors dict."""
    client = WashConnectClient(token=cached_session["token"])
    floors = await client.get_machine_status(cached_session["uln"])

    assert floors, "Expected at least one floor"


@pytest.mark.asyncio
async def test_get_machine_status_floor_names(cached_session):
    """Every floor must have a non-empty string name."""
    client = WashConnectClient(token=cached_session["token"])
    floors = await client.get_machine_status(cached_session["uln"])

    for floor_id, floor in floors.items():
        assert isinstance(floor["name"], str) and floor["name"], (
            f"Floor {floor_id!r} has a missing or non-string name"
        )


@pytest.mark.asyncio
async def test_get_machine_status_machine_fields(cached_session):
    """Every machine must have the expected fields with valid values."""
    client = WashConnectClient(token=cached_session["token"])
    floors = await client.get_machine_status(cached_session["uln"])

    for floor_id, floor in floors.items():
        for machine in floor["machines"]:
            missing = EXPECTED_MACHINE_FIELDS - machine.keys()
            assert not missing, (
                f"Floor {floor_id!r} machine {machine.get('machine_number')!r} "
                f"is missing fields: {missing}"
            )
            assert machine["type"] in VALID_TYPES, (
                f"Unexpected machine type: {machine['type']!r}"
            )
            assert machine["status"] in VALID_STATUSES, (
                f"Unexpected machine status: {machine['status']!r}"
            )


@pytest.mark.asyncio
async def test_get_machine_status_has_washers_and_dryers(cached_session):
    """The location should have at least one washer and one dryer."""
    client = WashConnectClient(token=cached_session["token"])
    floors = await client.get_machine_status(cached_session["uln"])

    all_machines = [m for f in floors.values() for m in f["machines"]]
    types = {m["type"] for m in all_machines}
    assert "washer" in types, "Expected at least one washer"
    assert "dryer" in types, "Expected at least one dryer"


@pytest.mark.asyncio
async def test_get_machine_status_public_with_bad_token():
    """Machine status is a public endpoint — succeeds even with a bad token."""
    client = WashConnectClient(token="invalid-token")
    floors = await client.get_machine_status("CA7527907")
    assert floors, "Expected floors even with a bad token (public endpoint)"


@pytest.mark.asyncio
async def test_get_machine_status_public_without_token():
    """Machine status is a public endpoint — succeeds with no token at all."""
    client = WashConnectClient()
    floors = await client.get_machine_status("CA7527907")
    assert floors, "Expected floors with no token (public endpoint)"
