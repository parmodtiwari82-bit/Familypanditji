# Launch handoff — AI Family Pandit Ji

**Release decision: NOT APPROVED FOR PUBLIC PRODUCTION LAUNCH.**  
A green test suite and successful container build validate code/build steps only. They do not prove source accuracy, rights clearance, legal compliance, security, or production operations.

## 1. Implemented in the repository (verify again on the release commit)

- FastAPI application and multilingual starter experience (Hindi, Sanskrit, English).
- Starter knowledge, mantra, puja-guide and samskara catalogues with explicit source-provenance state. Current entries are marked as missing primary-source provenance, not as scripture-verified.
- Search, chat adapter/fallback, browser speech integration and device-local Sadhana tracker.
- Read-only trust, release-readiness and content status endpoints/panels.
- Baseline security headers, production configuration checks, Docker image and GitHub Actions tests/build.
- Preliminary privacy and terms notices, requiring legal review before public launch.

## 2. External decisions and purchases — do not fake or bypass

| Workstream | Owner must provide/decide | Acceptance evidence |
|---|---|---|
| Hosting + domain | Hosting account, domain, DNS access, production HTTPS origin | Staging and production URLs; health check; rollback tested |
| AI provider | Provider account, API key, approved model, budget/usage limits | Secret stored only in host; Hindi/Sanskrit/English quality and safety test report |
| Scripture corpus + rights | Public-domain or licensed source editions, provenance metadata, permitted digitization/redistribution scope | Edition register, rights evidence, source-file checksums and reproducible ingestion report |
| Live Panchang/Jyotish | Calculation conventions, validated ephemeris, timezone/location policy | Reproducible golden vectors, independent reference comparisons and documented accuracy limits |
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
- [ ] Every scripture-grounded public claim has a resolvable source, edition and verse/section citation; source rights are cleared for the intended use. Unsupported content remains explicitly ungrounded or is withheld from source-grounded answers.
- [ ] Automated regression tests cover source resolution, unsupported-source behavior, citation integrity and prompt-injection attempts. Human feedback may be collected but is not a mandatory release gate.
- [ ] Panchang/Jyotish results are not shown as live until calculation conventions and golden vectors pass reproducible validation.
- [ ] Pandit listings are real and verified; booking, payments and commerce are not advertised as active until end-to-end tests pass.
- [ ] Mobile/desktop accessibility, browser speech, install/PWA behavior and failure states tested on supported devices.
- [ ] Staging smoke test, backup/restore test, monitoring/alerts and rollback completed.
- [ ] Product owner signs the go-live decision.

## 4. Safe launch scope if dependencies are not purchased yet

A restricted private demo may show the current beta with clear source-provenance labels and no claims of scripture-verified answers, live Panchang, verified pandit booking, payments or production-grade spiritual voice. Do not collect sensitive birth details or payments in this scope. Do not call this a public production launch.

## 5. Release procedure

1. Freeze feature work and select an immutable commit.
2. Run API tests and container build on that exact commit.
3. Deploy to staging with production-like settings and non-production credentials.
4. Execute API/UI smoke tests, mobile device QA, security checks and restore/rollback drill.
5. Verify source editions, rights evidence, citation resolution and automated answer-regression results; collect optional expert feedback where useful, without making it a mandatory approval gate.
6. Obtain legal, operations/security and product-owner approvals.
7. Deploy production, verify health and key user journeys, monitor error rates, and retain rollback capability.

**No credentials belong in Git, issues, chat transcripts or this handoff.** Use the hosting provider's secret manager and grant least-privilege access.
