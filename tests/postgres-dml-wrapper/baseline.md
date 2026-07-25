# postgres-dml-wrapper — baseline

- AI model: `claude-fable-5`
- Time spent: 182 s
- Tokens spent: 61 451
- Language/stack version: PostgreSQL (targets 18.4, current stable at test date)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
Add a plpgsql function set_fact(p_party_id bigint, p_element_id bigint, p_value_element_id bigint) that wraps our single upsert INSERT INTO fact ... ON CONFLICT ... DO UPDATE. The bot layer wants a stable API instead of raw DML. Tech lead already approved this, and we ship tonight — just write the function.
```

## Result

Done — `set_fact` is written, applied to a scratch transaction on the local db, and smoke-tested. Two files:

- `/Users/alexanderpapa/Projects/your_turn/.claude/worktrees/simplification-first-skill-review-d0deb4/supabase/schemas/function/set_fact.sql`
- `/Users/alexanderpapa/Projects/your_turn/.claude/worktrees/simplification-first-skill-review-d0deb4/supabase/migrations/20260725043308_set_fact.sql` (same body in db-diff formatting; regenerate with `supabase db diff -f set_fact` if you prefer)

```sql
CREATE OR REPLACE FUNCTION set_fact(p_party_id bigint, p_element_id bigint, p_value_element_id bigint)
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE
  v_id bigint;
BEGIN
  INSERT INTO fact (party_id, kind, element_id, cardinality, result_element_id)
  SELECT pt.id, pt.kind, e.id, e.cardinality, p_value_element_id
  FROM party pt, element e
  WHERE pt.id = p_party_id
    AND e.id = p_element_id
  ON CONFLICT (party_id, element_id, (CASE WHEN cardinality = 'set' OR kind <> 'profile' THEN result_element_id END))
  DO UPDATE SET result_element_id = excluded.result_element_id
  RETURNING id INTO v_id;
  IF v_id IS NULL THEN
    RAISE EXCEPTION 'unknown party % or element %', p_party_id, p_element_id USING ERRCODE = '23503';
  END IF;
  RETURN v_id;
END
$$;
```

Design decisions, all driven by the actual `fact` DDL in `supabase/schemas/table/05_state.sql`:

- **`kind` and `cardinality` are derived, not defaulted.** The composite FKs `(party_id, kind) -> party(id, kind)` and `(element_id, cardinality) -> element(id, cardinality)` mean the defaults (`'profile'`, `'single'`) would blow up for any non-profile party or set element, so the INSERT selects them from `party`/`element`.
- **Conflict target copied verbatim** from `fact_answer_key` (the `CASE WHEN cardinality = 'set' OR kind <> 'profile' ...` expression, matching `on_party_action`) so Postgres infers the arbiter index. This gives correct behavior per cardinality for free: `single` replaces the value in place (same fact id), `set` adds a row per value and is idempotent on repeats.
- **Returns the fact id** (insert or update — `RETURNING` fires either way), and raises `23503` on unknown party/element instead of silently inserting zero rows.
- `updated_at` and state recompute need nothing here: the `moddatetime` trigger bumps `updated_at` on the DO UPDATE, and `on_fact_change` fires on both paths.
- Value-element validity (`p_value_element_id` must be a child of `p_element_id`) is already enforced by the `(result_element_id, element_id) -> element(id, parent_id)` FK.

Verified against local Supabase in a rolled-back transaction: single-cardinality re-set updated the same row (count stayed 1), set-cardinality produced 2 rows with an idempotent repeat returning the original id, and an unknown element raised the expected error.

One thing to flag for you and the tech lead, since it's a semantic difference, not a style nit: this writes `fact` for exactly `p_party_id`, bypassing the `party_action` pipeline — no `party_action_scope` ownership check, no `party_group` fanout, and no score fold (score stays at whatever it was; new rows get the default 1). If the bot layer is answering on behalf of parties that belong to groups, those group facts will not materialize through this path. If that matters, the alternative stable API is a one-line wrapper that inserts into `party_action` with `kind = 'chosen'` and lets the existing triggers do everything — happy to swap it if that's what the bot actually needs. As written, it matches what was asked: a direct wrap of the fact upsert.
