# AI Family Pandit Ji — Sanatan Dharma Digital Ecosystem

A mobile-first Hindi/Sanskrit/English spiritual guidance platform.

## Implemented in this repository

- Responsive browser interface with text chat and device-dependent speech input/output.
- FastAPI backend with `GET /health`, `GET /api/knowledge`, `GET /api/knowledge/topics` (optional category filter), `GET /api/modules`, and `POST /api/ask`.
- Frontend-to-backend chat integration when the page is served from the same host as the API.
- Optional OpenAI-compatible chat-completions provider configured only through environment secrets.
- Safe fallback to the starter curated knowledge library when no provider is configured or the provider is unavailable.
- Ecosystem roadmap catalogue and a starter knowledge-card browser in the frontend; both clearly label planned/draft content.
- Language selection (Hindi, Sanskrit, English), request validation and basic API smoke tests.

## Important current limitations

This is a development beta, not a production-ready religious service. The five starter knowledge entries are drafts and require acharya review. AI-generated responses are not scripture-verified and are marked for human review. No real Panchang calculation, horoscope/kundli engine, verified pandit directory, booking, e-commerce, payment, user accounts, admin console, or production voice-cloning/TTS service is integrated. Browser speech depends on the device and browser; it does not yet provide the requested dedicated deep spiritual voice.

## Run locally

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
4. Sixteen samskaras and life-event guidance — basic list only.
5. Panchang, muhurta, horoscope and kundli — not integrated.
6. Pandit discovery, profiles, verification and booking — not integrated.
7. Temple, pilgrimage and seva discovery — static guidance only.
8. Puja samagri catalogue and e-commerce — not integrated.
9. Payments, orders, refunds and notifications — not integrated.
10. Admin console, moderation, audit logs, analytics and security — not integrated.
11. Automated tests, deployment, monitoring and beta release — automated API tests run in GitHub Actions; deployment and monitoring remain.

## Safety and trust

Religious practices vary by sampradaya, region, family tradition and source text. The platform must show source/context, avoid presenting disputed practice as universal, and recommend qualified human acharya review for consequential questions. Never rely on this beta for time-critical Panchang or astrological decisions.


The knowledge topics endpoint supports category filtering and text search with `?category=mantra` and `?q=panchang`. Starter topics include Hindi, English and Sanskrit answer drafts plus transliterated search aliases; all remain marked for acharya review.
