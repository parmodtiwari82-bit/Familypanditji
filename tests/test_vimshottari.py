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
