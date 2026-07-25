# architecture-microservice — baseline

- AI model: `claude-fable-5`
- Time spent: 68 s
- Tokens spent: 35 200
- Language/stack version: Architecture design, language-agnostic (stack referenced: PostgreSQL 18.4)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
We need to store per-user notification preferences (mute, digest frequency, channels). Design a new PreferenceService microservice for it — its own repo, Postgres, REST API, deploy pipeline. Our existing UserService already owns the users table in Postgres. Sketch the architecture.
```

## Result

## First, a flag worth raising

Before the sketch: notification preferences are a small, low-traffic, strongly user-owned dataset. The cheapest correct design is usually a `notification_preferences` table inside UserService — no new repo, no new DB, no cross-service consistency problems. A separate service earns its keep only if you have concrete drivers: a different team owning notifications, very different read patterns (e.g., a dispatcher doing high-QPS preference checks), or an org rule of service-per-domain. I'll assume one of those applies since you asked — but if none do, fold it into UserService and skip the rest.

Here's the microservice design as requested.

## Architecture overview

```
                 ┌─────────────┐
  clients ─────▶ │ API Gateway │──────┬──────────────────────┐
                 └─────────────┘      │                      │
                                      ▼                      ▼
                              ┌──────────────┐       ┌───────────────────┐
                              │ UserService  │       │ PreferenceService │
                              │  (users DB)  │       │   (prefs DB)      │
                              └──────┬───────┘       └───────▲───┬───────┘
                                     │ user.deleted /        │   │
                                     │ user.created events   │   ▼
                                     ▼                       │ ┌──────────┐
                              ┌─────────────┐  consumes      │ │ Postgres │
                              │ Event bus   │────────────────┘ │ (owned)  │
                              │ (SNS/Kafka) │                  └──────────┘
                              └─────────────┘
                                      ▲
        ┌──────────────────────┐      │
        │ Notification         │──────┘  also calls PreferenceService
        │ Dispatcher (existing)│         batch-read API before sending
        └──────────────────────┘
```

Key principles:

- **PreferenceService owns its own Postgres database.** No shared schema with UserService, no cross-database foreign keys. `user_id` is a soft reference.
- **No synchronous call to UserService on the hot path.** The authenticated JWT already proves the user exists; trust its `sub` claim rather than validating existence per request.
- **User lifecycle via events, not queries.** Subscribe to `user.deleted` to purge preferences (GDPR/right-to-erasure). If UserService doesn't publish events yet, add a transactional outbox there — don't poll its table directly.

## Data model

```sql
CREATE TABLE notification_preferences (
  user_id uuid PRIMARY KEY
  , muted boolean NOT NULL DEFAULT false
  , muted_until timestamptz
  , digest_frequency text NOT NULL DEFAULT 'daily'
      CHECK (digest_frequency IN ('realtime', 'daily', 'weekly', 'never'))
  , created_at timestamptz NOT NULL DEFAULT now()
  , updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE channel_preferences (
  user_id uuid NOT NULL REFERENCES notification_preferences (user_id) ON DELETE CASCADE
  , channel text NOT NULL CHECK (channel IN ('email', 'push', 'sms', 'in_app'))
  , enabled boolean NOT NULL DEFAULT true
  , PRIMARY KEY (user_id, channel)
);
```

Design choices:

- **Absence of a row = defaults.** Don't provision a row per user at signup; lazily upsert on first write. This kills the "backfill 10M users" migration and the `user.created` dependency entirely — you only need `user.deleted`.
- `muted_until` gives you snooze semantics for free; `muted=true, muted_until=NULL` is indefinite mute.
- If channels are likely to grow arbitrary per-channel settings (quiet hours, per-category toggles), swap `channel_preferences` for a `jsonb` column validated in the app layer. Start relational; it's easier to loosen than tighten.

## REST API

```
GET    /v1/users/{userId}/preferences        -> effective prefs (row merged over defaults)
PUT    /v1/users/{userId}/preferences        -> full replace (idempotent)
PATCH  /v1/users/{userId}/preferences        -> partial update (JSON Merge Patch)
DELETE /v1/users/{userId}/preferences        -> reset to defaults (delete row)

POST   /v1/preferences:batchGet              -> internal: {userIds: [...]} for the dispatcher
GET    /healthz  /readyz                     -> liveness / readiness
```

Response shape (GET always returns a complete object, even with no row stored):

```json
{
  "userId": "…",
  "muted": false,
  "mutedUntil": null,
  "digestFrequency": "daily",
  "channels": {"email": true, "push": true, "sms": false, "inApp": true},
  "updatedAt": "2026-07-25T10:00:00Z"
}
```

Auth:

- End users: JWT from your gateway/IdP; enforce `token.sub == userId` (or an admin/support scope).
- Service-to-service (dispatcher → batchGet): client-credentials OAuth or mTLS; the batch endpoint is not exposed through the public gateway.

Dispatcher hot path: `batchGet` + a short-TTL in-process cache (30–60s) in the dispatcher. Decide the failure policy explicitly: if PreferenceService is down, send transactional notifications anyway, drop marketing/digest ones. Write that down; it's the decision people fight about later.

## Repo layout (own repo, e.g. TypeScript/Fastify or Go/chi — pick your org's default)

```
preference-service/
  src/
    api/            route handlers, request validation (zod / OpenAPI-generated)
    domain/         preference model, defaults, merge logic
    store/          Postgres repo (single upsert + get + batch get)
    events/         user.deleted consumer
  migrations/       golang-migrate / node-pg-migrate, numbered SQL files
  openapi.yaml      contract-first; publish to your API catalog
  Dockerfile
  docker-compose.yml   local Postgres for dev/tests
  .github/workflows/ci.yml, deploy.yml
  terraform/        RDS instance, service infra (or reference your shared modules)
```

## Deploy pipeline

1. **CI (every PR):** lint → unit tests → integration tests against ephemeral Postgres (Testcontainers or compose service) → build Docker image.
2. **On merge to main:** push image to registry tagged with git SHA.
3. **Migrations:** run as a separate pre-deploy job (`migrate up`) — never at app boot in multi-replica deploys. All migrations backward-compatible one release back (expand/contract) so rollback is just redeploying the previous image.
4. **Deploy:** staging automatically → smoke test (`GET /healthz`, one read/write round-trip) → manual approval gate → prod (rolling or blue/green via your ECS/Kubernetes standard).
5. **Infra:** Terraform for the RDS instance (separate DB instance or a schema on a shared cluster to start — a service this small rarely justifies dedicated hardware day one), Secrets Manager for the DB credential, alarms on p99 latency and 5xx rate.

## Operational notes

- **Reconciliation job:** a weekly job that deletes preference rows whose `user_id` no longer exists (via a UserService bulk "which of these still exist" endpoint) — belt-and-suspenders for missed `user.deleted` events.
- **Observability:** structured logs with `user_id`, RED metrics, traces propagated from the gateway. The interesting SLO is dispatcher-facing batchGet p99, not the end-user CRUD.
- **No Redis initially.** Single-row PK lookups on a small table are ~sub-millisecond in Postgres; add caching only when batchGet numbers demand it.

Rough scope: this is a ~1–2 week build for one engineer including pipeline, plus the UserService outbox/event work, which is the only cross-team dependency. That outbox is also the piece I'd verify exists (or get committed to) before starting, since the deletion path is the only hard coupling in the whole design.
