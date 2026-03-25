"""DataUpdateCoordinator for Wash Connect."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AuthError, WashConnectClient, WashConnectError
from .const import CONF_TOKEN, CONF_ULN, DOMAIN, UPDATE_INTERVAL_SECONDS
from .helpers import flatten_machines

_LOGGER = logging.getLogger(__name__)


class WashConnectCoordinator(DataUpdateCoordinator[dict]):
    """Polls machine status and account balance; re-authenticates on token expiry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._client = WashConnectClient(
            token=entry.data[CONF_TOKEN],
            session=async_get_clientsession(hass),
        )
        self._uln = entry.data[CONF_ULN]
        self._email = entry.data[CONF_USERNAME]
        self._password = entry.data[CONF_PASSWORD]
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    async def _async_update_data(self) -> dict:
        try:
            return await self._fetch()
        except AuthError:
            _LOGGER.warning("Token expired — re-authenticating")
            try:
                await self._reauthenticate()
                return await self._fetch()
            except AuthError as exc:
                raise UpdateFailed(f"Re-authentication failed: {exc}") from exc
        except WashConnectError as exc:
            raise UpdateFailed(f"Error fetching Wash Connect data: {exc}") from exc

    async def _reauthenticate(self) -> None:
        await self._client.login(self._email, self._password)

    async def _fetch(self) -> dict:
        floors = await self._client.get_machine_status(self._uln)
        balance = await self._client.get_account_balance()
        return {
            "machines": flatten_machines(floors),
            "balance_cents": balance,
        }
