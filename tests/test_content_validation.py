from scripts.validate_content import check_temple_records, validate


def test_all_content_catalogues_pass_structural_validation():
    assert validate() == []


def test_temple_catalogue_requires_https_source_links_and_iso_review_date():
    errors = []
    check_temple_records([{
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


def test_temple_catalogue_rejects_duplicate_ids_and_missing_provenance():
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
    check_temple_records([record, record], errors)
    assert any("duplicate id 'same-temple'" in item for item in errors)
