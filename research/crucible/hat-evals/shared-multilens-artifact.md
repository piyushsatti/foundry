# Plan: Public "share report" feature for the analytics dashboard

## Goal
Let a logged-in user generate a public link to one of their saved reports so they can send it to a client without the client needing an account.

## Context
Reports live in Postgres, one row per report, `reports(id, owner_id, title, body_json, created_at)`. The dashboard is a Next.js app with an existing session-cookie auth layer. Clients are external, unauthenticated.

## Design

### 1. Share token
When the owner clicks "Share", we generate a token and store it:

```
ALTER TABLE reports ADD COLUMN share_token TEXT;
-- token = md5(report_id || current_timestamp)
UPDATE reports SET share_token = md5(id::text || now()::text) WHERE id = $1;
```

The public URL is `https://dash.example.com/shared/<share_token>`.

### 2. Public fetch endpoint
`GET /api/shared/:token` looks the report up by token and returns it:

```
SELECT id, owner_id, title, body_json, created_at
FROM reports
WHERE share_token = $1;
```

The response is the full row serialized to JSON, sent to the unauthenticated client. No session check — that's the point, anyone with the link can read it.

### 3. Rendering
The public page is server-rendered. It takes the `:token` from the URL and interpolates the report title directly into the page heading:

```
<h1>Report: ${report.title}</h1>
```

Report titles are user-supplied free text.

### 4. Revocation
To un-share, the owner clicks "Unshare", which sets `share_token = NULL`. Any existing link stops working immediately.

### 5. Rollout
Ship it behind no flag — it's additive, existing reports just get a null token until shared. Deploy Friday afternoon so it's live for the weekend client demos.

## Success criteria
- [ ] Owner can generate a share link
- [ ] Anyone with the link sees the report
- [ ] Owner can revoke
- [ ] Link is hard to guess

## Out of scope
- Per-link expiry
- View analytics
- Password-protected links
