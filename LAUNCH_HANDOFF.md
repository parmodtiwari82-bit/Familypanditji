# Launch handoff — AI Family Pandit Ji

**Release decision: NOT APPROVED FOR PUBLIC PRODUCTION LAUNCH.**  
This file is the execution handoff for the remaining work. A green test suite and a successful Docker build validate code/build steps only; they do not prove that external services, legal duties, religious review or production operations are ready.

## 1. Ready in the repository (verify again on the release commit)

- FastAPI application and multilingual starter experience (Hindi, Sanskrit, English).
- Draft knowledge, mantra, puja-guide and samskara catalogues with review-required status.
- Search, chat adapter/fallback, browser speech integration and device-local Sadhana tracker.
- Read-only trust, release-readiness and Acharya-review policy endpoints/panels.
- Baseline security headers, production configuration checks, Docker image and GitHub Actions tests/build.
- Preliminary privacy and terms notices, explicitly requiring legal replacement/review.

## 2. External decisions and purchases — do not fake or bypass

| Workstream | Owner must provide/decide | Acceptance evidence |
|---|---|---|
| Hosting + domain | Hosting account, domain, DNS access, production HTTPS origin | Staging and production URLs; health check; rollback tested |
| AI provider | Provider account, API key, approved model, budget/usage limits | Secret stored only in host; Hindi/Sanskrit/English quality and safety test report |
| Live Panchang/Jyotish | Licensed/approved calculation source or validated ephemeris, calculation convention, timezone/location policy | Golden test cases checked by qualified domain experts; documented accuracy limits |
| Acharya review | Named qualified reviewers, traditions/regions covered, source editions and review time | Signed review records for every item promoted from draft |
| Pandit directory/booking | Verification operator, identity/qualification process, consent, availability and cancellation policy | Real verified profiles, test booking lifecycle, support and dispute process |
| Store + payments | Merchant account, gateway, tax/invoice policy, shipping/returns/refunds | Sandbox-to-live payment test, signed webhook verification, refund/reconciliation tests |
| Voice | Chosen speech vendor/voice rights, languages, usage pricing and consent | Supported-device audio QA; clear fallback and disclosure |
| Legal + privacy | Legal operator identity, address/contact, grievance contact, retention and deletion policy | Counsel-approved privacy/terms and provider data-processing review |
| Operations/security | Support owner, incident contact, backups, monitoring, abuse/rate controls | Restore drill, alert test, security review and incident runbook |

## 3. Mandatory release gates

- [ ] All automated tests pass on the exact release commit.
- [ ] Production container builds and starts with production configuration.
- [ ] HTTPS, exact CORS origins, secrets handling and key rotation verified.
- [ ] Rate limiting/abuse controls implemented at a trusted gateway or application layer and load-tested.
- [ ] Security review covers authentication, authorization, CSRF, injection, dependency vulnerabilities and sensitive-data handling.
- [ ] Privacy notice, terms, consent and retention/deletion flows approved for the actual operator/providers.
- [ ] Every public religious answer/catalogue item has traceable source provenance and documented qualified Acharya approval, or remains clearly marked draft.
- [ ] Panchang/Jyotish results are not shown as live until calculation conventions and test vectors are independently validated.
- [ ] Pandit listings are real and verified; booking, payments and commerce are not advertised as active until end-to-end tests pass.
- [ ] Mobile/desktop accessibility, browser speech, install/PWA behavior and failure states tested on supported devices.
- [ ] Staging smoke test, backup/restore test, monitoring/alerts and rollback completed.
- [ ] Product owner signs the go-live decision.

## 4. Safe launch scope if dependencies are not purchased yet

A restricted private demo may show the current beta with clear draft/review labels and no claims of live Panchang, Kundli, verified pandit booking, payments or production-grade spiritual voice. Do not collect sensitive birth details or payments in this scope. Do not call this a public production launch.

## 5. Release procedure

1. Freeze feature work and select an immutable commit.
2. Run API tests and container build on that exact commit.
3. Deploy to staging with production-like settings and non-production credentials.
4. Execute API/UI smoke tests, mobile device QA, security checks and restore/rollback drill.
5. Obtain Acharya, legal, operations and product-owner approvals.
6. Deploy production, verify health and key user journeys, monitor error rates, and retain rollback capability.

**No credentials belong in Git, issues, chat transcripts or this handoff.** Use the hosting provider's secret manager and grant least-privilege access.
