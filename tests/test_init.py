"""Setting up, reading the codes and changing them through Nuki Web."""

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.nuki_web_access.const import API_URL, DOMAIN

from .conftest import CODE, mock_account

SWITCH = "switch.main_door_keypad_codes_diaristas_enabled"


async def _setup(hass, entry):
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_only_keypad_codes_become_entities(hass, entry, aioclient_mock):
    mock_account(aioclient_mock)
    await _setup(hass, entry)

    state = hass.states.get(SWITCH)
    assert state.state == "on"
    assert state.attributes["auth_id"] == 7
    assert state.attributes["weekdays"] == ["mon"]
    assert str(state.attributes["from_time"]) == "08:00:00"
    assert (
        hass.states.get("datetime.main_door_keypad_codes_diaristas_valid_until").state == "unknown"
    )
    assert not [s for s in hass.states.async_entity_ids() if "lucas" in s]


async def test_turning_off_sends_the_full_code_and_waits_for_nuki(hass, entry, aioclient_mock):
    mock_account(aioclient_mock)
    await _setup(hass, entry)
    aioclient_mock.post(f"{API_URL}/smartlock/111/auth/code1", status=204)
    aioclient_mock.get(f"{API_URL}/smartlock/111/auth/code1", json={**CODE, "enabled": False})

    await hass.services.async_call("switch", "turn_off", {"entity_id": SWITCH}, blocking=True)

    post = next(call for call in aioclient_mock.mock_calls if call[0] == "POST")
    assert post[2] == {
        "name": "Diaristas",
        "enabled": False,
        "remoteAllowed": False,
        "allowedWeekDays": 64,
        "allowedFromTime": 480,
        "allowedUntilTime": 900,
    }
    assert hass.states.get(SWITCH).state == "off"


async def test_set_access_with_a_window(hass, entry, aioclient_mock):
    mock_account(aioclient_mock)
    await _setup(hass, entry)
    aioclient_mock.post(f"{API_URL}/smartlock/111/auth/code1", status=204)
    aioclient_mock.get(
        f"{API_URL}/smartlock/111/auth/code1",
        json={**CODE, "allowedUntilDate": "2026-10-20T14:00:00.000Z", "allowedWeekDays": 127},
    )

    await hass.services.async_call(
        DOMAIN,
        "set_access",
        {
            "entity_id": SWITCH,
            "valid_until": "2026-10-20 14:00:00+00:00",
            "weekdays": list(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
        },
        blocking=True,
    )

    post = next(call for call in aioclient_mock.mock_calls if call[0] == "POST")
    assert post[2]["allowedUntilDate"] == "2026-10-20T14:00:00.000Z"
    assert post[2]["allowedWeekDays"] == 127


async def test_a_change_nuki_never_shows_is_retried_then_fails(hass, entry, aioclient_mock):
    mock_account(aioclient_mock)
    await _setup(hass, entry)
    aioclient_mock.post(f"{API_URL}/smartlock/111/auth/code1", status=204)
    aioclient_mock.get(f"{API_URL}/smartlock/111/auth/code1", json=CODE)

    with pytest.raises(HomeAssistantError, match="enabled"):
        await hass.services.async_call("switch", "turn_off", {"entity_id": SWITCH}, blocking=True)

    assert [call[0] for call in aioclient_mock.mock_calls].count("POST") == 2
    assert hass.states.get(SWITCH).state == "on"


async def test_a_refused_token_asks_for_a_new_one(hass, entry, aioclient_mock):
    aioclient_mock.get(f"{API_URL}/smartlock", status=401)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert [flow["context"]["source"] for flow in hass.config_entries.flow.async_progress()] == [
        "reauth"
    ]
