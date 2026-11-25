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
