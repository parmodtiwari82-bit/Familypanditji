# Edition-Aware Scripture Passage and Citation Contract

## Why this layer exists
A source work can have multiple recensions, editions, scripts, translations, and pagination systems. A citation must resolve to one registered edition and an edition-native location; a generic work title is not enough.

## Passage fields
Each passage has a stable passage ID, source ID, edition ID, ordered locator components (for example, chapter and verse, or mandala and sukta), original-language/script metadata, original text, and transcription provenance. OCR records must carry a confidence value from 0 to 1. Translation records identify the translation language, text, and translator or source; translation rights are tracked separately.

## Resolution behavior
The backend resolver resolves a passage ID against the passage manifest and source registry. It returns edition details and a readable locator. Unknown or broken references raise CitationNotFound; callers must show an explicit source-not-found response rather than inventing a verse or citation.

## Validation behavior
The passage validator checks source/edition references, edition ownership, recorded rights state, locator shape, transcription method/status, OCR confidence, and translation attribution. CI runs this validator and the tests.

## Current state and limitations
The passage manifest is intentionally empty. No verse text, translation, source URL, or rights claim is fabricated. Passing validation means only that the metadata structure is internally consistent with the registered IDs and rights evidence. It does not prove that a transcription matches a manuscript, that a translation is accurate, or that a religious interpretation is universally accepted.

## Next implementation step
Connect the resolver to the scripture-answer retrieval layer so scripture-specific factual claims can only be emitted with a resolvable passage ID and citation. If retrieval yields no suitable source, the answer must say the source was not found.
