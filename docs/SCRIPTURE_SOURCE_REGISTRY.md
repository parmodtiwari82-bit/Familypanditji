# Scripture Source Registry and Ingestion Policy

## Purpose
The registry separates a canonical work from a specific edition or repository copy. This prevents citations from silently mixing recensions, translations, or page numbering.

## Registry files
- `schemas/scripture-source-registry.schema.json`: machine-readable metadata contract.
- `data/scripture_source_registry.json`: current registry manifest.
- `scripts/validate_source_registry.py`: referential-integrity and conservative rights-policy checks.
- `tests/test_source_registry.py`: regression cases for empty state, rights evidence, source-to-edition links, and blocked ingestion.

## Required source metadata
Each source record identifies the work, tradition, language, script, source type, access state, rights state/evidence, and ingestion state. Each edition record identifies its parent source, edition label, publisher/repository, language, publication year or explicit null, text status, and rights evidence.

## Safe ingestion sequence
1. Identify a candidate source and record its stable source ID. Do not infer rights from a public URL.
2. Identify the exact edition, publisher/repository, publication details, and stable catalogue identifier where available.
3. Record rights evidence for that edition. Unknown or restricted rights block digitization/transcription for public redistribution.
4. Acquire only material whose reuse rights permit the intended operation. Preserve checksums, acquisition date, file provenance, and licence conditions in the ingestion record.
5. Record OCR/transcription tool and version, confidence, language/script checks, and the edition-native structural location for each passage.
6. Resolve every emitted citation to an ingested edition and exact location before allowing a scripture-specific claim to be labelled source-backed.

## Current state
The manifest is intentionally empty. No source edition, public-domain status, open licence, permission, or digitized scripture text has yet been asserted by this change. This is a safe foundation, not a completed scripture corpus. The validator passing means only that the manifest is internally consistent; it does not establish legal rights, source authenticity, or religious correctness.

## Expansion rule
A candidate can enter the registry with unknown rights, but it cannot become ingestion-ready or be marked text-ingested until the required rights evidence is recorded. Never change a record to cleared merely to make a test pass.

## Edition-aware citation resolver (implemented foundation)

- `data/scripture_passages.json` stores passage records separately from source and edition metadata.
- `schemas/scripture-passage-catalogue.schema.json` defines the passage record shape.
- `backend/scripture_citations.py` resolves a passage only when its source, edition and acquired artifact IDs all resolve, source/edition rights are eligible, the artifact belongs to that exact edition, and extraction confidence is at least 0.90.
- `GET /api/scripture/search?q=...` exposes resolved passage matches.
- `POST /api/ask` now returns a structured `scripture_citations` array. When no AI provider is configured but a passage resolves, it returns the retrieved original passage with its edition-specific citation. Draft catalogue answers remain explicitly unverified when no passage resolves.
- The passage catalogue is intentionally empty today. Therefore search currently returns `source_not_found`; this implementation does not create a scripture corpus or fabricate a verse citation.

Automated resolver tests cover an empty corpus, edition-specific resolution, unknown/restricted rights, low OCR confidence, mismatched artifact editions and incomplete query matches. The 0.90 confidence threshold is a conservative product rule, not proof that OCR text is correct. Rights metadata validation is not legal advice or proof of authenticity.

## First candidate source: Bhagavad Gita Sanskrit Wikisource

The registry now contains one **candidate digital transcription**, not an ingested corpus:
- Work: भगवद्गीता, original Sanskrit base text.
- Digital edition: Sanskrit Wikisource page, stable revision `oldid=407843` (page revision dated 2025-03-24).
- Page footer states CC BY-SA; reuse requires attribution, a link to the licence, indication of changes, and ShareAlike for adaptations.
- Scope is restricted to the base Sanskrit verse text. Commentaries, translations, introductions and other page material are excluded from this source record.
- This is a community digital transcription, not a named print edition or critical edition. Its textual accuracy has not yet been independently cross-checked.

The source and edition remain `metadata_only`; no artifact or passage has been acquired. The next step is to obtain the exact machine-readable verse text from this revision, record the acquisition and checksum, retain chapter/verse locations, and run automated structure and text-integrity checks before creating passage records. No source-grounded answer may cite it until those steps complete.
