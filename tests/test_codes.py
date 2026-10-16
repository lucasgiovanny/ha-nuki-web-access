"""Field conversions and update bodies."""

from datetime import UTC, datetime, time

from custom_components.nuki_web_access import codes


def test_weekdays_round_trip_and_no_mask_means_every_day():
    assert codes.weekdays_from_mask(64 + 4 + 1) == ["mon", "fri", "sun"]
    assert codes.mask_from_weekdays(["mon", "fri", "sun"]) == 69
    assert codes.weekdays_from_mask(None) == list(codes.WEEKDAYS)
    assert codes.weekdays_from_mask(0) == list(codes.WEEKDAYS)


def test_times_are_minutes_from_midnight():
    assert codes.minutes_to_time(480) == time(8, 0)
    assert codes.time_to_minutes(time(15, 30)) == 930
    assert codes.minutes_to_time(None) is None


def test_update_sends_back_unchanged_fields_and_none_clears_a_date():
    auth = {
        "id": "x",
        "name": "Diaristas",
        "enabled": True,
        "remoteAllowed": False,
        "allowedWeekDays": 64,
        "allowedUntilDate": "2026-10-20T15:00:00.000Z",
        "lockCount": 2,
        "code": 123456,
    }
    body = codes.build_update(auth, {"enabled": False, "allowedUntilDate": None})

    assert body == {
        "name": "Diaristas",
        "enabled": False,
        "remoteAllowed": False,
        "allowedWeekDays": 64,
        "allowedFromTime": 0,
        "allowedUntilTime": 0,
        "allowedUntilDate": None,
    }


def test_a_code_without_restrictions_sends_every_day_all_day():
    body = codes.build_update({"name": "P", "enabled": True}, {"enabled": False})
    assert body["allowedWeekDays"] == 127
    assert body["allowedFromTime"] == body["allowedUntilTime"] == 0


def test_dates_are_sent_in_utc():
    body = codes.build_update(
        {"name": "P"}, {"allowedFromDate": datetime(2026, 10, 20, 7, 30, tzinfo=UTC)}
    )
    assert body["allowedFromDate"] == "2026-10-20T07:30:00.000Z"


def test_mismatches_compare_dates_as_moments():
    until = datetime(2026, 10, 20, 15, 0, tzinfo=UTC)
    assert (
        codes.mismatches(
            {"allowedUntilDate": "2026-10-20T15:00:00.000Z"}, {"allowedUntilDate": until}
        )
        == []
    )
    assert codes.mismatches({}, {"allowedUntilDate": None, "enabled": False}) == ["enabled"]
    assert codes.mismatches({"enabled": True}, {"enabled": False}) == ["enabled"]


def test_mismatches_ignore_the_milliseconds_nuki_drops():
    sent = datetime(2026, 10, 20, 15, 0, 4, 512000, tzinfo=UTC)
    assert (
        codes.mismatches({"allowedFromDate": "2026-10-20T15:00:04.000Z"}, {"allowedFromDate": sent})
        == []
    )
