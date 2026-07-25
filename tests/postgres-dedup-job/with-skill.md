# postgres-dedup-job — with-skill

- AI model: `claude-fable-5`
- Time spent: 73 s
- Tokens spent: 44 198
- Language/stack version: PostgreSQL (targets 18.4, current stable at test date)
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
We keep getting duplicate signups (same email, different casing/whitespace). Write a nightly cleanup job that scans the users table, groups by normalized email, keeps the oldest row and deletes the rest. Also a Slack alert with the count.
```

## Result

There is no app-level `users`/email table in this repo (identities here are provider enums), so here is the design I would apply to the real table.

The nightly job is the wrong rung — it polices what a constraint can forbid. Running the request through the ladder:

**The need is "at most one account per normalized email". One declarative entity covers it forever:**

```sql
CREATE UNIQUE INDEX users_email_key ON users (lower(btrim(email)));
```

This forbids future duplicates race-free, including two concurrent signups in the same millisecond — a nightly sweep leaves a 24-hour duplicate window and loses that race by design.

**Existing duplicates are a one-time repair, not a recurring job** — same migration, immediately before the index:

```sql
WITH ranked AS (
  SELECT id
    , ROW_NUMBER() OVER (PARTITION BY lower(btrim(email)) ORDER BY created_at, id) AS rn
  FROM users
)
DELETE FROM users
WHERE id IN (SELECT id FROM ranked WHERE rn > 1)
;
```

**The Slack alert deletes itself.** Once the index exists, the nightly count is provably always zero — a monitor guaranteed to report zero is dead machinery. The one number you actually care about (rows the repair removed) is the DELETE's row count in the migration output. After that, a duplicate attempt surfaces as a unique violation at signup time — map it to "account already exists" in the signup handler, and failures land in your existing error tracking. No scheduler, no job code, no Slack webhook, no runbook to own.

Two checks before running the repair:

1. If duplicate rows own child data (orders, sessions, etc.), a bare DELETE either fails on the FK or cascades their data away. Re-point children to the kept row first — one `UPDATE child SET user_id = <keeper> WHERE user_id IN (<losers>)` per referencing table; list them from `pg_constraint`.
2. Also lowercase/trim in the signup path so stored values are canonical for display — but the index remains the enforcement either way; the app-side normalization is cosmetic, not a guard.

If a concrete driver ever exceeds the constraint (e.g., soft-deleted rows must be exempt), that is a `WHERE deleted_at IS NULL` on the same index — still not a job.
