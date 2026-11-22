"""Mathematical invariants for classical Jyotish derivations.

These tests verify internal formula consistency only; they do not certify
ephemeris accuracy, ayanamsa choice, regional conventions, or predictions.
"""
import pytest

from advanced_jyotish import navamsa_sign, divisional_sign


def test_navamsa_starts_and_pada_boundaries():
    assert navamsa_sign(0.0) == "मेष"
    assert navamsa_sign(30.0 / 9.0 - 1e-7) == "मेष"
    assert navamsa_sign(30.0 / 9.0) == "वृषभ"
    assert navamsa_sign(2 * 30.0 / 9.0) == "मिथुन"


def test_navamsa_classical_starting_signs_for_fixed_dual_and_movable_rashis():
    assert navamsa_sign(30.0) == "मकर"   # Taurus: ninth sign
    assert navamsa_sign(60.0) == "तुला"   # Gemini: fifth sign
    assert navamsa_sign(90.0) == "कर्क"   # Cancer: same sign


def test_hora_alternates_leo_and_cancer_by_sign_parity():
    assert divisional_sign(0.0, 2, "hora") == "सिंह"
    assert divisional_sign(15.0, 2, "hora") == "कर्क"
    assert divisional_sign(30.0, 2, "hora") == "कर्क"
    assert divisional_sign(45.0, 2, "hora") == "सिंह"


def test_drekkana_uses_same_fifth_and_ninth_signs():
    assert divisional_sign(0.0, 3, "drekkana") == "मेष"
    assert divisional_sign(10.0, 3, "drekkana") == "सिंह"
    assert divisional_sign(20.0, 3, "drekkana") == "धनु"


def test_saptamsa_and_dashamsa_even_sign_offsets():
    assert divisional_sign(30.0, 7, "saptamsa") == "वृश्चिक"
    assert divisional_sign(30.0, 10, "dashamsa") == "मकर"


def test_dwadasamsa_advances_one_sign_per_part():
    assert divisional_sign(30.0, 12, "dwadasamsa") == "वृषभ"
    assert divisional_sign(32.5, 12, "dwadasamsa") == "मिथुन"


@pytest.mark.parametrize("division", [0, 31, 1.5, "9"])
def test_divisional_chart_rejects_invalid_division(division):
    with pytest.raises(ValueError, match="division must be an integer"):
        divisional_sign(12.0, division, "dwadasamsa")


def test_divisional_chart_rejects_unknown_method():
    with pytest.raises(ValueError, match="unsupported varga method"):
        divisional_sign(12.0, 9, "unknown")


def test_jpl_mode_kundli_and_advanced_charts_include_mean_rahu_ketu():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from vedic_calc import calculate_kundli
    from advanced_jyotish import calculate_advanced_jyotish

    birth = datetime(1982, 1, 1, 0, 30, tzinfo=ZoneInfo("Asia/Kolkata"))
    tropical = {
        "Sun": 280.0, "Moon": 100.0, "Mercury": 275.0,
        "Venus": 300.0, "Mars": 210.0, "Jupiter": 190.0, "Saturn": 200.0,
    }

    chart = calculate_kundli(birth, 26.4499, 80.3319, tropical_override=tropical)
    assert {"Rahu", "Ketu"} <= set(chart["planets"])
    assert abs(
        (chart["planets"]["Ketu"]["longitude_degrees"]
         - chart["planets"]["Rahu"]["longitude_degrees"]) % 360 - 180
    ) < 0.001

    advanced = calculate_advanced_jyotish(
        birth, 26.4499, 80.3319, tropical_override=tropical
    )
    assert {"Rahu", "Ketu"} <= set(advanced["navamsa_d9"])
    assert {"Rahu", "Ketu"} <= set(advanced["divisional_charts"]["d10_dashamsa"])
