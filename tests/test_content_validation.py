import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_content.py"
SPEC = importlib.util.spec_from_file_location("validate_content", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_all_content_catalogues_pass_structural_validation():
    assert VALIDATOR.validate() == []


def test_temple_catalogue_requires_https_source_links_and_iso_review_date():
    errors = []
    VALIDATOR.check_temple_records([{
        "id": "sample-temple",
        "name_hi": "नमूना मंदिर",
        "name_en": "Sample Temple",
        "deity": "Shiva",
        "city": "Kanpur",
        "state": "Uttar Pradesh",
        "country": "India",
        "address": "Sample address",
        "official_website": "http://example.com",
        "official_information_url": "not-a-url",
        "source_status": "official_source",
        "last_checked_on": "yesterday",
    }], errors)
    assert any("official_website must be an absolute HTTPS URL" in item for item in errors)
    assert any("official_information_url must be an absolute HTTPS URL" in item for item in errors)
    assert any("last_checked_on must be an ISO date" in item for item in errors)


def test_temple_catalogue_rejects_duplicate_ids():
    errors = []
    record = {
        "id": "same-temple",
        "name_hi": "मंदिर",
        "name_en": "Temple",
        "deity": "Shiva",
        "city": "Kanpur",
        "state": "Uttar Pradesh",
        "country": "India",
        "address": "Sample address",
        "official_website": "https://example.com",
        "official_information_url": "https://example.com/info",
        "source_status": "official_source",
        "last_checked_on": "2026-11-23",
    }
    VALIDATOR.check_temple_records([record, record], errors)
    assert any("duplicate id 'same-temple'" in item for item in errors)


def test_missing_source_provenance_is_explicit_not_treated_as_verified():
    errors = []
    record = {"source_provenance": {
        "provenance_status": "missing",
        "source_ids": [],
        "edition_ids": [],
        "citation_locations": [],
        "rights_status": "not_assessed",
        "automated_validation_status": "structural_only",
    }}
    VALIDATOR.check_source_provenance(record, "sample", errors)
    assert errors == []


def test_traceable_provenance_requires_source_edition_citation_and_cleared_rights():
    errors = []
    record = {"source_provenance": {
        "provenance_status": "traceable",
        "source_ids": ["rigveda"],
        "edition_ids": ["edition-1"],
        "citation_locations": ["mandala-1/hymn-1/verse-1"],
        "rights_status": "not_assessed",
        "automated_validation_status": "structural_only",
    }}
    VALIDATOR.check_source_provenance(record, "sample", errors)
    assert any("traceable provenance requires rights_status=cleared" in item for item in errors)


def test_human_review_flag_is_not_accepted_as_a_required_gate():
    errors = []
    VALIDATOR.check_records([{"id": "x", "title": "y", "review_required": True}],
                            "sample", errors, ("title",))
    assert any("human review flags are not publication gates" in item for item in errors)
