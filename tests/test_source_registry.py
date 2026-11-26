import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("source_registry", ROOT / "scripts" / "validate_source_registry.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_empty_registry_scaffold_is_valid():
    data = json.loads((ROOT / "data" / "scripture_source_registry.json").read_text(encoding="utf-8"))
    assert data["sources"] == [] and data["editions"] == []
    assert VALIDATOR.validate_registry(data) == []


def test_text_ingestion_requires_eligible_rights():
    data = {"registry_version":"1","status":"candidate_sources","sources":[{
        "source_id":"sample.work","work_title":"Sample","tradition":"Indic","language":"sa",
        "script":"Devanagari","source_type":"primary_text","access_status":"accessible",
        "rights_status":"unknown","rights_evidence":"","ingestion_status":"text_ingested"
    }],"editions":[]}
    assert any("text_ingested requires" in e for e in VALIDATOR.validate_registry(data))


def test_edition_must_resolve_to_registered_source():
    data = {"registry_version":"1","status":"candidate_sources","sources":[],"editions":[{
        "edition_id":"sample.ed1","source_id":"missing.source","edition_label":"Edition 1",
        "publisher_or_repository":"Repository","publication_year":None,"language":"sa",
        "text_status":"metadata_only","rights_status":"unknown","rights_evidence":""
    }]}
    assert any("source_id does not resolve" in e for e in VALIDATOR.validate_registry(data))


def test_rights_clearance_requires_evidence():
    data = {"registry_version":"1","status":"candidate_sources","sources":[{
        "source_id":"sample.work","work_title":"Sample","tradition":"Indic","language":"sa",
        "script":"Devanagari","source_type":"primary_text","access_status":"accessible",
        "rights_status":"public_domain","rights_evidence":"","ingestion_status":"metadata_only"
    }],"editions":[]}
    assert any("cleared/open rights require rights_evidence" in e for e in VALIDATOR.validate_registry(data))


def test_ingestion_ready_rejects_unknown_rights():
    source = {"source_id":"sample.work","work_title":"Sample","tradition":"Indic","language":"sa",
        "script":"Devanagari","source_type":"primary_text","access_status":"accessible",
        "rights_status":"unknown","rights_evidence":"","ingestion_status":"metadata_only"}
    edition = {"edition_id":"sample.ed1","source_id":"sample.work","edition_label":"Edition 1",
        "publisher_or_repository":"Repository","publication_year":None,"language":"sa",
        "text_status":"metadata_only","rights_status":"unknown","rights_evidence":""}
    errors = VALIDATOR.validate_registry({"registry_version":"1","status":"ingestion_ready","sources":[source],"editions":[edition]})
    assert any("cannot include sources" in e for e in errors)
    assert any("cannot include editions" in e for e in errors)

def test_first_candidate_is_edition_specific_and_rights_evidenced_but_not_ingested():
    data = json.loads((ROOT / "data" / "scripture_source_registry.json").read_text(encoding="utf-8"))
    assert data["status"] == "candidate_sources"
    assert len(data["sources"]) == len(data["editions"]) == 1
    source = data["sources"][0]
    edition = data["editions"][0]
    assert source["source_id"] == edition["source_id"]
    assert source["rights_status"] == edition["rights_status"] == "open_licence"
    assert "CC BY-SA 4.0" in source["rights_evidence"]
    assert "oldid=407843" in edition["rights_evidence"]
    assert source["ingestion_status"] == "metadata_only"
    assert edition["text_status"] == "metadata_only"
    assert VALIDATOR.validate_registry(data) == []
