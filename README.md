# AI Family Pandit Ji — Sanatan Dharma Digital Ecosystem

A mobile-first Hindi/Sanskrit/English spiritual guidance platform, planned as a complete ecosystem rather than a single chat screen.

## Current repository milestone

- Responsive web beta interface: `index.html`
- Starter FastAPI service: `backend/main.py`
- Health endpoint: `GET /health`
- Placeholder question endpoint: `POST /api/ask`
- Browser speech input/output where supported by the device

**Important:** this is an early technical foundation, not a production-ready AI service. The current question endpoint is explicitly a placeholder. Live LLM responses, curated/cited religious knowledge, real Panchang calculations, astrology, bookings, commerce, payments, authentication, admin controls, and production voice are not yet integrated or tested.

## Run the web beta

Open `index.html` in a modern browser. For microphone access, serve it from localhost or HTTPS and grant microphone permission.

## Run the API

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn main:app --reload
```

Health check: `GET http://127.0.0.1:8000/health`

## Product modules / roadmap

1. Core platform, responsive UX, language and accessibility
2. AI Pandit conversation engine with deep spiritual voice and safe escalation
3. Reviewed knowledge library: puja, mantra, aarti, vrata, festivals, stories
4. Sixteen samskaras and life-event guidance
5. Panchang, muhurta, horoscope and kundli with location/time accuracy
6. Pandit discovery, profiles, verification and booking workflow
7. Temple, pilgrimage and seva discovery
8. Puja samagri catalogue and e-commerce
9. Payments, order management, refunds and notifications
10. Admin console, moderation, audit logs, analytics and security
11. Automated tests, deployment, monitoring and beta release

## Safety and trust

Religious practices vary by sampradaya, region, family tradition and source text. The platform must show source/context, avoid presenting disputed practice as universal, and recommend qualified human acharya review for consequential questions. Astrology and Panchang features must disclose calculation method, location and timezone.

## Configuration

Copy `.env.example` to `.env` for local development. Never commit real API keys, payment secrets, passwords, or private user data.
