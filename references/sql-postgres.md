# SQL / Postgres — Ladder Instantiation

Hard rules. "It feels more natural in plpgsql" is not a reason.

## Rungs in SQL

- **1 Structure.** Finite-domain values are rows referenced by FK, not text: comparison becomes an equality join; numbers live in numeric columns; IDs join things — humans get names via a label table. Validating data your own schema produced means the schema is wrong, not the data.
- **2 Declaration.** Unique/expression index (CASE allowed, `NULLS NOT DISTINCT`), CHECK, composite FK. Key trick — denormalize the parent discriminator into the child: `FOREIGN KEY (parent_id, kind) REFERENCES parent (id, kind) ON UPDATE CASCADE`, so the parent's attribute participates in the child's constraints; racy "IF single THEN update ELSE insert" trigger logic becomes one race-free upsert against a declarative index.
- **3 Derivation.** A subsystem's whole semantics is ONE SELECT over the full cross join of its domains. The only sanctioned cache: derived table + refresh trigger + reconciliation test against that reference query — never a second source of truth.
- **4 Reaction.** Triggers maintain derived data only — never business rules a constraint could hold, never destruction of user-entered data.

## Hard rules

- **DML is the API.** Never wrap a single INSERT/UPDATE/upsert in a function — a wrapper is a second API to keep in sync. Tables + GRANT/RLS with column lists (`GRANT INSERT (col1, col2) ON t`) are the stable API. Functions exist only for multi-statement orchestration or to expose a read-side relation.
- **One relation, not N getters.** A parameterless set-returning function or view; callers restrict with WHERE. No scalar getters (`is_visible(user, item)`), no chains of tiny functions: the unit of composition is the query (CTEs in one statement) — function ladders blind the planner and scatter semantics. Verify inlining and predicate pushdown with EXPLAIN.
- **Set-based, single-statement.** `IF TG_OP = 'DELETE' THEN OLD ELSE NEW` plumbing → `COALESCE(NEW.col, OLD.col)` in one statement; PERFORM-per-row → one INSERT ... SELECT; check-then-act → upsert.
- **One mechanism, N configs.** Exclusion = weight 0, not a special rule; N actor kinds = one supertype table, so one fact table serves all.

## Red flags

- `CREATE FUNCTION` around one DML statement
- A regex or safe-cast on data your own schema produced
- `IF TG_OP = ...` branches, check-then-insert, or per-row PERFORM in a trigger
- A parameterized getter where a relation + WHERE would do
- Correctness depending on trigger firing order
