# AI Family Pandit Ji — Sanatan Dharma Digital Ecosystem

A mobile-first Hindi/Sanskrit/English spiritual guidance platform.

## Implemented in this repository

- Responsive browser interface with text chat, searchable mantra cards, device-dependent speech input/output, selectable installed speech voices and native answer sharing.
- Device-local daily Sadhana/Sankalp tracker with a configurable mantra, daily japa goal, +1/+108 counters and progress indicator; its data stays in the browser and is not sent to the API.
- Public read-only Acharya review status panel; secure admin workflow specification and JSON Schema for source provenance, reviewer qualification, independent checks and review decisions. No public approval/write endpoint is exposed.
- Installable Progressive Web App shell (manifest, app icon and service worker); the static app shell can be cached, while live chat/API calls still require a network connection.
- FastAPI backend with `GET /health` (liveness), `GET /ready` (local asset/catalogue readiness only), `GET /api/knowledge`, `GET /api/knowledge/topics` (category and multilingual text filters), `GET /api/samskaras` (sixteen-samskara draft catalogue), `GET /api/puja-guides` (bilingual puja/aarti draft guides with filters), `GET /api/modules`, `GET /api/trust/status` (transparent beta, content-review and missing-capability status), `GET /api/mantras` (multilingual mantra catalogue and search), `GET /api/search` (unified search across knowledge, mantras and puja guides), `GET /api/panchang/overview` (educational five-limbs overview), `GET /api/panchang/calculate` (location/date Panchang calculation), `POST /api/kundli/calculate`, `POST /api/jyotish/advanced`, `GET /api/astronomy/status`, `GET /api/pandits` (verified records only; no booking), `POST /api/pandit-applications` (private pending application intake) and authenticated `GET /api/admin/pandits/pending` (private review queue), `GET /api/temples` (curated official-source temple discovery) and `GET /api/temples/{temple_id}` (single-temple detail with source provenance and pilgrimage-circuit membership), `GET /manifest.webmanifest`, `GET /sw.js`, `GET /privacy`, `GET /terms`, and `POST /api/ask`.
- Frontend-to-backend chat integration when the page is served from the same host as the API.
- Optional OpenAI-compatible chat-completions provider configured only through environment secrets.
- Safe fallback to the starter curated knowledge library when no provider is configured or the provider is unavailable.
- Ecosystem roadmap catalogue and a searchable, category-filtered knowledge-card browser with Hindi/English/Sanskrit draft display; a sixteen-samskara overview in Hindi and English, bilingual puja/aarti guide cards, a searchable multilingual mantra library, and an educational Panchang five-limbs section; all clearly label draft content requiring acharya review.
- Language selection (Hindi, Sanskrit, English), request validation and basic API smoke tests. Baseline HTTP security headers are applied to responses, and API responses use `Cache-Control: no-store`.

## Privacy and responsible use

The app footer links to `/privacy` and `/terms`. These are preliminary beta notices describing the current no-account/no-payment implementation, AI-provider data flow, device speech caveats and religious-content limitations. They are not a substitute for legal review. Before public launch, identify the legal operator, add a contact and grievance channel, confirm hosting/provider retention terms, and obtain jurisdiction-specific privacy/consumer-law review.

## Important current limitations

This is a development beta, not a production-ready religious service. The starter knowledge entries, mantra text, puja/aarti guides and samskara catalogue remain drafts requiring traceable sources and qualified Acharya review. AI-generated responses are not scripture-verified and are marked for human review.

Panchang and Kundli calculation endpoints are implemented. The dependency-free engine is explicitly low precision. The Docker image now bundles MIT-licensed Skyfield and downloads the freely available NASA/JPL DE440s file during image build; `engine=auto` selects it when both prerequisites are present. Local non-Docker development still needs `pip install -r backend/requirements-astronomy.txt` and `python scripts/download_ephemeris.py`. `GET /api/astronomy/status` reports whether both the local file and Skyfield dependency are ready. The `auto` mode transparently falls back when either prerequisite is missing. Lahiri ayanamsa, Rahu/Ketu mean nodes, ascendant/houses and Vedic conventions remain approximate; JPL Panchang limb-transition times now use a 10-minute DE440s scan plus binary search to about one second; nakshatra/yoga boundaries still depend on approximate Lahiri ayanamsa, so these are not certified Panchang times. No muhurta engine or regionally validated Panchang is claimed.

