"""Edition-aware scripture passage lookup with strict provenance gates.

A citation is returned only when its source, edition and acquired artifact
all resolve and both source/edition rights permit the intended use.
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

SAFE_RIGHTS = {"public_domain", "open_licence", "permission_granted"}
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    value = "".join(ch if ch.isalnum() or ch.isspace()
                    or unicodedata.category(ch).startswith("M") else " "
                    for ch in value)
    return " ".join(value.split())


def resolve_passages(query: str, registry: dict[str, Any],
                     manifest: dict[str, Any],
                     catalogue: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    """Return matching passages with edition-specific citations; fail closed."""
    normalized_query = normalize_text(query)
    if not normalized_query:
        return []
    source_by_id = {x.get("source_id"): x for x in registry.get("sources", [])
                    if isinstance(x, dict)}
    edition_by_id = {x.get("edition_id"): x for x in registry.get("editions", [])
                     if isinstance(x, dict)}
    artifact_by_id = {x.get("artifact_id"): x for x in manifest.get("artifacts", [])
                      if isinstance(x, dict)}
    query_tokens = set(normalized_query.split())
    results = []
    for passage in catalogue.get("passages", []):
        if not isinstance(passage, dict):
            continue
        source = source_by_id.get(passage.get("source_id"))
        edition = edition_by_id.get(passage.get("edition_id"))
        artifact = artifact_by_id.get(passage.get("artifact_id"))
        if not source or not edition or not artifact:
            continue
        if source.get("ingestion_status") != "text_ingested":
            continue
        if edition.get("text_status") not in {"digitized", "transcribed", "ocr_complete"}:
            continue
        if not str(source.get("rights_evidence", "")).strip() or not str(edition.get("rights_evidence", "")).strip():
            continue
        if not isinstance(artifact.get("sha256"), str) or not HEX_SHA256.fullmatch(artifact["sha256"]):
            continue
        if edition.get("source_id") != source.get("source_id"):
            continue
        if artifact.get("source_id") != source.get("source_id") or artifact.get("edition_id") != edition.get("edition_id"):
            continue
        if source.get("rights_status") not in SAFE_RIGHTS or edition.get("rights_status") not in SAFE_RIGHTS:
            continue
        if source.get("ingestion_status") == "blocked":
            continue
        text = str(passage.get("text_original", "")).strip()
        location = str(passage.get("location", "")).strip()
        passage_id = str(passage.get("passage_id", "")).strip()
        if not text or not location or not passage_id:
            continue
        confidence = passage.get("extraction_confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0.0 <= confidence <= 1.0:
            continue
        if confidence < 0.90:
            continue
        haystack = normalize_text(" ".join([
            text, location, str(passage.get("work_title", "")),
            str(passage.get("keywords", "")),
        ]))
        if not query_tokens.issubset(set(haystack.split())):
            continue
        results.append({
            "passage_id": passage_id,
            "work_title": str(passage.get("work_title") or source.get("work_title")),
            "source_id": source["source_id"],
            "edition_id": edition["edition_id"],
            "edition_label": edition.get("edition_label"),
            "publisher_or_repository": edition.get("publisher_or_repository"),
            "location": location,
            "text_original": text,
            "language": passage.get("language", edition.get("language")),
            "script": passage.get("script", source.get("script")),
            "citation_status": "citation_resolved",
            "rights_status": edition.get("rights_status"),
            "extraction_confidence": confidence,
        })
        if len(results) >= max(1, min(int(limit), 20)):
            break
    return results


def load_and_resolve(query: str, root: Path, limit: int = 5) -> list[dict[str, Any]]:
    """Load the versioned source inputs; missing/invalid inputs return no evidence."""
    try:
        registry = json.loads((root / "data/scripture_source_registry.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "data/scripture_ingestion_manifest.json").read_text(encoding="utf-8"))
        catalogue = json.loads((root / "data/scripture_passages.json").read_text(encoding="utf-8"))
        if not all(isinstance(x, dict) for x in (registry, manifest, catalogue)):
            return []
        return resolve_passages(query, registry, manifest, catalogue, limit)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return []
