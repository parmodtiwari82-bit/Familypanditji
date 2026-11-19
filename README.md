# AI Family Pandit Ji — Sanatan Dharma Digital Ecosystem

A mobile-first Hindi/Sanskrit/English spiritual guidance platform.

## Implemented in this repository

- Responsive browser interface with text chat, searchable mantra cards, device-dependent speech input/output, selectable installed speech voices and native answer sharing.
- Installable Progressive Web App shell (manifest, app icon and service worker); the static app shell can be cached, while live chat/API calls still require a network connection.
- FastAPI backend with `GET /health`, `GET /api/knowledge`, `GET /api/knowledge/topics` (category and multilingual text filters), `GET /api/samskaras` (sixteen-samskara draft catalogue), `GET /api/puja-guides` (bilingual puja/aarti draft guides with filters), `GET /api/modules`, `GET /api/trust/status` (transparent beta, content-review and missing-capability status), `GET /api/mantras` (multilingual mantra catalogue and search), `GET /api/search` (unified search across knowledge, mantras and puja guides), `GET /api/panchang/overview` (educational five-limbs overview only), `GET /manifest.webmanifest`, `GET /sw.js`, and `POST /api/ask`.
- Frontend-to-backend chat integration when the page is served from the same host as the API.
- Optional OpenAI-compatible chat-completions provider configured only through environment secrets.
- Safe fallback to the starter curated knowledge library when no provider is configured or the provider is unavailable.
- Ecosystem roadmap catalogue and a searchable, category-filtered knowledge-card browser with Hindi/English/Sanskrit draft display; a sixteen-samskara overview in Hindi and English, bilingual puja/aarti guide cards, a searchable multilingual mantra library, and an educational Panchang five-limbs section; all clearly label draft content requiring acharya review.
- Language selection (Hindi, Sanskrit, English), request validation and basic API smoke tests.

## Important current limitations

This is a development beta, not a production-ready religious service. The five starter knowledge entries, sixteen-samskara overview and puja/aarti guide catalogue are drafts and require acharya review. AI-generated responses are not scripture-verified and are marked for human review. The PWA caches only the app shell; live chat/API calls require connectivity. The Panchang endpoint is educational and does not calculate today's Panchang or muhurta. No real Panchang calculation, horoscope/kundli engine, verified pandit directory, booking, e-commerce, payment, user accounts, admin console, or production voice-cloning/TTS service is integrated. Browser speech and available voice choices depend on the device and browser; pitch is adjusted, but this does not guarantee a dedicated deep spiritual voice or production voice service.

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
6. Panchang, muhurta, horoscope and kundli — not integrated.
7. Pandit discovery, profiles, verification and booking — not integrated.
8. Temple, pilgrimage and seva discovery — static guidance only.
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
