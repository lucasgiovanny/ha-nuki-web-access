"""Keypad code fields: reading them from Nuki Web and building updates."""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Any

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
ALL_WEEKDAYS = 127

_UPDATABLE = (
    "name",
    "enabled",
    "remoteAllowed",
    "allowedFromDate",
    "allowedUntilDate",
    "allowedWeekDays",
    "allowedFromTime",
    "allowedUntilTime",
)
_DATES = ("allowedFromDate", "allowedUntilDate")


def parse_date(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def format_date(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def weekdays_from_mask(mask: int | None) -> list[str]:
    """Nuki's bitmask counts down from 64 (Monday) to 1 (Sunday); no mask means every day."""
    mask = ALL_WEEKDAYS if mask in (None, 0) else mask
    return [day for bit, day in zip(range(6, -1, -1), WEEKDAYS, strict=True) if mask & (1 << bit)]


def mask_from_weekdays(days: list[str]) -> int:
    return sum(1 << (6 - WEEKDAYS.index(day)) for day in days)


def minutes_to_time(minutes: int | None) -> time | None:
    return None if minutes is None else time(minutes // 60 % 24, minutes % 60)


def time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def build_update(auth: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """The code's current fields with the changes applied; a None date removes that limit."""
    # Nuki rejects or ignores partial updates, so unchanged fields are sent back as they are.
    body = {key: auth[key] for key in _UPDATABLE if key in auth}
    # Without the weekday and time fields Nuki keeps the old dates; these defaults mean no restriction.
    body.setdefault("allowedWeekDays", ALL_WEEKDAYS)
    body.setdefault("allowedFromTime", 0)
    body.setdefault("allowedUntilTime", 0)
    for key, value in changes.items():
        body[key] = format_date(value) if key in _DATES else value
    return body


def mismatches(auth: dict[str, Any], changes: dict[str, Any]) -> list[str]:
    """The changed fields that Nuki Web does not show with their new value yet."""
    wrong = []
    for key, expected in changes.items():
        actual = auth.get(key)
        if key in _DATES:
            # Nuki stores whole seconds, so compare what was actually sent.
            if parse_date(actual) != parse_date(format_date(expected)):
                wrong.append(key)
        elif actual != expected:
            wrong.append(key)
    return wrong
