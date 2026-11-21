# Deployment guide

This repository now includes a Dockerfile for a portable container build. A successful image build is not the same as a live deployment; a hosting account, domain, environment secrets and operator approval are still required.

## Container build

From the repository root:

```bash
docker build -t ai-family-pandit-ji .
docker run --rm -p 8000:8000 \
  -e AI_API_KEY="$AI_API_KEY" \
  -e AI_MODEL="$AI_MODEL" \
  -e APP_ENV=production \
  -e ALLOWED_ORIGINS="https://your-domain.example" \
  ai-family-pandit-ji
```

Open `/health` to confirm the API process responds. Use `/api/release/readiness` for the explicit production checklist; it intentionally remains not-ready until all external services and human approvals are actually verified. The image runs as a non-root user and includes a container health check.

## Required hosting configuration

- Set `PORT` to the port supplied by the hosting platform (the container command reads it).
- Set `APP_ENV=production` and `ALLOWED_ORIGINS` to exact frontend origins. Production startup rejects wildcard origins and non-HTTPS AI endpoints.
- Keep `AI_TIMEOUT_SECONDS` between 1 and 120 seconds; the default is 25 seconds.
- Configure `ASK_RATE_LIMIT_MAX` (default 20) and `ASK_RATE_LIMIT_WINDOW_SECONDS` (default 60) to cap repeated `POST /api/ask` requests per client IP. Valid ranges are 1–10000 requests and 1–3600 seconds.
- The built-in limiter is per application process and uses the direct connection IP; behind a proxy, configure trusted client-IP handling at the edge. For multiple workers/replicas, enforce a shared rate limit at the API gateway/WAF or a shared store. Do not treat this in-memory guard as a substitute for distributed abuse protection.
- Configure `AI_API_KEY` and `AI_MODEL` as hosting secrets if AI-provider answers are required. Never commit real keys.
- Keep provider usage limits, billing alerts and key rotation under the account owner's control.
- Enable HTTPS, platform logs, backups and uptime monitoring.

## Public-facing notices

The app exposes preliminary beta notices at `/privacy` and `/terms`. Before public release, replace/approve these drafts with the legal operator's identity, a monitored contact and grievance channel, actual AI/hosting provider details, retention periods, user-rights process, refund/consumer terms (if commerce is enabled), and jurisdiction-specific legal review. Do not claim privacy or data-retention guarantees that the selected providers and hosting configuration do not support.

## Before public launch

1. Complete expert acharya review and source verification for all religious content.
2. Perform a security/privacy review, including abuse controls, rate limiting and data-retention decisions.
3. Integrate and validate real Panchang and Jyotish calculation services before exposing time-sensitive results.
4. Verify pandit identities and qualifications before enabling listings or booking.
5. Integrate payment provider webhooks, refunds and order controls before accepting money.
6. Test voice behavior on supported Android, iOS and desktop browsers.
7. Deploy to a staging environment, run smoke tests, then approve production release.

## Current release status

Development beta only. No live hosting provider, production domain, provider secrets, expert sign-off, payment gateway, booking workflow or production voice service is configured by this repository alone.
