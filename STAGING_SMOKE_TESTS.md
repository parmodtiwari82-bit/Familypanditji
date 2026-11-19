# Staging smoke-test runbook

Run these checks against a staging URL after deploying the exact release commit. Replace `BASE_URL` with the staging origin. Do not run payment or destructive tests against production.

## API checks

```bash
export BASE_URL="https://staging.example.com"
curl -fsS "$BASE_URL/health"
curl -fsS "$BASE_URL/api/trust/status"
curl -fsS "$BASE_URL/api/release/readiness"
curl -fsS "$BASE_URL/api/modules"
curl -fsS "$BASE_URL/api/panchang/overview"
curl -fsS "$BASE_URL/api/mantras"
curl -fsS "$BASE_URL/api/puja-guides"
curl -fsS "$BASE_URL/api/samskaras"
curl -fsS "$BASE_URL/api/content/review-policy"
curl -fsS "$BASE_URL/privacy"
curl -fsS "$BASE_URL/terms"
```

Expected: HTTP 200 for configured routes; health reports service identity; trust/readiness clearly state beta or pending status until verified; religious catalogues retain draft/review labels; Panchang overview says educational only; no fake pandit profiles or active booking/payment claims.

## Input validation

```bash
curl -fsS -X POST "$BASE_URL/api/ask" -H "Content-Type: application/json" \
  -d '{"question":"गायत्री मंत्र का अर्थ बताइए","language":"hi"}'

# Invalid language must return 422.
curl -sS -o /dev/null -w "%{http_code}\n" -X POST "$BASE_URL/api/ask" \
  -H "Content-Type: application/json" -d '{"question":"hello","language":"fr"}'
```

Expected: valid query returns a safe beta answer; invalid language and oversized questions return 422. Never use real birth data or sensitive personal information in smoke tests.

## Browser and device checks

- Test current Android Chrome and desktop browsers at narrow mobile and desktop widths.
- Search in Hindi, Sanskrit and English; verify results and empty states.
- Test microphone denied, speech recognition unsupported, and speech synthesis unavailable; UI must fail gracefully.
- Test voice selection and audio only where browser voices are available.
- Add a Sadhana target, increment, reload and verify device-local persistence.
- Clear Sadhana data and verify confirmation prevents accidental deletion.
- Install the PWA where supported; verify icon, standalone launch and update behavior.
- Open privacy and terms from the footer; replace draft notices before public release.

## Security and operations

- Production secrets exist only in the host secret manager, never in Git or browser bundles.
- Exact HTTPS CORS origins are configured; wildcard CORS must fail production startup.
- Verify HTTPS certificate/redirect, HSTS at public edge, security headers and no-store API responses.
- Apply gateway/WAF rate limits and abuse controls; verify 429 behavior without relying on in-memory per-process limits.
- Verify logs do not contain API keys, authorization headers, sensitive prompts or personal birth details.
- Complete backup restore, monitoring alert, incident contact and rollback drills.

## Go/no-go record

Record commit SHA, staging URL, test date, tester, pass/fail evidence and defects. Production requires product-owner, operations/security, legal/privacy and qualified Acharya sign-off. Any failed mandatory gate means **NO-GO**.
