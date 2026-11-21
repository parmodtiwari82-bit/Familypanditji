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
