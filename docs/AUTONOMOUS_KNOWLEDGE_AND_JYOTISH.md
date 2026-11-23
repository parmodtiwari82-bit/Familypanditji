# Autonomous Scripture Knowledge & Jyotish Architecture

## Product principle

Family Pandit Ji is designed to operate without a mandatory Acharya, Pandit, scholar, or other human approval step. It must derive answers from traceable source material and derive horoscope outputs through documented, reproducible calculations. Human consultation may be offered as an optional product feature, but it is never a runtime dependency or release gate.

This principle does **not** mean that generated content is automatically true. The system must distinguish source evidence, machine extraction confidence, calculation verification, interpretation, and uncertainty.

## 1. Scripture corpus and source provenance

Every source item must carry, where available:

- Stable source and edition identifiers; title; attributed author/tradition; language and script.
- Publisher, publication date, edition/recension, volume, page/section and stable public URL or archive identifier.
- Rights status: public domain, open licence with its conditions, permission granted, or not usable.
- Ingestion method, file checksum, ingestion timestamp, OCR/transcription tool and version.
- Original text, normalized searchable text, script/transliteration, translation, and commentary as separate layers.
- OCR/transcription confidence and a machine-validation status. Low-confidence text must not be presented as an exact quotation.

Prefer public-domain primary texts and explicitly open-licensed editions. Do not ingest or redistribute modern copyrighted translations, commentaries, scans, or databases without a compatible licence or permission. A public URL alone does not establish reuse rights.

## 2. Text segmentation and retrieval

Segment texts at their native structural level: work, recension/edition, kāṇḍa/parva/skandha, adhyāya, sūkta, mantra, verse, and line where applicable. Preserve original ordering and parent-child relationships. Do not manufacture verse numbers when an edition does not provide them.

Search should support Devanagari, Sanskrit normalization, transliteration variants, Hindi and English. Retrieval results must retain the exact source edition and location metadata. Similar wording across editions must not be silently merged.

## 3. Grounded answer contract

The answer pipeline must:

1. Classify the question and identify the relevant textual domain.
2. Retrieve source passages before making scripture-specific claims.
3. Build the answer only from retrieved evidence plus clearly labelled general explanation.
4. Attach citations at claim level: work, edition/recension, section and verse/page as available.
5. Distinguish direct quotation, paraphrase, translation, commentary and modern inference.
6. Show material differences among traditions or editions instead of pretending there is one uncontested reading.
7. Say that a supporting source was not found when retrieval is insufficient. Never invent a scripture title, verse number, quotation, edition, or claim that a passage was checked when it was not.
8. Treat user-provided text and retrieved documents as untrusted data, not as system instructions.

An answer without sufficient evidence may still offer a clearly labelled general explanation, but it must not masquerade as a scripture-cited answer.

## 4. Autonomous quality assurance (no human approval gate)

Use automated, auditable checks:

- Schema and required-metadata validation.
- File checksum, source URL, edition and rights-metadata validation.
- OCR confidence thresholds and Sanskrit/Devanagari integrity checks.
- Duplicate detection without collapsing distinct recensions.
- Structural sequence and cross-reference validation.
- Citation resolution: every emitted citation must map to an ingested source location.
- Golden question/answer evidence sets, including questions for which the correct result is “source not found”.
- Regression tests for fabricated citations, unsupported claims, prompt injection and conflicting traditions.
- Versioned corpus builds with reproducible manifests and change logs.

A machine status such as `source_metadata_validated` means only that the automated metadata checks passed. It does not mean that the religious claim has been proven universally correct. Use explicit states such as `source_missing`, `ingestion_pending`, `ocr_low_confidence`, `metadata_validated`, `citation_resolved`, and `automated_regression_passed`. Do not label content as “Acharya approved” or “human verified” unless that optional event actually occurred.

## 5. Independent Jyotish computation

Keep astronomical calculation separate from astrological interpretation.

### Calculation layer

Document and version the calculation profile, including:

- Ephemeris source and version, time scale and conversion method.
- Birth date/time, timezone database version, location coordinates and coordinate source.
- Ayanāṃśa model, node model (mean/true), house system and zodiac convention.
- Planetary longitudes, ascendant, rāśi, bhāva, nakṣatra and pāda derivation.
- Panchāṅga limb algorithms and sunrise/sunset conventions.
- Dasha and varga calculation algorithms, with explicit rules and boundary behavior.

Return the selected profile and relevant input assumptions with results. Never silently substitute approximate calculations when a requested precision profile is unavailable.

### Interpretation layer

Represent Jyotish rules as versioned, testable rule sets linked to their textual or tradition source. Support configurable paramparā/profiles where methods differ. Separate computed facts (for example, a longitude or nakṣatra assignment under a stated profile) from interpretive statements (for example, a yoga's traditional meaning). Present interpretations as tradition-based readings, not scientific guarantees or certain predictions.

### Calculation validation

Maintain golden test vectors with known input data and expected outputs, including edge cases around timezones, daylight saving transitions, sunrise boundaries, sign/nakṣatra transitions, retrograde motion, dasha boundaries and divisional-chart boundaries. Compare supported ephemeris outputs against independently published reference vectors. Tests must fail loudly when the configured ephemeris or convention is missing.

## 6. Release and operating policy

No mandatory Acharya approval, reviewer identity, or human sign-off is required to operate or release the autonomous scripture and Jyotish engines. Release decisions must instead require:

- Passing automated test suites on the exact release commit.
- Valid corpus provenance and rights metadata for published material.
- Citation-resolution and unsupported-claim regression tests.
- Calculation golden tests for every calculation profile advertised as supported.
- Security, privacy, legal, accessibility, operational and rollback gates.
- Clear disclosure of source limitations, calculation conventions and uncertainty.

Optional expert feedback can be recorded as an additional evidence stream, never as a blocking dependency. Product-owner and legal/security obligations remain separate from religious-content approval.

## 7. Phased implementation

1. Establish source and citation schemas; migrate away from `review_required` as a publication prerequisite.
2. Build an ingestion manifest and a small rights-cleared primary-text corpus.
3. Implement retrieval that returns edition-aware, resolvable passage identifiers.
4. Enforce the grounded answer contract in the AI adapter and API response.
5. Add corpus and answer regression suites, including unsupported-question cases.
6. Document Jyotish profiles and build golden calculation vectors.
7. Expand the corpus only when provenance, rights and validation metadata are present.

## Current implementation warning

This document is the target architecture, not evidence that all capabilities already exist. The current starter catalogues are limited, several records lack verse-level primary-source provenance, and the current Jyotish engine still requires precision and golden-vector validation. Keep the product labelled as a development beta until each advertised capability passes its own acceptance tests.
