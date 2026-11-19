# Secure Admin & Acharya Content Workflow

## Current implementation status

The public API exposes a read-only policy at `GET /api/content/review-policy`. There is intentionally no public create, update, approve, reject, reviewer-login or admin endpoint. The browser must not be treated as an authorization boundary. The content-review JSON Schema in `schemas/content-review.schema.json` defines the metadata contract for a future authenticated workflow; a schema-valid record is not an approval.

## Roles to implement before enabling writes

- **Content editor:** drafts and edits content; cannot approve their own changes.
- **Acharya reviewer:** records source evidence, tradition context, qualification, individual checks and a decision.
- **Publisher:** a separate authorized role that can publish only an approved, immutable revision.
- **Security administrator:** manages accounts, MFA, role assignments, key rotation and incident response; cannot silently alter review history.

Require least privilege, MFA for privileged users, short-lived sessions, secure HttpOnly/Secure/SameSite cookies, CSRF protection, server-side authorization on every mutation, rate limits and login lockout/abuse monitoring. Never store passwords, API keys or session tokens in browser local storage or Git.

## Required publication controls

1. Every content change creates a new revision with a stable content ID and a cryptographic hash.
2. Record source title, author/tradition, edition/publication, page/section, language and sampradaya/region.
3. Review mantra wording, translation, ritual steps and regional context as separate checks.
4. Record reviewer identity, qualification, timestamp, decision and notes.
5. Enforce separation of duties: author cannot approve own revision; publisher cannot bypass approval.
6. Approved revision is immutable; corrections create a new revision and new review.
7. Store append-only audit events for draft, edit, review, approval, rejection, publication, role change and access denial.
8. Public catalogue exposes only explicitly published revisions; all other content stays draft and visibly marked as requiring Acharya review.

## Production dependencies

Before enabling this console, choose and configure a managed identity provider or audited authentication service, a persistent database, encrypted backups, a secrets manager, TLS hosting, monitoring and an incident-response owner. Complete a threat model, penetration test, privacy/legal review and restore drill. Do not implement a homemade password system as a shortcut.

## Acceptance tests for the future write workflow

- Unauthenticated and wrong-role users receive 401/403 on every mutation.
- CSRF, replay, stale revision and cross-tenant access attempts are rejected.
- Author self-approval and publish-before-approval are rejected server-side.
- Every accepted or rejected mutation creates an audit record.
- A failed database transaction never leaves a partially published revision.
- Public endpoints never reveal private reviewer data or unpublished drafts.

## Current release blocker

This document and schema are implementation specifications only. They do not provide authentication, database persistence, reviewer verification, audit storage or a working admin dashboard. Do not claim the admin workflow is live until those dependencies and tests are complete.