The advanced Jyotish endpoint exposes preliminary D2 Hora, D3 Drekkana, D7 Saptamsa, D9 Navamsa, D10 Dashamsa and D12 Dwadasamsa placements, plus Vimshottari Mahadasha, Antardasha and Pratyantardasha. These derivations still require trusted golden-test comparisons and qualified Jyotish review before consequential use. City quick-fill presets are approximate city-center coordinates; users should refine them to the actual birth location. Birth details are not persisted by the calculation endpoints.

The temple directory currently contains five initial temple records, four Uttarakhand Char Dham shrines, and the twelve traditional Jyotirlinga entries (Kedarnath is one shared record, not duplicated). The directory distinguishes temple-trust/administration sites from government tourism information; government links are not presented as temple websites. Their linked sources are official Uttarakhand government tourism and yatra-registration portals, not individual temple websites. It is not exhaustive; visitors must reconfirm opening dates, weather, routes, registration, timings and rules on the linked official sources. Pandit self-application intake and a private admin pending queue are implemented; verification remains a manual admin action and no live verified profiles, booking lifecycle, e-commerce, payments, user accounts or production voice service are integrated. The Pandit directory returns only real records and currently has no verified booking workflow. Browser speech and available voice choices depend on the device/browser; pitch adjustment does not guarantee a dedicated spiritual voice. The PWA caches only the app shell; live API calls require connectivity.
 
## Production launch handoff

See [LAUNCH_HANDOFF.md](LAUNCH_HANDOFF.md) for the owner-input checklist, external integration evidence and mandatory release gates. See [STAGING_SMOKE_TESTS.md](STAGING_SMOKE_TESTS.md) for staging API, browser, security and go/no-go checks. The current repository remains a development beta; do not treat CI success or a container build as production launch approval. `GET /api/trust/status` reports implemented calculation endpoints and the Pandit discovery API foundation separately from still-missing live verified listings, booking, commerce, production voice, expert review and operational release gates.

## Deployment\n\nSee [DEPLOYMENT.md](DEPLOYMENT.md) for the Docker build, hosting configuration and pre-launch checklist. A container build does not itself deploy the application.\n\n## Run locally

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`. API docs are at `http://127.0.0.1:8000/docs`.

## Optional AI provider configuration

Set these environment variables on the server (do not put secrets in Git):

- `AI_API_KEY`: provider API key
- `AI_BASE_URL`: OpenAI-compatible API base URL (default `https://api.openai.com/v1`)
- `AI_MODEL`: model identifier supported by that provider
- `AI_TIMEOUT_SECONDS`: request timeout (default 25)
- `ALLOWED_ORIGINS`: comma-separated production frontend origins; use `*` only for local development

The backend calls `/chat/completions`. If the key/model is missing or the provider errors, it falls back to the local knowledge library. The API health endpoint reveals only whether credentials are configured, never the key.

## Tests

```bash
cd backend
pytest -q
```

## Product roadmap

1. Core platform, responsive UX, language and accessibility — starter beta implemented; needs device testing.
2. AI Pandit conversation engine — optional provider adapter implemented; credentials, provider validation and safety evaluation remain.
3. Reviewed knowledge library — starter drafts only; acharya review and source citations remain.
4. Sixteen samskaras and life-event guidance — overview catalogue added; detailed procedures, source citations and acharya review remain.
5. Puja and aarti guidance — introductory bilingual draft guides added; tradition-specific vidhi, mantras, citations and acharya review remain.
6. Panchang and Kundli calculations plus preliminary D2/D3/D7/D9/D10/D12 vargas and full Vimshottari periods — approximate engine and optional JPL DE440s planetary positions / standard-horizon solar events integrated; Vedic convention validation, regional Panchang comparison, precise JPL limb-transition times, muhurta and professional interpretation remain outstanding.
7. Pandit discovery, profiles, verification and booking — not integrated.
8. Temple, pilgrimage and seva discovery — searchable directory covering the twelve Jyotirlinga circuit and Uttarakhand Char Dham, alongside the initial temple records; broader national pilgrimage coverage remains outstanding.
9. Puja samagri catalogue and e-commerce — not integrated.
10. Payments, orders, refunds and notifications — not integrated.
11. Admin console, moderation, audit logs, analytics and security — not integrated.
12. Automated tests, deployment, monitoring and beta release — automated API tests run in GitHub Actions; deployment and monitoring remain.

## Safety and trust

Religious practices vary by sampradaya, region, family tradition and source text. The platform must show source/context, avoid presenting disputed practice as universal, and recommend qualified human acharya review for consequential questions. Never rely on this beta for time-critical Panchang or astrological decisions.


The knowledge topics endpoint supports combined category filtering and text search with `?category=mantra&q=Gayatri` or `?q=panchang`. The frontend exposes these filters, displays language-specific draft answers, and reports empty search results. Starter topics include Hindi, English and Sanskrit answer drafts plus transliterated search aliases; all remain marked for acharya review.


