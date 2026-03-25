"""Config flow for Wash Connect."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .api import ApiError, AuthError, WashConnectClient
from .const import CONF_SRCODE, CONF_TOKEN, CONF_ULN, CONF_USER_ID, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_SRCODE): str,
    }
)


class WashConnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Wash Connect config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            client = WashConnectClient()
            try:
                session = await client.login(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                location = await client.get_locations(user_input[CONF_SRCODE])
            except AuthError:
                errors["base"] = "invalid_auth"
            except ApiError:
                errors["base"] = "invalid_srcode"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"{session['user_id']}_{location['uln'].strip()}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=location["location_name"],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SRCODE: user_input[CONF_SRCODE],
                        CONF_USER_ID: session["user_id"],
                        CONF_TOKEN: session["token"],
                        CONF_ULN: location["uln"].strip(),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
