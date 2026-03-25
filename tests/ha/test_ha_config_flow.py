"""HA config flow tests — all API calls are mocked."""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import data_entry_flow
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.wash_connect.api import ApiError, AuthError
from custom_components.wash_connect.const import (
    CONF_SRCODE,
    CONF_TOKEN,
    CONF_ULN,
    CONF_USER_ID,
    DOMAIN,
)

USER_INPUT = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "testpass",
    CONF_SRCODE: "W001274",
}

VALID_LOGIN = {
    "user_id": "595122",
    "token": "test-token-abc",
    "last_uln": "CA7527907",
    "account_balance": "1175",
}

VALID_LOCATION = {
    "location_id": "11450",
    "location_name": "245 Montecito Ave",
    "uln": "CA7527907   ",
}

_PATCH = "custom_components.wash_connect.config_flow.WashConnectClient"


async def _init_flow(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    return result


async def test_config_flow_happy_path(hass):
    """Valid credentials produce a config entry with all expected keys."""
    result = await _init_flow(hass)

    with patch(_PATCH) as mock_cls:
        mock_cls.return_value.login = AsyncMock(return_value=VALID_LOGIN)
        mock_cls.return_value.get_locations = AsyncMock(return_value=VALID_LOCATION)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "245 Montecito Ave"
    data = result["data"]
    assert data[CONF_USERNAME] == "test@example.com"
    assert data[CONF_TOKEN] == "test-token-abc"
    assert data[CONF_USER_ID] == "595122"
    assert data[CONF_ULN] == "CA7527907"  # trailing space stripped


async def test_config_flow_invalid_auth(hass):
    """AuthError from login keeps the form open with invalid_auth error."""
    result = await _init_flow(hass)

    with patch(_PATCH) as mock_cls:
        mock_cls.return_value.login = AsyncMock(side_effect=AuthError("bad password"))
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


async def test_config_flow_invalid_srcode(hass):
    """ApiError from get_locations keeps the form open with invalid_srcode error."""
    result = await _init_flow(hass)

    with patch(_PATCH) as mock_cls:
        mock_cls.return_value.login = AsyncMock(return_value=VALID_LOGIN)
        mock_cls.return_value.get_locations = AsyncMock(
            side_effect=ApiError("no location")
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_srcode"


async def test_config_flow_cannot_connect(hass):
    """An unexpected exception keeps the form open with cannot_connect error."""
    result = await _init_flow(hass)

    with patch(_PATCH) as mock_cls:
        mock_cls.return_value.login = AsyncMock(side_effect=Exception("network down"))
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_config_flow_already_configured(hass):
    """A second setup for the same user+location aborts as already_configured."""
    # First setup
    result = await _init_flow(hass)
    with patch(_PATCH) as mock_cls:
        mock_cls.return_value.login = AsyncMock(return_value=VALID_LOGIN)
        mock_cls.return_value.get_locations = AsyncMock(return_value=VALID_LOCATION)
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    # Second attempt with the same credentials
    result = await _init_flow(hass)
    with patch(_PATCH) as mock_cls:
        mock_cls.return_value.login = AsyncMock(return_value=VALID_LOGIN)
        mock_cls.return_value.get_locations = AsyncMock(return_value=VALID_LOCATION)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
