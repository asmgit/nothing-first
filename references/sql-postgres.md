# SQL / Postgres — Ladder Instantiation

Hard rules. "It feels more natural in plpgsql" is not a reason.

## Rungs in SQL

- **2 Structure.** Finite-domain values are rows referenced by FK, not text: comparison becomes an equality join; numbers live in numeric columns; IDs join things — humans get names via a label table. Validating data your own schema produced (a regex, a safe-cast) means the schema is wrong, not the data.
- **3 Declaration.** Unique/expression index (CASE allowed, `NULLS NOT DISTINCT`), CHECK, composite FK. Key trick — denormalize the parent discriminator into the child: `FOREIGN KEY (parent_id, kind) REFERENCES parent (id, kind) ON UPDATE CASCADE`, so the parent's attribute participates in the child's constraints; racy "IF single THEN update ELSE insert" trigger logic becomes one race-free upsert against a declarative index.
- **4 Derivation.** A subsystem's whole semantics is ONE SELECT over the full cross join of its domains. The only sanctioned cache: derived table + refresh trigger + reconciliation test against that reference query — never a second source of truth.
- **5 Reaction.** Triggers maintain derived data only — never business rules a constraint could hold, never destruction of user-entered data.

## Hard rules

- **DML is the API.** Never wrap a single INSERT/UPDATE/upsert in a function — a wrapper is a second API to keep in sync. Tables + GRANT/RLS with column lists (`GRANT INSERT (col1, col2) ON t`) are the stable API. Functions exist only for multi-statement orchestration or to expose a read-side relation.
- **One relation, not N getters.** A parameterless set-returning function or view; callers restrict with WHERE. No scalar getters (`is_visible(user, item)`), no chains of tiny functions: the unit of composition is the query (CTEs in one statement) — function ladders blind the planner and scatter semantics. Verify inlining and predicate pushdown with EXPLAIN.
- **Set-based, single-statement.** `IF TG_OP = 'DELETE' THEN OLD ELSE NEW` plumbing → `COALESCE(NEW.col, OLD.col)` in one statement; PERFORM-per-row → one INSERT ... SELECT; check-then-act → upsert; two-phase sync (SELECT then branch UPDATE/INSERT) that needs the action taken → `MERGE ... RETURNING merge_action()` (PG17+) — measured −40% time, −30 LOC on a sync procedure.
- **One supertype table.** N actor kinds = one supertype table — every table that references an actor then serves all kinds through one FK.
- **A materialized closure certifies reachability — delete the walk.** Applies whenever a transitive-closure table is maintained incrementally and an edge is removed (membership, org charts, permissions, BOM). Recursive *definition* does not force recursive *evaluation*: bound the affected set in closed form (`ancestors(u) × descendants(v)`), then keep a row iff a constant-size certificate exists — one direct edge crossing that boundary, its two legs being closure rows provably outside the box, so they cannot be casualties and the witness cannot be circular. Any surviving path of any length must cross that boundary, so three joins replace the walk; acyclicity makes one of the two filters free. Evidence: recursive CTE 22 833 ms → 6 ms, and 5870 random-DAG cuts plus 119 pgTAP tests with zero divergence from a reference walk.
