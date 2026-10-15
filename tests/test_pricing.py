from datetime import datetime, timedelta, timezone

import pytest

from app.pricing import (
    DAILY_CAP_PAISE,
    DAY_RATE_PAISE,
    FREE_MINUTES,
    NIGHT_RATE_PAISE,
    PricingError,
    allocate,
    billable_hours,
    fee,
    fits,
    normalise_vehicle,
    validate_stay,
)

LOCAL = timezone(timedelta(hours=5, minutes=30))


def at(hour, minute=0):
    return datetime(2026, 1, 1, hour, minute, tzinfo=LOCAL)


def test_exact_free_period():
    result = fee(at(10), at(10) + timedelta(minutes=FREE_MINUTES))
    assert result["total_paise"] == 0
    assert result["billable_hours"] == 0


def test_31_minutes_charges_one_hour():
    result = fee(at(10), at(10) + timedelta(minutes=31))
    assert result["billable_hours"] == 1
    assert result["total_paise"] == DAY_RATE_PAISE


def test_partial_billable_hour_rounds_up():
    result = fee(at(10), at(10) + timedelta(minutes=91))
    assert result["billable_hours"] == 2
    assert result["total_paise"] == 2 * DAY_RATE_PAISE


def test_night_rate_is_lower_than_day_rate():
    hours = billable_hours(at(23), at(23) + timedelta(minutes=91))
    assert hours
    assert all(rate == NIGHT_RATE_PAISE for _, _, rate in hours)


def test_daily_cap_applies_to_long_daytime_stay():
    result = fee(at(7), at(21))
    assert result["total_paise"] == DAILY_CAP_PAISE
    assert result["capped"] is True


def test_vehicle_names_are_normalised():
    assert normalise_vehicle("  CAR ") == "compact"
    assert normalise_vehicle("scooter") == "bike"


def test_invalid_vehicle_is_rejected():
    with pytest.raises(PricingError):
        normalise_vehicle("spaceship")


def test_vehicle_fits_same_size_or_larger_slot():
    assert fits("bike", "bike")
    assert fits("bike", "compact")
    assert not fits("compact", "bike")


def test_truck_cannot_use_car_slot():
    slots = [
        {"id": 1, "floor": 1, "size": "compact", "code": "1-C01"}
    ]
    assert allocate("truck", slots) is None


def test_allocate_chooses_smallest_fitting_slot():
    slots = [
        {"id": 1, "floor": 1, "size": "large", "code": "1-L01"},
        {"id": 2, "floor": 2, "size": "compact", "code": "2-C01"},
        {"id": 3, "floor": 1, "size": "compact", "code": "1-C02"},
    ]
    chosen = allocate("car", slots)
    assert chosen["code"] == "1-C02"


def test_exit_before_entry_is_rejected():
    with pytest.raises(PricingError):
        validate_stay(at(12), at(11))


def test_stay_over_maximum_is_rejected():
    entry = at(10)
    exit_at = entry + timedelta(days=31)
    with pytest.raises(PricingError):
        validate_stay(entry, exit_at)
