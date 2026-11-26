import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scripture_citations", ROOT / "backend" / "scripture_citations.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture(rights="public_domain", confidence=0.99):
    registry = {
        "sources": [{"source_id":"gita.work","work_title":"Bhagavad Gita",
                     "script":"Devanagari","rights_status":rights,"rights_evidence":"CC BY-SA 4.0","ingestion_status":"text_ingested"}],
        "editions": [{"edition_id":"gita.edition1","source_id":"gita.work",
                      "edition_label":"Test edition","publisher_or_repository":"Test archive",
                      "language":"sa","rights_status":rights,"text_status":"transcribed","rights_evidence":"CC BY-SA 4.0"}]
    }
    manifest = {"artifacts":[{"artifact_id":"gita.artifact1","source_id":"gita.work",
                              "edition_id":"gita.edition1","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]}
    catalogue = {"passages":[{"passage_id":"gita.2.47","source_id":"gita.work",
        "edition_id":"gita.edition1","artifact_id":"gita.artifact1",
        "work_title":"Bhagavad Gita","location":"अध्याय 2, श्लोक 47",
        "text_original":"कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
        "language":"sa","script":"Devanagari","extraction_confidence":confidence,
        "keywords":"कर्म फल"}]}
    return registry, manifest, catalogue


def test_empty_corpus_returns_no_citations():
    assert MODULE.resolve_passages("कर्म", {"sources":[],"editions":[]},
                                   {"artifacts":[]}, {"passages":[]}) == []


def test_resolves_edition_specific_passage_and_location():
    r, m, c = fixture()
    found = MODULE.resolve_passages("कर्म फल", r, m, c)
    assert len(found) == 1
    assert found[0]["passage_id"] == "gita.2.47"
    assert found[0]["edition_id"] == "gita.edition1"
    assert found[0]["location"] == "अध्याय 2, श्लोक 47"
    assert found[0]["citation_status"] == "citation_resolved"


def test_unknown_or_restricted_rights_never_return_citations():
    r, m, c = fixture("unknown")
    assert MODULE.resolve_passages("कर्म फल", r, m, c) == []


def test_low_confidence_extraction_never_returns_exact_citation():
    r, m, c = fixture(confidence=0.75)
    assert MODULE.resolve_passages("कर्म फल", r, m, c) == []


def test_artifact_must_match_source_and_edition():
    r, m, c = fixture()
    m["artifacts"][0]["edition_id"] = "different.edition"
    assert MODULE.resolve_passages("कर्म फल", r, m, c) == []


def test_query_requires_all_terms_to_match():
    r, m, c = fixture()
    assert MODULE.resolve_passages("कर्म मोक्ष", r, m, c) == []

def test_missing_extraction_confidence_is_not_assumed_perfect():
    r, m, c = fixture()
    del c["passages"][0]["extraction_confidence"]
    assert MODULE.resolve_passages("कर्म फल", r, m, c) == []


def test_metadata_only_source_cannot_be_cited():
    r, m, c = fixture()
    r["sources"][0]["ingestion_status"] = "metadata_only"
    assert MODULE.resolve_passages("कर्म फल", r, m, c) == []


def test_missing_artifact_checksum_or_rights_evidence_blocks_citation():
    r, m, c = fixture()
    del m["artifacts"][0]["sha256"]
    assert MODULE.resolve_passages("कर्म फल", r, m, c) == []
    r, m, c = fixture()
    r["editions"][0]["rights_evidence"] = ""
    assert MODULE.resolve_passages("कर्म फल", r, m, c) == []
