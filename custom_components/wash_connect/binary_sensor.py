"""Binary sensor platform for Wash Connect — machine availability."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WashConnectCoordinator
from .sensor import _machine_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WashConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        MachineAvailableSensor(coordinator, entry, bt_name, _machine_device_info(entry, machine))
        for bt_name, machine in coordinator.data["machines"].items()
    )


class MachineAvailableSensor(CoordinatorEntity[WashConnectCoordinator], BinarySensorEntity):
    """True when the machine is available (not in use or out of service)."""

    _attr_has_entity_name = True
    _attr_translation_key = "is_available"
    # No device_class: RUNNING would mean on=in_use/off=available, which is
    # the inverse of our "is_available" semantics.  We manage icons manually.
    _attr_device_class = None

    def __init__(
        self,
        coordinator: WashConnectCoordinator,
        entry: ConfigEntry,
        bt_name: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._bt_name = bt_name
        self._attr_unique_id = f"{entry.entry_id}_{bt_name}_is_available"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return super().available and self._bt_name in self.coordinator.data.get("machines", {})

    @property
    def _machine(self) -> dict:
        return self.coordinator.data["machines"][self._bt_name]

    @property
    def is_on(self) -> bool:
        return self._machine["status"] == "available"

    @property
    def icon(self) -> str:
        return "mdi:check-circle-outline" if self.is_on else "mdi:timer-sand"
