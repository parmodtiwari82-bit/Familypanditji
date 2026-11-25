#!/usr/bin/env python3
"""Validate passage records against the registered work and exact edition."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "scripture_source_registry.json"
PASSAGES_PATH = ROOT / "data" / "scripture_passages.json"
SAFE_RIGHTS = {"public_domain", "open_licence", "permission_granted"}
RIGHTS = SAFE_RIGHTS | {"unknown", "restricted", "not_for_redistribution"}
LOCATOR_KINDS = {"kanda","mandala","ashtaka","adhyaya","sarga","skandha","chapter","section","hymn","sukta","verse","mantra","pada","folio","page","other"}


def validate_passages(registry, manifest):
    errors = []
    if not isinstance(registry, dict) or not isinstance(manifest, dict):
        return ["registry and passage manifest must be objects"]
    sources = registry.get("sources", [])
    editions = registry.get("editions", [])
    passages = manifest.get("passages")
    if not isinstance(sources, list) or not isinstance(editions, list):
        return ["registry sources and editions must be arrays"]
    if not isinstance(passages, list):
        return ["passages must be an array"]
    source_map = {x.get("source_id"): x for x in sources if isinstance(x, dict) and isinstance(x.get("source_id"), str)}
    edition_map = {x.get("edition_id"): x for x in editions if isinstance(x, dict) and isinstance(x.get("edition_id"), str)}
    seen = set()
    for i, passage in enumerate(passages):
        label = f"passages[{i}]"
        if not isinstance(passage, dict):
            errors.append(f"{label} must be an object")
            continue
        pid = passage.get("passage_id")
        if not isinstance(pid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", pid):
            errors.append(f"{label}: invalid passage_id")
        elif pid in seen:
            errors.append(f"{label}: duplicate passage_id")
        seen.add(pid)
        source = source_map.get(passage.get("source_id"))
        edition = edition_map.get(passage.get("edition_id"))
        if source is None:
            errors.append(f"{label}: source_id does not resolve")
        if edition is None:
            errors.append(f"{label}: edition_id does not resolve")
        elif edition.get("source_id") != passage.get("source_id"):
            errors.append(f"{label}: edition does not belong to passage source")
        if source is not None and source.get("rights_status") not in SAFE_RIGHTS:
            errors.append(f"{label}: source rights are not cleared for text ingestion")
        if edition is not None and edition.get("rights_status") not in SAFE_RIGHTS:
            errors.append(f"{label}: edition rights are not cleared for text ingestion")
        if edition is not None and not str(edition.get("rights_evidence", "")).strip():
            errors.append(f"{label}: edition rights evidence is missing")
        for key in ("language", "script", "original_text"):
            if not isinstance(passage.get(key), str) or not passage[key].strip():
                errors.append(f"{label}: {key} must be non-empty")
        locator = passage.get("locator")
        if not isinstance(locator, list) or not locator:
            errors.append(f"{label}: locator must contain at least one edition-native component")
        else:
            for n, part in enumerate(locator):
                if not isinstance(part, dict) or part.get("kind") not in LOCATOR_KINDS or not isinstance(part.get("value"), str) or not part["value"].strip():
                    errors.append(f"{label}: locator[{n}] requires a supported kind and non-empty value")
        transcription = passage.get("transcription")
        if not isinstance(transcription, dict):
            errors.append(f"{label}: transcription metadata is required")
        else:
            if transcription.get("method") not in {"human_transcription","ocr","born_digital","unknown"}:
                errors.append(f"{label}: invalid transcription method")
            if transcription.get("status") not in {"unreviewed","machine_checked","automated_validated","manually_corrected"}:
                errors.append(f"{label}: invalid transcription status")
            confidence = transcription.get("confidence")
            if confidence is not None and (not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1):
                errors.append(f"{label}: confidence must be between 0 and 1")
            if transcription.get("method") == "ocr" and confidence is None:
                errors.append(f"{label}: OCR transcription requires confidence")
        translations = passage.get("translations", [])
        if not isinstance(translations, list):
            errors.append(f"{label}: translations must be an array")
        else:
            for n, translation in enumerate(translations):
                tlabel = f"{label}: translations[{n}]"
                if not isinstance(translation, dict):
                    errors.append(f"{tlabel} must be an object")
                    continue
                for key in ("translation_id", "language", "text", "translator_or_source"):
                    if not isinstance(translation.get(key), str) or not translation[key].strip():
                        errors.append(f"{tlabel}: {key} must be non-empty")
                rights = translation.get("rights_status", "unknown")
                if rights not in RIGHTS:
                    errors.append(f"{tlabel}: invalid rights_status")
                if rights in SAFE_RIGHTS and not str(translation.get("rights_evidence", "")).strip():
                    errors.append(f"{tlabel}: rights evidence is required")
    if manifest.get("status") == "empty_scaffold" and passages:
        errors.append("empty_scaffold requires an empty passages array")
    if manifest.get("status") not in {"empty_scaffold","candidate_passages","ingestion_in_progress"}:
        errors.append("invalid passage manifest status")
    if manifest.get("status") == "candidate_passages" and not passages:
        errors.append("candidate_passages requires at least one passage")
    return errors


def load_and_validate():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(PASSAGES_PATH.read_text(encoding="utf-8"))
    return validate_passages(registry, manifest)


def main():
    try:
        errors = load_and_validate()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read scripture passage data: {exc}")
        return 1
    if errors:
        print("Scripture passage validation failed:")
        print("\\n".join(f"- {error}" for error in errors))
        return 1
    print("Scripture passage manifest validation passed (metadata integrity only).")
    print("No claim is made about textual authenticity, translation accuracy, or rights beyond recorded evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
