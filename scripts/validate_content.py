#!/usr/bin/env python3
"""Validate catalogue structure and publication-safety metadata.

This checks structural integrity only. It does not verify scripture, translations,
ritual correctness, temple operating hours, reviewer identity, or source accuracy.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FILES = (
    "knowledge_hi.json",
    "puja_guides.json",
    "samskaras.json",
    "ecosystem_modules.json",
    "pandit_directory.json",
    "temples.json",
)


def load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: cannot read valid JSON ({exc})")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path.relative_to(ROOT)}: root must be a JSON object")
        return None
    return value


def check_records(records: Any, label: str, errors: list[str], required: tuple[str, ...], require_review: bool = True) -> None:
    if not isinstance(records, list):
        errors.append(f"{label}: expected an array")
        return
    seen: set[str] = set()
    for index, record in enumerate(records):
        where = f"{label}[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{where}: expected an object")
            continue
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"{where}: missing non-empty id")
        elif record_id in seen:
            errors.append(f"{where}: duplicate id {record_id!r}")
        else:
            seen.add(record_id)
        for key in required:
            value = record.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}: missing non-empty {key}")
        if require_review and record.get("review_required") is not True:
            errors.append(f"{where}: starter content must retain review_required=true")


def check_temple_records(records: Any, errors: list[str]) -> None:
    """Require traceable source metadata without claiming current operating details."""
    required = (
        "name_hi", "name_en", "deity", "city", "state", "country", "address",
        "official_website", "official_information_url", "source_status", "last_checked_on",
    )
    check_records(records, "temples.temples", errors, required, require_review=False)
    if not isinstance(records, list):
        return
    for index, temple in enumerate(records):
        if not isinstance(temple, dict):
            continue
        where = f"temples.temples[{index}]"
        for key in ("official_website", "official_information_url"):
            value = temple.get(key)
            parsed = urlparse(value) if isinstance(value, str) else None
            if parsed is None or parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{where}: {key} must be an absolute HTTPS URL")
        checked = temple.get("last_checked_on")
        try:
            date.fromisoformat(checked)
        except (TypeError, ValueError):
            errors.append(f"{where}: last_checked_on must be an ISO date (YYYY-MM-DD)")


def validate() -> list[str]:
    errors: list[str] = []
    catalogues = {name: load_json(DATA / name, errors) for name in FILES}

    knowledge = catalogues["knowledge_hi.json"]
    if knowledge is not None:
        if knowledge.get("status") != "draft_requires_acharya_review":
            errors.append("knowledge_hi.json: starter status must remain draft_requires_acharya_review")
        if knowledge.get("language") != "hi":
            errors.append("knowledge_hi.json: language must be hi")
        check_records(knowledge.get("entries"), "knowledge_hi.entries", errors,
                      ("title", "answer", "category", "answer_en", "answer_sa"))

    puja = catalogues["puja_guides.json"]
    if puja is not None:
        if puja.get("status") != "draft_requires_acharya_review":
            errors.append("puja_guides.json: starter status must remain draft_requires_acharya_review")
        check_records(puja.get("guides"), "puja_guides.guides", errors, ("title_hi", "title_en", "summary_hi"))
        for index, guide in enumerate(puja.get("guides", []) if isinstance(puja.get("guides"), list) else []):
            if isinstance(guide, dict):
                for language in ("hi", "en"):
                    steps = guide.get(f"steps_{language}")
                    if not isinstance(steps, list) or not steps or any(not isinstance(s, str) or not s.strip() for s in steps):
                        errors.append(f"puja_guides.guides[{index}]: steps_{language} must be a non-empty list of strings")

    samskaras = catalogues["samskaras.json"]
    if samskaras is not None:
        if samskaras.get("status") != "draft_requires_acharya_review":
            errors.append("samskaras.json: starter status must remain draft_requires_acharya_review")
        records = samskaras.get("samskaras")
        check_records(records, "samskaras.samskaras", errors, ("name_hi", "name_en", "description_hi"))
        if isinstance(records, list):
            numbers = [item.get("number") for item in records if isinstance(item, dict)]
            if numbers != list(range(1, 17)):
                errors.append("samskaras.samskaras: expected exactly 16 records numbered 1 through 16 in order")

    modules = catalogues["ecosystem_modules.json"]
    if modules is not None:
        check_records(modules.get("modules"), "ecosystem_modules.modules", errors, ("name_hi", "name_en", "group", "status", "description"), require_review=False)
        if isinstance(modules.get("modules"), list):
            allowed = {"beta", "planned", "in_development", "paused", "retired"}
            for index, module in enumerate(modules["modules"]):
                if isinstance(module, dict) and module.get("status") not in allowed:
                    errors.append(f"ecosystem_modules.modules[{index}]: unknown status {module.get('status')!r}")

    pandits = catalogues["pandit_directory.json"]
    if pandits is not None:
        if not isinstance(pandits.get("pandits"), list):
            errors.append("pandit_directory.json: pandits must be an array")
        if pandits.get("status") != "directory_beta_no_booking":
            errors.append("pandit_directory.json: do not imply booking or verification is live")

    temples = catalogues["temples.json"]
    if temples is not None:
        check_temple_records(temples.get("temples"), errors)

    schema_path = ROOT / "schemas" / "content-review.schema.json"
    load_json(schema_path, errors)
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("Content catalogue validation failed:")
        for problem in problems:
            print(f"- {problem}")
        sys.exit(1)
    print(f"Content catalogue validation passed: {len(FILES)} data catalogues and review schema are structurally valid.")
    print("Note: this is not Acharya review, temple-hours verification, or religious-source verification.")
