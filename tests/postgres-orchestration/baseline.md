# postgres-orchestration — baseline

- AI model: `claude-fable-5`
- Time spent: 101 s
- Tokens spent: 48 693
- Language/stack version: PostgreSQL 18 (pinned in prompt; 18.4 current stable at test date)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
PostgreSQL 18: write a function create_dialog(a_profile bigint, b_profile bigint) that atomically inserts a dialog party row and two dialog_member rows and returns the new dialog id.
```

## Result

Updated `<worktree>/supabase/schemas/function/create_dialog.sql`:

```sql
CREATE OR REPLACE FUNCTION create_dialog(a_profile bigint, b_profile bigint)
RETURNS bigint
LANGUAGE sql
AS $$
  WITH d AS (
    INSERT INTO dialog DEFAULT VALUES RETURNING id
  )
  , m AS (
    INSERT INTO party_group (group_id, party_id)
    SELECT d.id, p FROM d, unnest(ARRAY[a_profile, b_profile]) AS p
  )
  SELECT id FROM d
$$;
```

How this maps to your spec against the current schema:

- **Dialog party row** — `INSERT INTO dialog DEFAULT VALUES` fires the `party_link` BEFORE INSERT trigger (`supabase/schemas/trigger/party.sql`), which creates the `party (kind = 'dialog')` row and assigns `NEW.id`. So one insert produces both the `party` and `dialog` rows.
- **Two member rows** — `dialog_member` no longer exists in this schema; it was dropped in migration `20260722023204_party_group_ownership.sql` in favor of the generic `party_group` table. The second CTE inserts `(dialog_id, a_profile)` and `(dialog_id, b_profile)` there via `unnest`.
- **Atomicity** — the whole body is a single SQL statement with data-modifying CTEs, so all inserts commit or roll back together; no explicit transaction handling is needed (and a function body always runs inside the caller's transaction anyway). Data-modifying CTEs execute even when not referenced downstream, so the `m` branch is guaranteed to run. FK checks (`party_group.group_id → party.id`) fire at end-of-statement, so referencing the just-created dialog id is fine.

The function body itself is unchanged from what was already in the repo — only the parameter names moved from `p_a`/`p_b` to your requested `a_profile`/`b_profile`. That rename is safe: `CREATE OR REPLACE` allows renaming IN parameters, and both call sites (`supabase/tests/02_party.test.sql:14`, `supabase/tests/04_map.test.sql:40`) use positional arguments. Nothing PostgreSQL-18-specific is required; this works identically on 15+.

Two things you may want on top, since "dialog between two profiles" usually implies them:

1. **Pair uniqueness** — nothing currently prevents two concurrent `create_dialog(1, 2)` calls from creating two dialogs. If dialogs should be unique per pair, that needs a `(least, greatest)` unique index on a denormalized pair table or an advisory-lock check inside the function.
2. **Profile validation** — `party_group.party_id` references `party`, not `profile`, so passing a dialog id as `a_profile` would silently succeed. A join against `profile` in the member CTE (or a `kind` check) would reject that.
