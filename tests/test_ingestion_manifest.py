import importlib.util

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ingestion_manifest", ROOT / "scripts" / "validate_ingestion_manifest.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_empty_manifest_is_valid():
    assert VALIDATOR.validate_manifest({"manifest_version":"1.0.0","artifacts":[]},{"sources":[],"editions":[]}) == []


def test_artifact_requires_registered_source_and_edition():
    item = {"artifact_id":"a1","source_id":"missing","edition_id":"missing"}
    errors = VALIDATOR.validate_manifest({"manifest_version":"1.0.0","artifacts":[item]},{"sources":[],"editions":[]})
    assert any("source_id does not resolve" in e for e in errors)
    assert any("edition_id does not resolve" in e for e in errors)


def test_ocr_requires_confidence_and_sha256_format():
    source = {"source_id":"work.one","rights_status":"public_domain","ingestion_status":"metadata_only"}
    edition = {"edition_id":"work.one.ed1","source_id":"work.one","rights_status":"public_domain"}
    item = {"artifact_id":"a1","source_id":"work.one","edition_id":"work.one.ed1","artifact_type":"ocr_output",
        "storage_ref":"repo://artifact/a1","acquired_at":"2026-01-01T00:00:00Z","acquisition_method":"licensed download",
        "sha256":"bad","extraction_method":"ocr","extraction_tool":"tesseract","extraction_tool_version":"5",
        "language":"sa","script":"Devanagari","structural_location":"kanda 1 / sukta 1"}
    errors = VALIDATOR.validate_manifest({"manifest_version":"1.0.0","artifacts":[item]},{"sources":[source],"editions":[edition]})
    assert any("sha256" in e for e in errors)
    assert any("OCR requires ocr_confidence" in e for e in errors)


def test_restricted_edition_blocks_artifact_ingestion():
    source = {"source_id":"work.one","rights_status":"public_domain","ingestion_status":"metadata_only"}
    edition = {"edition_id":"work.one.ed1","source_id":"work.one","rights_status":"unknown"}
    item = {"artifact_id":"a1","source_id":"work.one","edition_id":"work.one.ed1"}
    errors = VALIDATOR.validate_manifest({"manifest_version":"1.0.0","artifacts":[item]},{"sources":[source],"editions":[edition]})
    assert any("edition rights do not permit ingestion" in e for e in errors)
