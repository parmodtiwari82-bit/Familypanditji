# Render staging deployment

This repository includes a Render Blueprint at `render.yaml` for a private evaluation/staging deployment.

## Deploy

1. Sign in to Render and connect the GitHub repository `parmodtiwari82-bit/Familypanditji`.
2. Open Render's Blueprint flow and select branch `deploy/render-staging-blueprint`.
3. Review the service settings and create the web service.
4. Wait for the Docker build and deploy to finish. Render will provide the HTTPS service URL.
5. Open `/health`, then `/api/astronomy/status`, `/api/release/readiness`, and `/docs` (docs are enabled in staging).
6. Use the service URL as the base URL for the staging smoke-test script in `STAGING_SMOKE_TESTS.md`.

## Staging-only safeguards

- The blueprint sets `APP_ENV=staging`; it is not a production deployment.
- No AI provider key is included. Chat therefore uses the repository's limited curated fallback.
- Free instances may spin down when idle and can have ephemeral storage. Do not treat this as durable production hosting.
- Do not enter real or sensitive birth details until you have reviewed the service's data handling and access controls. The Kundli calculation API is intended not to persist birth details, but hosting logs and operational systems still require review.
- The current Vedic calculations remain approximate and require independent ephemeris/golden-vector and qualified Acharya review. A successful deploy proves the API runs, not astrological accuracy.

## Production

Do not promote this free staging blueprint directly to production. Production requires a paid/appropriate hosting plan, explicit HTTPS CORS origin, secrets management, durable storage where needed, security/privacy review, monitoring, backup/restore and owner approval. Follow `DEPLOYMENT.md` and `LAUNCH_HANDOFF.md`.
