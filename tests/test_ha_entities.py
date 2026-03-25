"""
HA entity tests — loads the full integration and inspects entity state/config.

Uses a mocked WashConnectClient so no live API calls are made.
"""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.helpers import entity_registry as er

from custom_components.wash_connect.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from fixtures import ENTRY_DATA, SAMPLE_FLOORS

_COORDINATOR_CLIENT = "custom_components.wash_connect.coordinator.WashConnectClient"

# With 2 machines (SAMPLE_FLOORS):
#   2 × 5 machine sensors  = 10
#   1 account balance       =  1
#   2 binary sensors        =  2
EXPECTED_SENSORS = 11
EXPECTED_BINARY_SENSORS = 2


async def _setup_integration(hass):
    """Load the integration with mocked API calls; return the config entry."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA)
    entry.add_to_hass(hass)

    with patch(_COORDINATOR_CLIENT) as mock_cls:
        mock_cls.return_value.get_machine_status = AsyncMock(return_value=SAMPLE_FLOORS)
        mock_cls.return_value.get_account_balance = AsyncMock(return_value=1175)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_entity_count(hass):
    """Correct number of sensors and binary sensors are registered."""
    entry = await _setup_integration(hass)
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)

    sensors = [e for e in entries if e.domain == "sensor"]
    binary_sensors = [e for e in entries if e.domain == "binary_sensor"]

    assert len(sensors) == EXPECTED_SENSORS
    assert len(binary_sensors) == EXPECTED_BINARY_SENSORS


async def test_bt_name_sensor_is_default_hidden(hass):
    """bt_name is a diagnostic sensor that is hidden from the UI by default."""
    entry = await _setup_integration(hass)
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)

    bt_sensors = [e for e in entries if e.unique_id.endswith("_bt_name")]
    assert bt_sensors, "Expected at least one bt_name sensor"
    for sensor in bt_sensors:
        assert sensor.disabled_by is not None


async def test_balance_sensor_on_separate_device(hass):
    """balance_cents is on the account device, not a machine device."""
    entry = await _setup_integration(hass)
    registry = er.async_get(hass)

    balance_entry = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_balance_cents"
    )
    assert balance_entry is not None

    entity = registry.async_get(balance_entry)
    assert entity.device_id is not None

    # The machine sensors use bt_name in their unique_ids; balance does not.
    assert "bt001" not in entity.unique_id
    assert "bt002" not in entity.unique_id


async def test_is_available_true_for_available_machine(hass):
    """is_available binary sensor is ON when machine status is 'available'."""
    entry = await _setup_integration(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{entry.entry_id}_bt001_is_available"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state.state == "on"


async def test_is_available_false_for_in_use_machine(hass):
    """is_available binary sensor is OFF when machine status is 'in_use'."""
    entry = await _setup_integration(hass)
    registry = er.async_get(hass)

    entity_id = registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{entry.entry_id}_bt002_is_available"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state.state == "off"
