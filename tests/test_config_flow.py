"""Adding the account with its API token."""

from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN
from homeassistant.data_entry_flow import FlowResultType

from custom_components.nuki_web_access.const import API_URL, DOMAIN

from .conftest import LOCK


async def test_token_with_bearer_prefix_creates_the_entry(hass, aioclient_mock):
    aioclient_mock.get(f"{API_URL}/smartlock", json=[LOCK])
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "Bearer  abc "}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_API_TOKEN: "abc"}
    assert result["result"].unique_id == "222"


async def test_refused_token_shows_an_error(hass, aioclient_mock):
    aioclient_mock.get(f"{API_URL}/smartlock", status=401)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "x"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
