
# LinkSwift URL Shortener MVP

A simple URL shortener that automatically generates an active API key when a user requests access. Admins can monitor keys, short links and click counts, optionally set an expiry date, or revoke access at any time.

## Stack
Python, Flask, Supabase PostgreSQL, HTML/CSS/JavaScript, Vercel.

## Setup
1. Create a Supabase project and run `schema.sql` in its SQL Editor.
2. Install Python 3.11+, then run:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ADMIN_PASSWORD`, `FLASK_SECRET_KEY`, and `BASE_URL` in your environment. Never commit `.env`.
4. Run `flask --app app run --debug` and open http://127.0.0.1:5000.
5. For Vercel, push to GitHub, import the repo, add the environment variables in Vercel settings, and deploy. Check current Vercel Python/Flask docs if runtime configuration has changed.

## User flow
1. Visitor submits name/email and an optional use case at `/`. An active API key is generated immediately.
2. The key is hashed for authentication and temporarily encrypted server-side so it can be displayed to the requester in the same browser session. The raw key is never stored in plaintext in the database.
3. The requester copies and saves the key, then uses it on the site or in their own app.
4. Admin logs in at `/admin` to monitor issued keys, link creation and redirect clicks. Admin can set an optional expiry date or revoke a key at any time.
5. Expired and revoked keys cannot create new short links. Existing short links continue redirecting unless separately disabled.

## API
`POST /api/shorten` with `Content-Type: application/json`, `X-API-Key: lks_your_key`, body `{"url":"https://example.com/a/long/path"}`.

Example:
```bash
curl -X POST "https://your-domain.vercel.app/api/shorten" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: lks_your_key" \\
  -d '{"url":"https://example.com/a/long/path"}'
```

Successful response is HTTP 201 with `short_url`, `code`, and `original_url`. Invalid, revoked, or expired keys receive HTTP 401.

## Limitations
- The issued key is displayed to the requester while the request page is open; keep the same browser session open until you copy the key. If the key is lost after acknowledgement, add a key-rotation/reissue workflow. Expiry dates are interpreted as the end of the selected date in UTC.
- Revocation blocks new links, but existing links continue redirecting.
- Add rate limiting, abuse/spam protection, CSRF protection and stronger admin authentication before public production use.
- Supabase service-role key is privileged: keep it server-side only.
- Run tests with `python -m pytest -q` after installing dependencies.

# API Key Management Service

## Project Summary
**Category:** Backend & APIs  
**Difficulty:** Intermediate  
**Suggested team split:** Key generation, authentication, permissions, audit logs 

## Description
This project is a good fit for a small team that wants to build something real and usable in a short amount of time. It focuses on one clear feature, clean data flow, and a simple user experience that can be demoed without extra fluff. The goal is to turn a good idea into a working MVP with a solid backend, a basic interface, and a realistic set of edge cases.

## Scope
Issue, revoke, and expire API keys; enforce scopes and log usage.

## Core Features
- Deliver the main user flow from start to finish.
- Support the required data model and user interactions.
- Handle validation, edge cases, and error states cleanly.
- Include basic monitoring, feedback, or reporting where relevant.
- Make the app easy to explain during a live demo.

## Deliverables
- A working deployed application or API demo
- A clear README with setup instructions and environment variables
- A minimal database schema or data model definition
- UI screens or API endpoints for the core MVP
- A basic test strategy covering the happy path and one major failure path
- A short demo script explaining the architecture, choices, and trade-offs

## Suggested Architecture
- Frontend: simple dashboard, form-based interface, or lightweight visual layer
- Backend: API or service layer for business logic and validation
- Data layer: database, in-memory persistence, or structured file storage for MVP use
- Optional extras: auth, async jobs, scheduling, WebSockets, caching, or notifications depending on the project

## Learning Outcomes
Authentication, authorization, secure token handling

## Recommended MVP Checklist
1. Define the main user flow and success criteria.
2. Build the data model and core backend logic.
3. Connect the UI or client to the main application flow.
4. Add key validation, security checks, and realistic error states.
5. Test the happy path and at least one important edge case.
6. Deploy the app and document the setup clearly.

## Free Deployment Options
Render, Railway, Fly.io, Cloud Run, or Supabase for database features.

## Good Free Hosting Choices
- Static frontend: Vercel, Netlify, or GitHub Pages
- API/backend: Render, Railway, or Fly.io
- Database/realtime services: Supabase, Neon, Firebase, or Cloudflare D1
- Documentation/demo pages: GitHub Pages, Cloudflare Pages, or Vercel

## Typical Tech Stack
- Frontend: React, Next.js, plain HTML/JS, or similar lightweight UI tooling
- Backend: Node.js, Python (Flask/FastAPI), or Java/Spring Boot
- Database: Postgres, SQLite, Supabase, or a simple file-based store
- Real-time layer: WebSockets, polling, or background workers if needed

## Final Demo Expectations
- Provide a working URL with sample or seeded data
- Show one clear end-to-end flow from start to finish
- Explain the most important technical decisions and trade-offs
- Include screenshots, screen recordings, or a brief live walk-through
- Highlight what was completed in the MVP and what would be next if the project continued

## Next Improvements
- Add authorization, auditing, or stronger validation
- Improve test coverage and resilience
- Add analytics, metrics, or observability
- Expand functionality once the core MVP is stable
dfa1529c8e093116961e19e3cc894950c83ee4aa
