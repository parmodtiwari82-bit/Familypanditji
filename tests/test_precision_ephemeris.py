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
