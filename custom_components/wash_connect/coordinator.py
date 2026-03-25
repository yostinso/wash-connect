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
from .const import CONF_REFRESH_TOKEN, CONF_TOKEN, CONF_ULN, DOMAIN, UPDATE_INTERVAL_SECONDS
from .helpers import flatten_machines

_LOGGER = logging.getLogger(__name__)


class WashConnectCoordinator(DataUpdateCoordinator[dict]):
    """Polls machine status and account balance; re-authenticates on token expiry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        self._client = WashConnectClient(
            token=entry.data[CONF_TOKEN],
            refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
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
            pass
        except WashConnectError as exc:
            raise UpdateFailed(f"Error fetching Wash Connect data: {exc}") from exc

        _LOGGER.warning("Token expired — re-authenticating")

        # Try a token refresh first (no password needed, no new login invalidates others).
        if await self._client.refresh_firebase_token():
            try:
                data = await self._fetch()
                self._persist_tokens()
                return data
            except AuthError:
                _LOGGER.warning("Refreshed token rejected — falling back to full re-login")

        # Full re-login as fallback.
        try:
            await self._client.login(self._email, self._password)
            data = await self._fetch()
            self._persist_tokens()
            return data
        except AuthError as exc:
            raise UpdateFailed(f"Re-authentication failed: {exc}") from exc
        except WashConnectError as exc:
            raise UpdateFailed(f"Error fetching Wash Connect data: {exc}") from exc

    def _persist_tokens(self) -> None:
        """Write the current token + refresh_token back to the config entry."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            data={
                **self._entry.data,
                CONF_TOKEN: self._client.token,
                CONF_REFRESH_TOKEN: self._client.refresh_token,
            },
        )

    async def _fetch(self) -> dict:
        floors = await self._client.get_machine_status(self._uln)
        balance = await self._client.get_account_balance()
        return {
            "machines": flatten_machines(floors),
            "balance_cents": balance,
        }
