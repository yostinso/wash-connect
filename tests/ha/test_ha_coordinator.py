"""HA coordinator tests — verifies fetch logic and re-auth behaviour."""
import pytest
from unittest.mock import AsyncMock

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.wash_connect.api import AuthError, WashConnectError
from custom_components.wash_connect.coordinator import WashConnectCoordinator
from custom_components.wash_connect.const import DOMAIN
from custom_components.wash_connect.helpers import flatten_machines
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import ENTRY_DATA, SAMPLE_FLOORS


def _make_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)
    return entry


def _make_coordinator(hass):
    entry = _make_entry(hass)
    coordinator = WashConnectCoordinator(hass, entry)
    return coordinator


def _mock_client(coordinator, floors=None, balance=1175):
    """Replace coordinator._client with an AsyncMock."""
    coordinator._client.get_machine_status = AsyncMock(
        return_value=floors if floors is not None else SAMPLE_FLOORS
    )
    coordinator._client.get_account_balance = AsyncMock(return_value=balance)
    coordinator._client.login = AsyncMock(return_value={"token": "new-token"})
    return coordinator._client


async def test_coordinator_fetch_returns_machines_and_balance(hass):
    """A successful fetch populates machines (keyed by bt_name) and balance_cents."""
    coordinator = _make_coordinator(hass)
    _mock_client(coordinator)

    await coordinator.async_refresh()

    assert coordinator.data["balance_cents"] == 1175
    machines = coordinator.data["machines"]
    assert "bt001" in machines
    assert "bt002" in machines
    assert machines["bt001"]["floor_name"] == "1st Floor"


async def test_coordinator_fetch_flattens_machines(hass):
    """Coordinator data has machines keyed by bt_name, not nested by floor."""
    coordinator = _make_coordinator(hass)
    _mock_client(coordinator)
    await coordinator.async_refresh()

    # Values are flat dicts with floor_name injected
    machine = coordinator.data["machines"]["bt001"]
    assert "floor_name" in machine
    assert "machines" not in machine  # not the raw nested structure


async def test_coordinator_reauth_on_auth_error(hass):
    """AuthError on first fetch triggers re-login, then a successful retry."""
    coordinator = _make_coordinator(hass)
    client = _mock_client(coordinator)

    # First call raises AuthError; second call (after re-auth) succeeds.
    client.get_account_balance = AsyncMock(
        side_effect=[AuthError("expired"), 1175]
    )

    await coordinator.async_refresh()

    client.login.assert_awaited_once()
    assert coordinator.data["balance_cents"] == 1175


async def test_coordinator_reauth_failure_raises_update_failed(hass):
    """If re-authentication itself fails, UpdateFailed is raised."""
    coordinator = _make_coordinator(hass)
    client = _mock_client(coordinator)

    client.get_account_balance = AsyncMock(side_effect=AuthError("expired"))
    client.login = AsyncMock(side_effect=AuthError("bad credentials"))

    with pytest.raises(UpdateFailed):
        await coordinator.async_refresh()


async def test_coordinator_api_error_raises_update_failed(hass):
    """A non-auth WashConnectError (e.g. bad response) raises UpdateFailed."""
    coordinator = _make_coordinator(hass)
    client = _mock_client(coordinator)

    client.get_machine_status = AsyncMock(side_effect=WashConnectError("bad response"))

    with pytest.raises(UpdateFailed):
        await coordinator.async_refresh()
