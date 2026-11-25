"""Edition-aware citation lookup for the curated scripture passage manifest."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CitationNotFound(LookupError):
    """Raised when a passage identifier is not present in the curated corpus."""


def resolve_citation(passage_id, manifest_path=None, registry_path=None):
    manifest_path = Path(manifest_path or ROOT / "data" / "scripture_passages.json")
    registry_path = Path(registry_path or ROOT / "data" / "scripture_source_registry.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    matches = [p for p in manifest.get("passages", []) if p.get("passage_id") == passage_id]
    if not matches:
        raise CitationNotFound(f"No registered passage found for {passage_id!r}")
    passage = matches[0]
    source = next((s for s in registry.get("sources", []) if s.get("source_id") == passage["source_id"]), None)
    edition = next((e for e in registry.get("editions", []) if e.get("edition_id") == passage["edition_id"]), None)
    if source is None or edition is None or edition.get("source_id") != passage["source_id"]:
        raise CitationNotFound(f"Passage {passage_id!r} has unresolved source or edition metadata")
    location = " / ".join(f"{part['kind']} {part['value']}" for part in passage["locator"])
    return {
        "passage_id": passage["passage_id"],
        "work_title": source["work_title"],
        "edition": edition["edition_label"],
        "publisher_or_repository": edition["publisher_or_repository"],
        "location": location,
        "language": passage["language"],
        "script": passage["script"],
        "original_text": passage["original_text"],
        "translations": passage.get("translations", []),
        "citation_status": "edition_linked"
    }
