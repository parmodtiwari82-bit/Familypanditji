from datetime import datetime, timezone

import pytest

from precision_ephemeris import (
    calculate_tropical_longitudes,
    mean_node_longitudes,
    to_sidereal_longitudes,
)


def test_mean_lunar_nodes_are_opposite_and_normalized():
    rahu, ketu = mean_node_longitudes(datetime(2026, 11, 21, tzinfo=timezone.utc))
    assert 0 <= rahu < 360
    assert 0 <= ketu < 360
    assert abs(((ketu - rahu) % 360) - 180) < 1e-9


def test_sidereal_conversion_applies_same_ayanamsa_and_adds_mean_nodes():
    moment = datetime(2026, 11, 21, tzinfo=timezone.utc)
    tropical = {"Sun": 240.0, "Moon": 120.0}
    result = to_sidereal_longitudes(tropical, moment)
    assert set(result) == {"Sun", "Moon", "Rahu", "Ketu"}
    assert abs(((result["Ketu"] - result["Rahu"]) % 360) - 180) < 1e-9
    assert all(0 <= value < 360 for value in result.values())


def test_ephemeris_rejects_naive_datetime_before_loading_file(tmp_path):
    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_tropical_longitudes(datetime(2026, 11, 21), tmp_path / "de440s.bsp")


def test_ephemeris_rejects_dates_outside_de440s_range(tmp_path):
    with pytest.raises(ValueError, match="1849 through 2150"):
        calculate_tropical_longitudes(
            datetime(1700, 1, 1, tzinfo=timezone.utc), tmp_path / "missing.bsp"
        )


def test_ephemeris_requires_explicit_local_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="JPL ephemeris file not found"):
        calculate_tropical_longitudes(
            datetime(2026, 11, 21, tzinfo=timezone.utc), tmp_path / "missing.bsp"
        )


def test_jpl_sunrise_requires_timezone_aware_datetime(tmp_path):
    from precision_ephemeris import calculate_sunrise_sunset
    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_sunrise_sunset(datetime(2026, 11, 21, 12, 0), 26.45, 80.33, tmp_path / "missing.bsp")


def test_jpl_sunrise_rejects_invalid_coordinates(tmp_path):
    from precision_ephemeris import calculate_sunrise_sunset
    with pytest.raises(ValueError, match="latitude/longitude"):
        calculate_sunrise_sunset(datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc), 91, 80.33, tmp_path / "missing.bsp")


def test_jpl_sunrise_enforces_de440s_date_range(tmp_path):
    from precision_ephemeris import calculate_sunrise_sunset
    with pytest.raises(ValueError, match="1849 through 2150"):
        calculate_sunrise_sunset(datetime(1800, 1, 1, tzinfo=timezone.utc), 26.45, 80.33, tmp_path / "missing.bsp")


def test_jpl_sunrise_requires_local_ephemeris_file(tmp_path):
    from precision_ephemeris import calculate_sunrise_sunset
    with pytest.raises(FileNotFoundError, match="JPL ephemeris file not found"):
        calculate_sunrise_sunset(datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc), 26.45, 80.33, tmp_path / "missing.bsp")


def test_jpl_panchang_transitions_require_timezone_aware_datetime(tmp_path):
    from precision_ephemeris import calculate_panchang_limb_transitions
    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_panchang_limb_transitions(datetime(2026, 11, 21), tmp_path / "missing.bsp")


def test_jpl_panchang_transitions_enforce_supported_date_range(tmp_path):
    from precision_ephemeris import calculate_panchang_limb_transitions
    with pytest.raises(ValueError, match="1849 through 2150"):
        calculate_panchang_limb_transitions(datetime(1700, 1, 1, tzinfo=timezone.utc), tmp_path / "missing.bsp")


def test_jpl_panchang_transitions_require_local_ephemeris_file(tmp_path):
    from precision_ephemeris import calculate_panchang_limb_transitions
    with pytest.raises(FileNotFoundError, match="JPL ephemeris file not found"):
        calculate_panchang_limb_transitions(datetime(2026, 11, 21, tzinfo=timezone.utc), tmp_path / "missing.bsp")


def test_jpl_panchang_transitions_validate_scan_horizon(tmp_path):
    from precision_ephemeris import calculate_panchang_limb_transitions
    with pytest.raises(ValueError, match="max_hours"):
        calculate_panchang_limb_transitions(datetime(2026, 11, 21, tzinfo=timezone.utc), tmp_path / "missing.bsp", max_hours=0)
