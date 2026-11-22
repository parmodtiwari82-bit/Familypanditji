from datetime import datetime

from advanced_jyotish import calculate_vimshottari


def test_vimshottari_has_nine_antardashas_and_pratyantardashas_per_period():
    birth = datetime(1990, 12, 10, 0, 40)
    result = calculate_vimshottari(birth, 42.5)
    periods = result["mahadasha_periods"]
    assert len(periods) == 9
    assert all(len(md["antardashas"]) == 9 for md in periods)
    assert all(len(ad["pratyantardashas"]) == 9
               for md in periods for ad in md["antardashas"])


def test_vimshottari_identifies_birth_antardasha_and_pratyantardasha():
    birth = datetime(1990, 12, 10, 0, 40)
    result = calculate_vimshottari(birth, 42.5)
    md = next(p for p in result["mahadasha_periods"] if p["active_at_birth"] if "active_at_birth" in p)
    ad = next(p for p in md["antardashas"] if p["active_at_birth"])
    pd = next(p for p in ad["pratyantardashas"] if p["active_at_birth"])
    assert result["birth_period"] == md["lord"]
    assert result["birth_antardasha"] == ad["lord"]
    assert result["birth_pratyantardasha"] == pd["lord"]


def test_complete_future_subperiods_sum_to_parent_duration():
    result = calculate_vimshottari(datetime(1990, 12, 10, 0, 40), 42.5)
    for md in result["mahadasha_periods"][1:]:
        ad_total = sum(p["duration_years_approx"] for p in md["antardashas"])
        assert abs(ad_total - md["duration_years_approx"]) < 0.0001
        for ad in md["antardashas"]:
            pd_total = sum(p["duration_years_approx"] for p in ad["pratyantardashas"])
            assert abs(pd_total - ad["duration_years_approx"]) < 0.0001


def test_advanced_api_returns_birth_subperiods():
    from fastapi.testclient import TestClient
    from main import app

    response = TestClient(app).post("/api/jyotish/advanced", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.4499, "longitude": 80.3319, "timezone": "Asia/Kolkata"
    })
    assert response.status_code == 200
    data = response.json()["vimshottari"]
    assert data["birth_antardasha"]
    assert data["birth_pratyantardasha"]
    assert len(data["mahadasha_periods"][0]["antardashas"]) == 9


def test_frontend_exposes_birth_subperiods():
    from pathlib import Path

    html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
    assert "अंतरदशा" in html
    assert "प्रत्यंतरदशा" in html
    assert "birth_pratyantardasha" in html


def test_panchang_ui_displays_estimated_limb_end_times():
    from pathlib import Path

    html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
    assert "data.limb_ends_at?.tithi" in html
    assert "data.limb_ends_at?.nakshatra" in html
    assert "data.limb_ends_at?.yoga" in html
    assert "data.limb_ends_at?.karana" in html


def test_advanced_jyotish_uses_supplied_ephemeris_and_discloses_limits():
    from advanced_jyotish import calculate_advanced_jyotish

    birth = datetime(1990, 12, 10, 0, 40)
    supplied = {
        "Sun": 250.0, "Moon": 42.5, "Mars": 120.0, "Mercury": 260.0,
        "Jupiter": 80.0, "Venus": 280.0, "Saturn": 290.0,
        "Rahu": 100.0, "Ketu": 280.0,
    }
    result = calculate_advanced_jyotish(birth, 26.45, 80.33, supplied)
    assert result["calculation"] == (
        "advanced_derivations_from_supplied_ephemeris_with_approximate_lahiri"
    )
    assert "JPL DE440s" in result["accuracy_note_hi"]
    from vedic_calc import ayanamsa_lahiri_approx, norm
    expected_moon = norm(42.5 - ayanamsa_lahiri_approx(birth))
    assert result["navamsa_d9"]["Moon"]["longitude_degrees"] == round(expected_moon, 4)


def test_advanced_jyotish_marks_low_precision_fallback_when_no_override():
    from advanced_jyotish import calculate_advanced_jyotish

    result = calculate_advanced_jyotish(datetime(1990, 12, 10, 0, 40), 26.45, 80.33)
    assert result["calculation"] == "advanced_derivations_from_low_precision_starter_ephemeris"
