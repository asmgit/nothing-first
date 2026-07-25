# postgres-orchestration — with-skill

- AI model: `claude-fable-5`
- Time spent: 115 s
- Tokens spent: 51 292
- Language/stack version: PostgreSQL 18 (pinned in prompt; 18.4 current stable at test date)
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
PostgreSQL 18: write a function create_dialog(a_profile bigint, b_profile bigint) that atomically inserts a dialog party row and two dialog_member rows and returns the new dialog id.
```

## Result

Nothing to write — this function already exists and already satisfies the request. Per the nothing-first ladder this lands on rung 0: the need is covered by existing entities, so adding another one (or a twin table) would be pure liability.

What exists, verified in the repo:

**`<worktree>/supabase/schemas/function/create_dialog.sql`** — declared in migrations `20260721225459_init.sql` and `20260722023204_party_group_ownership.sql`, exercised by `supabase/tests/02_party.test.sql` and `04_map.test.sql`:

```sql
CREATE OR REPLACE FUNCTION create_dialog(p_a bigint, p_b bigint)
RETURNS bigint
LANGUAGE sql
AS $$
  WITH d AS (
    INSERT INTO dialog DEFAULT VALUES RETURNING id
  )
  , m AS (
    INSERT INTO party_group (group_id, party_id)
    SELECT d.id, p FROM d, unnest(ARRAY[p_a, p_b]) AS p
  )
  SELECT id FROM d
$$;
```

How the request's named mechanisms map onto existing entities:

- **"dialog party row"** — not inserted by the function, and shouldn't be: the `party_link` BEFORE INSERT trigger on `dialog` (`supabase/schemas/trigger/party.sql`) creates the `party` row and stamps `NEW.id`. Inserting it in the function too would duplicate that mechanism.
- **"two dialog_member rows"** — there is no `dialog_member` table; membership is `party_group`, one relation serving every party kind (dialog, group, the global group). Creating `dialog_member` would be a hand-rolled twin of `party_group` — red flag, one mechanism with N configs already covers it.
- **"atomically"** — the body is a single statement with data-modifying CTEs; single statement = atomic, no explicit transaction machinery needed. A self-dialog (`a = b`) aborts the whole statement via the `party_group` PK, so no guard is needed either.
- **"returns the new dialog id"** — the final `SELECT id FROM d`.

The only delta from your requested signature is parameter names (`p_a, p_b` vs `a_profile, b_profile`). All current callers pass positionally, so renaming changes nothing today; it only becomes an API change if the function is exposed as a named-param RPC — rename then, when that's a fact.
