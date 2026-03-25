"""
Fixtures for HA component tests.

pytest_homeassistant_custom_component is loaded here (not in the root conftest)
so its socket-blocking autouse fixture only applies to tests in this directory.
"""
pytest_plugins = "pytest_homeassistant_custom_component"

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.wash_connect.const import (
    CONF_SRCODE,
    CONF_TOKEN,
    CONF_ULN,
    CONF_USER_ID,
    DOMAIN,
)

ENTRY_DATA = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "testpass",
    CONF_SRCODE: "W001274",
    CONF_USER_ID: "595122",
    CONF_TOKEN: "test-token",
    CONF_ULN: "CA7527907",
}

SAMPLE_FLOORS = {
    "1": {
        "name": "1st Floor",
        "machines": [
            {
                "machine_number": "001",
                "bt_name": "bt001",
                "last_user": "connect",
                "start_time": "2026-03-23T15:05:08.000Z",
                "status": "available",
                "time_remaining": "0",
                "type": "washer",
            },
            {
                "machine_number": "002",
                "bt_name": "bt002",
                "last_user": "connect",
                "start_time": "2026-03-23T14:20:00.000Z",
                "status": "in_use",
                "time_remaining": "45",
                "type": "dryer",
            },
        ],
    },
}
