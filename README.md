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
