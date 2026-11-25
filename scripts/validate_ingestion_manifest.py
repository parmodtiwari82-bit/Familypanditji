#!/usr/bin/env python3
"""Validate provenance for each acquired/transcribed scripture artifact."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "scripture_source_registry.json"
MANIFEST = ROOT / "data" / "scripture_ingestion_manifest.json"
SAFE_RIGHTS = {"public_domain", "open_licence", "permission_granted"}
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate_manifest(manifest, registry):
    errors = []
    if not isinstance(manifest, dict):
        return ["manifest root must be an object"]
    if manifest.get("manifest_version") != "1.0.0":
        errors.append("manifest_version must be 1.0.0")
    records = manifest.get("artifacts")
    if not isinstance(records, list):
        return errors + ["artifacts must be an array"]
    sources = {x.get("source_id"): x for x in registry.get("sources", []) if isinstance(x, dict)}
    editions = {x.get("edition_id"): x for x in registry.get("editions", []) if isinstance(x, dict)}
    seen = set()
    for i, item in enumerate(records):
        label = f"artifacts[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        artifact_id = item.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id.strip() or artifact_id in seen:
            errors.append(f"{label}: artifact_id must be non-empty and unique")
        seen.add(artifact_id)
        source = sources.get(item.get("source_id"))
        edition = editions.get(item.get("edition_id"))
        if source is None:
            errors.append(f"{label}: source_id does not resolve")
        if edition is None:
            errors.append(f"{label}: edition_id does not resolve")
        elif edition.get("source_id") != item.get("source_id"):
            errors.append(f"{label}: edition does not belong to source")
        if source and (source.get("rights_status") not in SAFE_RIGHTS or source.get("ingestion_status") == "blocked"):
            errors.append(f"{label}: source rights/status do not permit ingestion")
        if edition and edition.get("rights_status") not in SAFE_RIGHTS:
            errors.append(f"{label}: edition rights do not permit ingestion")
        for key in ("artifact_type", "storage_ref", "acquired_at", "acquisition_method", "sha256", "extraction_method", "extraction_tool", "extraction_tool_version", "language", "script", "structural_location"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{label}: {key} must be non-empty")
        if isinstance(item.get("sha256"), str) and not HEX_SHA256.fullmatch(item["sha256"]):
            errors.append(f"{label}: sha256 must be 64 lowercase hexadecimal characters")
        acquired = item.get("acquired_at")
        if isinstance(acquired, str) and acquired:
            try:
                datetime.fromisoformat(acquired.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{label}: acquired_at must be ISO-8601")
        confidence = item.get("ocr_confidence")
        if confidence is not None and (not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1):
            errors.append(f"{label}: ocr_confidence must be between 0 and 1")
        if item.get("extraction_method") == "ocr" and confidence is None:
            errors.append(f"{label}: OCR requires ocr_confidence")
    return errors


def main():
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read ingestion inputs: {exc}")
        return 1
    errors = validate_manifest(manifest, registry)
    if errors:
        print("Scripture ingestion manifest validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Scripture ingestion manifest validation passed (provenance metadata only).")
    print("Checksums are format-checked, not recomputed; no authenticity or rights claim is made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
