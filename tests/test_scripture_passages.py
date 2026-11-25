import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

VALIDATOR = load("passage_validator", ROOT / "scripts" / "validate_scripture_passages.py")
RESOLVER = load("scripture_citations", ROOT / "backend" / "scripture_citations.py")


def test_empty_passage_manifest_is_valid():
    registry = json.loads((ROOT / "data" / "scripture_source_registry.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "scripture_passages.json").read_text(encoding="utf-8"))
    assert manifest["passages"] == []
    assert VALIDATOR.validate_passages(registry, manifest) == []


def test_passage_requires_resolvable_source_and_edition():
    passage = {"passage_id":"sample.1","source_id":"missing","edition_id":"missing.ed",
      "locator":[{"kind":"verse","value":"1"}],"language":"sa","script":"Devanagari",
      "original_text":"text","transcription":{"method":"ocr","status":"unreviewed","confidence":0.7}}
    errors = VALIDATOR.validate_passages({"sources":[],"editions":[]},{"status":"candidate_passages","passages":[passage]})
    assert any("source_id does not resolve" in e for e in errors)
    assert any("edition_id does not resolve" in e for e in errors)


def test_ocr_requires_confidence_and_exact_locator():
    source = {"source_id":"work.one","rights_status":"public_domain"}
    edition = {"edition_id":"work.ed1","source_id":"work.one","rights_status":"public_domain","rights_evidence":"catalogue rights statement","edition_label":"Edition 1","publisher_or_repository":"Archive"}
    passage = {"passage_id":"work.1","source_id":"work.one","edition_id":"work.ed1",
      "locator":[],"language":"sa","script":"Devanagari","original_text":"text",
      "transcription":{"method":"ocr","status":"unreviewed"}}
    errors = VALIDATOR.validate_passages({"sources":[source],"editions":[edition]},{"status":"candidate_passages","passages":[passage]})
    assert any("locator must contain" in e for e in errors)
    assert any("OCR transcription requires confidence" in e for e in errors)


def test_translation_must_identify_its_translator_or_source():
    source = {"source_id":"work.one","rights_status":"public_domain"}
    edition = {"edition_id":"work.ed1","source_id":"work.one","rights_status":"public_domain","rights_evidence":"rights evidence","edition_label":"Edition 1","publisher_or_repository":"Archive"}
    passage = {"passage_id":"work.1","source_id":"work.one","edition_id":"work.ed1",
      "locator":[{"kind":"verse","value":"1"}],"language":"sa","script":"Devanagari","original_text":"text",
      "transcription":{"method":"born_digital","status":"unreviewed"},
      "translations":[{"translation_id":"en1","language":"en","text":"translation","translator_or_source":""}]}
    errors = VALIDATOR.validate_passages({"sources":[source],"editions":[edition]},{"status":"candidate_passages","passages":[passage]})
    assert any("translator_or_source must be non-empty" in e for e in errors)


def test_missing_citation_returns_explicit_not_found():
    with pytest.raises(RESOLVER.CitationNotFound):
        RESOLVER.resolve_citation("not-in-corpus")
