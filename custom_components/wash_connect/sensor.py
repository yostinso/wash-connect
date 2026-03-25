"""Sensor platform for Wash Connect."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import WashConnectCoordinator
from .helpers import estimated_completion, parse_dt, to_int


# ---------------------------------------------------------------------------
# Entity descriptions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class MachineSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any] = lambda _: None



MACHINE_SENSOR_DESCRIPTIONS: tuple[MachineSensorDescription, ...] = (
    MachineSensorDescription(
        key="status",
        translation_key="status",
        icon="mdi:washing-machine",
        value_fn=lambda m: m["status"],
    ),
    MachineSensorDescription(
        key="time_remaining",
        translation_key="time_remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
        value_fn=lambda m: to_int(m["time_remaining"]),
    ),
    MachineSensorDescription(
        key="start_time",
        translation_key="start_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda m: parse_dt(m["start_time"]),
    ),
    MachineSensorDescription(
        key="estimated_completion",
        translation_key="estimated_completion",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=estimated_completion,
    ),
    MachineSensorDescription(
        key="bt_name",
        translation_key="bt_name",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m["bt_name"],
    ),
)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WashConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for bt_name, machine in coordinator.data["machines"].items():
        device_info = _machine_device_info(entry, machine)
        for description in MACHINE_SENSOR_DESCRIPTIONS:
            entities.append(
                MachineSensor(coordinator, entry, bt_name, description, device_info)
            )

    entities.append(AccountBalanceSensor(coordinator, entry))
    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Machine sensor
# ---------------------------------------------------------------------------


class MachineSensor(CoordinatorEntity[WashConnectCoordinator], SensorEntity):
    """A single sensor for one attribute of one machine."""

    entity_description: MachineSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WashConnectCoordinator,
        entry: ConfigEntry,
        bt_name: str,
        description: MachineSensorDescription,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._bt_name = bt_name
        self._attr_unique_id = f"{entry.entry_id}_{bt_name}_{description.key}"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return super().available and self._bt_name in self.coordinator.data.get("machines", {})

    @property
    def _machine(self) -> dict:
        return self.coordinator.data["machines"][self._bt_name]

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._machine)


# ---------------------------------------------------------------------------
# Account balance sensor
# ---------------------------------------------------------------------------


class AccountBalanceSensor(CoordinatorEntity[WashConnectCoordinator], SensorEntity):
    """Account balance in cents."""

    _attr_has_entity_name = True
    _attr_translation_key = "balance_cents"
    _attr_icon = "mdi:cash"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: WashConnectCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_balance_cents"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_account")},
            name=f"{MANUFACTURER} Account",
            manufacturer=MANUFACTURER,
        )

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("balance_cents")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _machine_device_info(entry: ConfigEntry, machine: dict) -> DeviceInfo:
    machine_type = machine["type"].capitalize()  # "Washer" / "Dryer"
    floor = machine["floor_name"]
    number = machine["machine_number"]
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{machine['bt_name']}")},
        name=f"{floor} {machine_type} {number}",
        manufacturer=MANUFACTURER,
        model=machine_type,
    )
