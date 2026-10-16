"""Fixtures: a Nuki Web account with one lock and one keypad code."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.const import CONF_API_TOKEN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nuki_web_access import coordinator
from custom_components.nuki_web_access.const import API_URL, DOMAIN

LOCK = {"smartlockId": 111, "accountId": 222, "name": "Main door", "type": 5}
APP_USER = {
    "id": "app1",
    "smartlockId": 111,
    "authId": 1,
    "type": 0,
    "name": "Lucas",
    "enabled": True,
    "remoteAllowed": True,
    "lockCount": 3,
}
CODE = {
    "id": "code1",
    "smartlockId": 111,
    "authId": 7,
    "type": 13,
    "name": "Diaristas",
    "enabled": True,
    "remoteAllowed": False,
    "lockCount": 0,
    "allowedWeekDays": 64,
    "allowedFromTime": 480,
    "allowedUntilTime": 900,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def no_verify_wait(monkeypatch):
    monkeypatch.setattr(coordinator, "VERIFY_DELAYS", (0, 0, 0))


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, unique_id="222", data={CONF_API_TOKEN: "tok"})


def mock_account(aioclient_mock, code: dict[str, Any] | None = None) -> None:
    aioclient_mock.get(f"{API_URL}/smartlock", json=[LOCK])
    aioclient_mock.get(f"{API_URL}/smartlock/111/auth", json=[APP_USER, code or CODE])
