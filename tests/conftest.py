"""
Root conftest — loads the HA custom component test plugin for all tests.

pytest_homeassistant_custom_component's socket-blocking autouse fixture applies
to all tests; E2E tests opt out via pytestmark = pytest.mark.enable_socket.
"""
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def _auto_enable_custom_integrations(request):
    """Enable custom integrations for any test that uses the hass fixture."""
    if "hass" in request.fixturenames:
        request.getfixturevalue("enable_custom_integrations")
