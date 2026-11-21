import json
from pathlib import Path


def test_panchang_module_catalogue_discloses_current_jpl_capabilities_and_limits():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "data" / "ecosystem_modules.json").read_text(encoding="utf-8"))
    module = next(item for item in payload["modules"] if item["id"] == "panchang")
    assert "JPL DE440s" in module["description"]
    assert "अंग-समाप्ति समय" in module["description"]
    assert "मुहूर्त engine अभी उपलब्ध नहीं" in module["description"]


def test_jyotish_module_catalogue_discloses_vargas_dasha_and_validation_limits():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "data" / "ecosystem_modules.json").read_text(encoding="utf-8"))
    module = next(item for item in payload["modules"] if item["id"] == "jyotish")
    for feature in ("D2/D3/D7/D9/D10/D12", "महादशा-अंतरदशा-प्रत्यंतरदशा", "JPL DE440s"):
        assert feature in module["description"]
    assert "विशेषज्ञ सत्यापन बाकी" in module["description"]


def test_panchang_module_catalogue_discloses_jpl_transition_method_and_convention_limit():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "data" / "ecosystem_modules.json").read_text(encoding="utf-8"))
    module = next(item for item in payload["modules"] if item["id"] == "panchang")
    assert "10-minute scan + binary search" in module["description"]
    assert "approximate Lahiri" in module["description"]
