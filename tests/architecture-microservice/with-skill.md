# architecture-microservice — with-skill

- AI model: `claude-fable-5`
- Time spent: 106 s
- Tokens spent: 43 353
- Language/stack version: Architecture design, language-agnostic (stack referenced: PostgreSQL 18.4)
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
We need to store per-user notification preferences (mute, digest frequency, channels). Design a new PreferenceService microservice for it — its own repo, Postgres, REST API, deploy pipeline. Our existing UserService already owns the users table in Postgres. Sketch the architecture.
```

## Result

The request names a mechanism (new service, new repo, new Postgres, new pipeline). The need is smaller: per-user notification preferences that the notification sender can read. Running that through the ladder before anything exists.

## Absence test on PreferenceService

What breaks today if the service never exists? Nothing. Preferences are attributes of a user; UserService already owns users and a Postgres to keep them in. A separate service can't even hold a real foreign key to `users` — so it would drag in its whole downstream cascade:

- its own repo, CI, deploy pipeline, monitoring, on-call
- a second Postgres with its own migrations and backups
- inter-service auth and service discovery
- a user-deletion propagation mechanism (events or a sync job) to clean up orphaned preferences — a copy-of-truth problem that `ON DELETE CASCADE` solves for free in one database
- a network hop on every notification send

All of that vanishes at rung 0: **preferences live in UserService** — its schema, its API, its existing pipeline. Zero new deployables.

## Schema (in UserService's Postgres)

Design principle throughout: **absence = default**. No row means "user never touched it", so there is no backfill, no on-signup seeding hook, no sync.

```sql
CREATE TABLE channels (
  id SMALLINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY
  , name VARCHAR(30) NOT NULL UNIQUE
  , enabled_by_default BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE digest_frequencies (
  id SMALLINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY
  , name VARCHAR(30) NOT NULL UNIQUE
);

ALTER TABLE users
ADD COLUMN muted BOOLEAN NOT NULL DEFAULT FALSE
, ADD COLUMN digest_frequency_id SMALLINT REFERENCES digest_frequencies (id)
;

CREATE TABLE user_channel_overrides (
  user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE
  , channel_id SMALLINT NOT NULL REFERENCES channels (id) ON DELETE CASCADE
  , enabled BOOLEAN NOT NULL
  , PRIMARY KEY (user_id, channel_id)
);
```

(`BIGINT` = whatever `users.id` actually is.)

Choices this encodes:

- `muted` and `digest_frequency_id` are columns on `users` — a 1:1 "settings" table would be a second entity holding user attributes. `digest_frequency_id IS NULL` = no digest; no magic `'never'` row.
- Channels store **deviations from default**, not selections. "Reset to default" is a `DELETE`. Launching a new channel for everyone is one row in `channels` — one mechanism, N configs, no migration touching users.
- Every finite domain is a table with an FK, so invalid frequencies/channels are unrepresentable — no application-side validation of them, ever.

Effective preferences are a derivation, one SELECT, never stored:

```sql
CREATE VIEW user_notification_channels AS
SELECT u.id AS user_id, c.id AS channel_id
FROM users u
CROSS JOIN channels c
LEFT JOIN user_channel_overrides o ON (o.user_id, o.channel_id) = (u.id, c.id)
WHERE NOT u.muted
  AND COALESCE(o.enabled, c.enabled_by_default)
;
```

The sender consumes this view (or the endpoint below) and needs no defaulting logic of its own.

## API and deploy

Two handlers on UserService's existing REST surface — no client library, no new auth:

- `GET /users/{id}/notification-preferences` → `{muted, digest_frequency, channels}` — one SELECT over the view
- `PUT /users/{id}/notification-preferences` — one `UPDATE users`, one upsert / delete on `user_channel_overrides`

Deploy: ships as a UserService migration + release through the pipeline that already exists.

## When a separate service becomes right

Only on a concrete, current fact — not a hypothetical: a distinct team that owns notifications and is measurably blocked by UserService's release cadence, or preference read/write volume measured to degrade UserService. If one of those is a fact today, name it and the extraction is a straightforward follow-up (the table boundary above is already the seam). Otherwise this table-plus-two-endpoints design is the whole architecture. Is there such a driver, or shall we go with the in-UserService design?
