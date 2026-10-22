# Team plan: five members

1. Team lead/integrator: repository, issues, reviews and demo.
2. Flask/API developer: URL validation, shorten endpoint and redirects.
3. Supabase developer: schema, setup and database verification.
4. Frontend developer: public page, request form, admin UI and responsive CSS.
5. QA/security/deployment: tests, secrets review, Vercel deployment and acceptance checks.

## Five-day sprint
- Day 1: scope, schema, API contract, repository and tasks.
- Day 2: key requests, admin login, immediate issuance and revocation.
- Day 3: shorten API, redirect and frontend integration.
- Day 4: end-to-end tests, mobile checks and security review.
- Day 5: deploy, verify Supabase, fix blockers and demo.

## Acceptance criteria
- No user signup required.
- Admin approves/rejects requests and revokes issued keys.
- Key secret is shown once; only SHA-256 hash is stored.
- Invalid/revoked keys cannot create links.
- Short URLs redirect to destinations.
- Supabase service-role key never appears in frontend or Git.
