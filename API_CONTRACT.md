# API Contract

## Request API access
`POST /request-key` form fields: `name`, `email`, optional `reason`. An active API key is generated immediately when the request is submitted. The request record is marked `issued`.

## Issuance and admin controls
The key is generated automatically and is available to the requester in the same browser session. The database stores a hash for authentication and a temporary encrypted copy for one-time display. In `/admin`, the administrator can monitor usage, set or clear an optional expiry date, or revoke the key. Expiry dates apply through the end of the selected calendar day in UTC.

## Shorten a URL
`POST /api/shorten` with `Content-Type: application/json`, `X-API-Key: lks_your_key`, body `{"url":"https://example.com"}`.

Success: HTTP 201 with `short_url`, `code`, and `original_url`. Invalid, revoked, or expired keys receive HTTP 401.
