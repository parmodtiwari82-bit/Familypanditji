#!/usr/bin/env python3
"""Verify scripture artifact bytes, provenance and rights-safe eligibility.

This checks byte integrity and metadata gates only; it cannot establish textual
authenticity, OCR correctness, religious correctness or legal rights itself.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/scripture_ingestion_manifest.json"
REGISTRY = ROOT / "data/scripture_source_registry.json"
CATALOGUE = ROOT / "data/scripture_passages.json"
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
ELIGIBLE_RIGHTS = {"public_domain", "open_licence", "permission_granted"}
TEXT_READY = {"digitized", "transcribed", "ocr_complete"}


def _safe_artifact_path(storage_ref, root):
    if not isinstance(storage_ref, str) or not storage_ref.strip():
        raise ValueError("storage_ref must be a non-empty repository-relative path")
    candidate = Path(storage_ref)
    if candidate.is_absolute() or candidate.as_posix().startswith(("..", "./")):
        raise ValueError("storage_ref must be a repository-relative path inside the repository")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError("storage_ref escapes repository root")
    return resolved


def validate_artifact_files(manifest, registry, catalogue, root):
    errors = []
    artifacts = manifest.get("artifacts", []) if isinstance(manifest, dict) else []
    sources = {x.get("source_id"): x for x in registry.get("sources", []) if isinstance(x, dict)}
    editions = {x.get("edition_id"): x for x in registry.get("editions", []) if isinstance(x, dict)}
    artifact_ids = set()
    for index, item in enumerate(artifacts):
        label = f"artifacts[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label}: record must be an object")
            continue
        aid = item.get("artifact_id")
        if not isinstance(aid, str) or not aid or aid in artifact_ids:
            errors.append(f"{label}: artifact_id must be unique and non-empty")
        artifact_ids.add(aid)
        source = sources.get(item.get("source_id"))
        edition = editions.get(item.get("edition_id"))
        if not source or not edition or edition.get("source_id") != item.get("source_id"):
            errors.append(f"{label}: source/edition provenance does not resolve")
        else:
            if source.get("rights_status") not in ELIGIBLE_RIGHTS:
                errors.append(f"{label}: source rights are not cleared for ingestion")
            if edition.get("rights_status") not in ELIGIBLE_RIGHTS:
                errors.append(f"{label}: edition rights are not cleared for ingestion")
            if edition.get("text_status") not in TEXT_READY:
                errors.append(f"{label}: edition text is not marked digitized/transcribed/OCR-complete")
        digest = item.get("sha256")
        if not isinstance(digest, str) or not HEX_SHA256.fullmatch(digest):
            errors.append(f"{label}: invalid SHA-256")
            continue
        try:
            path = _safe_artifact_path(item.get("storage_ref"), root)
            if not path.is_file():
                errors.append(f"{label}: artifact file does not exist")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != digest:
                errors.append(f"{label}: SHA-256 does not match artifact bytes")
        except (OSError, ValueError) as exc:
            errors.append(f"{label}: {exc}")
    for index, passage in enumerate(catalogue.get("passages", []) if isinstance(catalogue, dict) else []):
        if not isinstance(passage, dict) or passage.get("artifact_id") not in artifact_ids:
            errors.append(f"passages[{index}]: artifact_id does not resolve")
    return errors


def main():
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read scripture artifact inputs: {exc}")
        return 1
    errors = validate_artifact_files(manifest, registry, catalogue, ROOT)
    if errors:
        print("Scripture artifact integrity validation failed:")
        print("\\n".join(f"- {error}" for error in errors))
        return 1
    print("Scripture artifact integrity validation passed (rights gates, byte checksums and references).")
    print("No claim is made about authenticity, OCR correctness or religious accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
