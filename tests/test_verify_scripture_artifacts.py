import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_scripture_artifacts", ROOT / "scripts" / "verify_scripture_artifacts.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture(tmp_path):
    payload = "संस्कृत मूल पाठ".encode("utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "chapter.txt").write_bytes(payload)
    registry = {
        "sources":[{"source_id":"gita","rights_status":"open_licence"}],
        "editions":[{"edition_id":"gita.rev1","source_id":"gita",
                     "rights_status":"open_licence","text_status":"transcribed"}]
    }
    manifest = {"artifacts":[{"artifact_id":"gita.ch1","source_id":"gita","edition_id":"gita.rev1",
        "storage_ref":"data/chapter.txt","sha256":hashlib.sha256(payload).hexdigest()}]}
    catalogue = {"passages":[{"passage_id":"gita.1.1","artifact_id":"gita.ch1"}]}
    return manifest, registry, catalogue


def test_valid_artifact_checksum_and_passage_reference(tmp_path):
    m,r,c=fixture(tmp_path)
    assert MODULE.validate_artifact_files(m,r,c,tmp_path)==[]


def test_unknown_source_rights_block_artifact(tmp_path):
    m,r,c=fixture(tmp_path)
    r["sources"][0]["rights_status"]="unknown"
    assert any("source rights are not cleared" in e for e in MODULE.validate_artifact_files(m,r,c,tmp_path))


def test_unknown_edition_rights_block_artifact(tmp_path):
    m,r,c=fixture(tmp_path)
    r["editions"][0]["rights_status"]="unknown"
    assert any("edition rights are not cleared" in e for e in MODULE.validate_artifact_files(m,r,c,tmp_path))


def test_metadata_only_edition_cannot_back_artifact(tmp_path):
    m,r,c=fixture(tmp_path)
    r["editions"][0]["text_status"]="metadata_only"
    assert any("text is not marked" in e for e in MODULE.validate_artifact_files(m,r,c,tmp_path))


def test_tampered_artifact_bytes_are_rejected(tmp_path):
    m,r,c=fixture(tmp_path)
    (tmp_path/"data"/"chapter.txt").write_text("बदला हुआ पाठ",encoding="utf-8")
    assert any("SHA-256 does not match" in e for e in MODULE.validate_artifact_files(m,r,c,tmp_path))


def test_missing_artifact_is_rejected(tmp_path):
    m,r,c=fixture(tmp_path)
    (tmp_path/"data"/"chapter.txt").unlink()
    assert any("does not exist" in e for e in MODULE.validate_artifact_files(m,r,c,tmp_path))


def test_path_traversal_is_rejected(tmp_path):
    m,r,c=fixture(tmp_path)
    m["artifacts"][0]["storage_ref"]="../outside.txt"
    assert any("repository-relative" in e for e in MODULE.validate_artifact_files(m,r,c,tmp_path))


def test_passage_must_reference_registered_artifact(tmp_path):
    m,r,c=fixture(tmp_path)
    c["passages"][0]["artifact_id"]="missing"
    assert any("artifact_id does not resolve" in e for e in MODULE.validate_artifact_files(m,r,c,tmp_path))
