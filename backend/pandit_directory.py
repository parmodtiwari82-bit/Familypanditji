"""Private, admin-managed Pandit profile registry.

Only profiles with an explicit platform review decision are returned publicly.
This module does not implement bookings, payments, identity-provider checks or
independent government certification.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _connect(database: Path) -> sqlite3.Connection:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS pandit_profiles (
            profile_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            country TEXT NOT NULL,
            service_categories_json TEXT NOT NULL,
            languages_json TEXT NOT NULL,
            tradition TEXT NOT NULL,
            biography TEXT NOT NULL,
            qualification_summary TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending_review','verified','suspended')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            verified_at TEXT,
            verifier_name TEXT,
            verifier_qualification TEXT,
            verification_method TEXT,
            evidence_reference TEXT,
            review_notes TEXT
        )"""
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_pandit_public_search ON pandit_profiles(status, city, state)"
    )
    return connection


def _public_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "profile_id": row["profile_id"],
        "display_name": row["display_name"],
        "city": row["city"],
        "state": row["state"],
        "country": row["country"],
        "service_categories": json.loads(row["service_categories_json"]),
        "languages": json.loads(row["languages_json"]),
        "tradition": row["tradition"],
        "biography": row["biography"],
        "qualification_summary": row["qualification_summary"],
        "directory_status": "platform_reviewed_profile",
        "verification_scope": "Profile details and submitted qualification evidence reviewed by platform staff; not government certification or a guarantee of service quality.",
        "verified_at": row["verified_at"],
    }


def create_pending_profile(database: Path, profile: dict[str, Any]) -> dict[str, Any]:
    profile_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with _connect(database) as connection:
        connection.execute(
            """INSERT INTO pandit_profiles (
                profile_id, display_name, city, state, country,
                service_categories_json, languages_json, tradition, biography,
                qualification_summary, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_review', ?, ?)""",
            (
                profile_id, profile["display_name"], profile["city"], profile["state"],
                profile["country"], json.dumps(profile["service_categories"], ensure_ascii=False),
                json.dumps(profile["languages"], ensure_ascii=False), profile["tradition"],
                profile["biography"], profile["qualification_summary"], now, now,
            ),
        )
    return {"profile_id": profile_id, "status": "pending_review"}


def verify_profile(database: Path, profile_id: str, review: dict[str, str]) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(database) as connection:
        cursor = connection.execute(
            """UPDATE pandit_profiles SET status='verified', updated_at=?, verified_at=?,
                verifier_name=?, verifier_qualification=?, verification_method=?,
                evidence_reference=?, review_notes=?
            WHERE profile_id=? AND status='pending_review'""",
            (
                now, now, review["reviewer_name"], review["reviewer_qualification"],
                review["verification_method"], review["evidence_reference"],
                review["review_notes"], profile_id,
            ),
        )
        return cursor.rowcount == 1


def suspend_profile(database: Path, profile_id: str, reason: str) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(database) as connection:
        cursor = connection.execute(
            """UPDATE pandit_profiles SET status='suspended', updated_at=?, review_notes=?
            WHERE profile_id=? AND status='verified'""",
            (now, reason, profile_id),
        )
        return cursor.rowcount == 1


def list_verified_profiles(database: Path, city: str | None = None,
                           state: str | None = None, service: str | None = None,
                           language: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    clauses = ["status='verified'"]
    params: list[Any] = []
    if city:
        clauses.append("lower(city)=lower(?)")
        params.append(city.strip())
    if state:
        clauses.append("lower(state)=lower(?)")
        params.append(state.strip())
    query = "SELECT * FROM pandit_profiles WHERE " + " AND ".join(clauses) + " ORDER BY display_name COLLATE NOCASE LIMIT ?"
    params.append(limit)
    with _connect(database) as connection:
        rows = connection.execute(query, params).fetchall()
    records = [_public_record(row) for row in rows]
    if service:
        wanted = service.casefold().strip()
        records = [item for item in records if any(wanted == x.casefold() for x in item["service_categories"])]
    if language:
        wanted = language.casefold().strip()
        records = [item for item in records if any(wanted == x.casefold() for x in item["languages"])]
    return records


def get_profile_status(database: Path, profile_id: str) -> dict[str, Any] | None:
    with _connect(database) as connection:
        row = connection.execute(
            "SELECT profile_id, status, created_at, updated_at, verified_at FROM pandit_profiles WHERE profile_id=?",
            (profile_id,),
        ).fetchone()
    return dict(row) if row else None
