#!/usr/bin/env python3
"""Validate registry integrity and conservative ingestion/rights policy."""
import json, re, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "scripture_source_registry.json"
SAFE = {"public_domain", "open_licence", "permission_granted"}
RIGHTS = SAFE | {"unknown", "restricted", "not_for_redistribution"}


def validate_registry(data):
    errors = []
    if not isinstance(data, dict):
        return ["registry root must be an object"]
    sources, editions = data.get("sources"), data.get("editions")
    if not isinstance(sources, list):
        errors.append("sources must be an array")
        sources = []
    if not isinstance(editions, list):
        errors.append("editions must be an array")
        editions = []
    source_ids = set()
    for i, item in enumerate(sources):
        label = f"sources[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        sid = item.get("source_id")
        if not isinstance(sid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", sid):
            errors.append(f"{label}: invalid source_id")
        elif sid in source_ids:
            errors.append(f"{label}: duplicate source_id")
        source_ids.add(sid)
        for key in ("work_title", "tradition", "language", "script", "source_type"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{label}: {key} must be non-empty")
        rights, ingestion = item.get("rights_status"), item.get("ingestion_status")
        if rights not in RIGHTS:
            errors.append(f"{label}: invalid rights_status")
        if ingestion not in {"not_started", "metadata_only", "text_ingested", "blocked"}:
            errors.append(f"{label}: invalid ingestion_status")
        if ingestion == "text_ingested" and rights not in SAFE:
            errors.append(f"{label}: text_ingested requires an eligible rights_status")
        if rights in SAFE and not str(item.get("rights_evidence", "")).strip():
            errors.append(f"{label}: cleared/open rights require rights_evidence")
        url = item.get("access_url")
        if url is not None:
            parsed = urlparse(url) if isinstance(url, str) else None
            if parsed is None or parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{label}: access_url must be absolute HTTPS")
    edition_ids = set()
    for i, item in enumerate(editions):
        label = f"editions[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        eid = item.get("edition_id")
        if not isinstance(eid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", eid):
            errors.append(f"{label}: invalid edition_id")
        elif eid in edition_ids:
            errors.append(f"{label}: duplicate edition_id")
        edition_ids.add(eid)
        if item.get("source_id") not in source_ids:
            errors.append(f"{label}: source_id does not resolve")
        for key in ("edition_label", "publisher_or_repository", "language", "text_status"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{label}: {key} must be non-empty")
        rights = item.get("rights_status")
        if rights not in RIGHTS:
            errors.append(f"{label}: invalid rights_status")
        if rights in SAFE and not str(item.get("rights_evidence", "")).strip():
            errors.append(f"{label}: rights_evidence required")
        if item.get("text_status") in {"digitized", "transcribed", "ocr_pending", "ocr_complete"} and rights not in SAFE:
            errors.append(f"{label}: digitized text requires eligible rights status")
    status = data.get("status")
    if status not in {"empty_scaffold", "candidate_sources", "ingestion_ready", "ingestion_in_progress"}:
        errors.append("invalid registry status")
    if status == "empty_scaffold" and (sources or editions):
        errors.append("empty_scaffold requires empty sources and editions")
    if status == "candidate_sources" and not sources:
        errors.append("candidate_sources requires at least one source")
    if status == "ingestion_ready":
        if not sources or not editions:
            errors.append("ingestion_ready requires source and edition records")
        if any(x.get("rights_status") not in SAFE for x in sources if isinstance(x, dict)):
            errors.append("ingestion_ready cannot include sources without eligible rights")
        if any(x.get("rights_status") not in SAFE for x in editions if isinstance(x, dict)):
            errors.append("ingestion_ready cannot include editions without eligible rights")
    return errors


def main():
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read source registry: {exc}")
        return 1
    errors = validate_registry(data)
    if errors:
        print("Scripture source registry validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Scripture source registry validation passed (metadata integrity only).")
    print("No claim is made about textual accuracy, legal rights, or completeness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