## Install the web app

Serve the app over HTTPS (or localhost during development), open it in a supported mobile/desktop browser, and use the browser's **Install app** or **Add to Home Screen** option. The service worker caches the app shell only; API responses, AI chat and voice recognition are not guaranteed to work offline.


## Unified search

Use `GET /api/search?q=Gayatri&language=en` to search the starter knowledge library, mantra entries and puja/aarti guides together. Supported languages are `hi`, `sa` and `en`; results are capped at 50 and every result remains explicitly marked as a draft requiring acharya review. This is catalogue search, not a source-verification service.


## Trust and release status

The `GET /api/trust/status` endpoint reports whether the optional AI provider is configured, counts draft knowledge assets, shows beta versus planned module counts, and explicitly lists major capabilities that are not implemented. It always reports production release readiness as false until the missing integrations, expert review, security work and deployment checks are completed. This endpoint is a transparency summary, not a certification or security audit.


## Panchang, Jyotish and Pandit directory foundations

- `GET /api/panchang/overview` is an educational explanation only; it does not calculate a live Panchang or muhurta.
- `GET /api/jyotish/guide` documents the consent-based birth details required by a future chart engine. No kundli or prediction calculations are performed.
- `GET /api/pandits` reads the verified-first directory catalogue. It currently returns an empty list and does not accept bookings. No sample or fictional pandit profiles are displayed.
- Directory verification, secure birth-data handling, a validated ephemeris/calculation engine, and expert review are prerequisites before these become live services.


## Daily Sadhana and Sankalp

The home page includes a private, device-local japa tracker. It supports a custom practice name, daily target, +1 and +108 counters and a progress indicator. Data is stored in that browser's local storage; it is not synchronized across devices or sent to the backend. Clearing browser data or changing devices may remove it.

## Admin and Acharya review specification

See [ADMIN_CONTENT_WORKFLOW.md](ADMIN_CONTENT_WORKFLOW.md) and [schemas/content-review.schema.json](schemas/content-review.schema.json). The home page shows the public read-only review policy and catalogue counts. These artifacts specify a future secure workflow; they do not create admin accounts, authenticate reviewers, store approvals or publish content. No public write/approval route is available.

## Acharya content review workflow foundation

- `GET /api/content/review-policy` describes the source/provenance metadata and human review steps required before religious content can be approved.
- It reports the current catalogue sizes for knowledge, puja guides, samskaras and mantras where available.
- Required evidence includes source title, author/tradition, edition/publication, page/section, reviewer identity and qualification, review date, decision and notes.
- This is deliberately a read-only workflow blueprint. It does not authenticate reviewers, accept submissions, or approve content. All starter content remains draft until a secure editorial system and genuine acharya sign-off exist.


## Pandit directory foundation

The public `GET /api/pandits` endpoint and mobile-first directory search UI return only profiles that an authenticated platform admin has explicitly reviewed; pending, rejected and suspended profiles are never public. A prospective Pandit can submit a minimal application through `POST /api/pandit-applications`; it is stored privately in `pending_review` and is not published automatically. Admin-only `GET /api/admin/pandits/pending` lists pending applications, `POST /api/admin/pandits/{profile_id}/verify` records the review method, reviewer qualification, evidence reference and notes, `POST /api/admin/pandits/{profile_id}/reject` records a reason and removes an application from the pending queue without publishing it, and `POST /api/admin/pandits/{profile_id}/suspend` removes a verified profile from public results. Application status is available through the protected status endpoint. Set `ADMIN_API_TOKEN` to a random secret of at least 32 characters and optionally set `PANDIT_DIRECTORY_DB` to a persistent SQLite volume. Verification means platform review of submitted profile/evidence only; it is not government certification or a guarantee of service quality. This foundation does not implement document uploads, messaging, availability, booking or payment. Define and publish a lawful retention/deletion policy before collecting real applicant data; do not submit identity documents or other sensitive evidence through this beta form.


### Pandit application data retention and erasure

The admin-only `POST /api/admin/pandits/{profile_id}/erase` endpoint permanently deletes an unverified pending or rejected application from the active SQLite database. It requires a bearer admin token, a reason and explicit `confirm_delete: true`; it refuses verified profiles. This is a manual erasure control, not an automatic retention scheduler or a self-service applicant identity-verification process. Set and publish a lawful retention schedule before collecting real applications, handle valid data-subject requests through an appropriately verified process, and define separate retention/deletion for backups, logs and hosting-provider copies. Do not collect identity-document uploads in this beta.
