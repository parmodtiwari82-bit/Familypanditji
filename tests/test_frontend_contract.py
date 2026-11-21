from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_advanced_jyotish_uses_same_selected_engine_as_birth_chart():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    advanced_handler = html.split("document.getElementById('advancedJyotishButton')", 1)[1]
    assert "engine:document.getElementById('kEngine').value" in advanced_handler
    assert "fetch('/api/jyotish/advanced'" in advanced_handler


def test_panchang_ui_discloses_engine_accuracy_and_missing_transition_times():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "data.engine?.note_hi" in html
    assert "data.sunrise_sunset_status" in html
    assert "इस इंजन मोड में उपलब्ध नहीं" in html
    assert "Skyfield + स्थानीय फ़ाइल आवश्यक" in html


def test_indian_city_presets_fill_panchang_and_birth_coordinates_without_gps():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "INDIA_CITY_PRESETS" in html
    assert "bindCityPreset('pCity','pLat','pLon')" in html
    assert "bindCityPreset('kCity','kLat','kLon')" in html
    assert "कानपुर / Kanpur" in html
    assert "लखनऊ / Lucknow" in html
    assert "कोई GPS permission नहीं ली जाती" in html


def test_city_preset_coordinates_remain_editable_after_selection():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="pLat" type="number"' in html
    assert 'id="pLon" type="number"' in html
    assert 'id="kLat" type="number"' in html
    assert 'id="kLon" type="number"' in html
