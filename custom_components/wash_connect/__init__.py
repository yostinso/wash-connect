"""The Wash Connect integration."""
from __future__ import annotations

from .const import DOMAIN

# homeassistant is not available in the test environment, so guard all HA
# imports.  The async_setup_entry / async_unload_entry functions are only
# ever called by HA itself, never by tests.
try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import Platform
    from homeassistant.core import HomeAssistant

    from .coordinator import WashConnectCoordinator

    PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Set up Wash Connect from a config entry."""
        coordinator = WashConnectCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True

    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Unload a config entry."""
        unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        if unloaded:
            hass.data[DOMAIN].pop(entry.entry_id)
        return unloaded

except ImportError:
    pass
