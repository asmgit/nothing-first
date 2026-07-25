---
name: nothing-first
license: MIT
description: Use for any development or design work — architecture (even with no code at all), schemas, APIs, functions, modules, configs, pipelines, in any language — whenever tempted to add a wrapper, helper, defensive guard, flag, or special case; on any simplify/refactor pass or over-engineering / premature-abstraction / YAGNI concern; after any solution works, before calling it done; and for all SQL/Postgres/Supabase schema, RLS, trigger, and query design. Goal: the best code is the code that does not exist.
---

# Nothing First

## Overview

**What is the best code? — The code that does not exist.** It has no bugs, costs nothing to read, test, maintain, or explain. Every line, concept, and mechanism is a liability; the feature is the asset. Second best: less code. The strongest change is a deletion, and a pass is measured by what it deletes. Before writing any mechanism, check whether the platform already provides it — constraint, type system, stdlib, framework API; reimplementing a platform mechanism is a modeling error.

The ladder below is the method: each rung down is more code you own, each rung up is work absorbed by data or platform. A change that deletes a concept beats a change that patches it. Distilled from real sessions where every correction climbed the ladder and most ended in deletion: races disappeared by design, whole bug classes became unrepresentable, semantics became visible in one place.

ALWAYS ON: in any language, and at pure architecture level with no code at all.

## The Ladder

Start every piece of logic at rung 0. Fall only when the current rung genuinely cannot express it — "it feels more natural in code" is not a reason.

0. **Nothing.** Does the concept need to exist at all? An existing relation, a row of config, a WHERE clause, or a platform feature may already express it. Never built — or deleted — is the goal reached: zero code, zero failure modes.
1. **Data model / types.** Make the invalid state unrepresentable. Finite-domain values are typed data (enum rows, numeric columns), not free strings or code branches. Storing answers as FKs to option rows instead of free text deleted an entire regex-guard layer in one move; validating data your own schema or types produced means the model is wrong, not the data.
2. **Declarative invariant.** Type system, schema validation, constraint, declarative framework API, config. SQL: unique/expression index (CASE allowed, `NULLS NOT DISTINCT`), CHECK, composite FK. Key trick: denormalize the parent discriminator into the child — `FOREIGN KEY (parent_id, kind) REFERENCES parent (id, kind) ON UPDATE CASCADE` — so the parent's attribute can participate in the child's constraints; racy "IF single THEN update ELSE insert" trigger logic becomes one race-free upsert against a declarative index.
3. **One pure transformation over the whole input.** SQL: a subsystem's whole semantics is ONE SELECT over the full cross join of its domains; caches and triggers are derived from it, never the truth themselves. Anything derivable from existing state belongs here — not in an event or effect handler.
4. **Reactive mechanism.** Trigger, event, watcher, hook: the system reacts to data changes, nobody has to remember to call anything. Only for reacting to external changes and maintaining derived data — never business rules a constraint could hold, never destroying user-entered data to keep a derived invariant convenient.
5. **Imperative glue.** Last resort, only for genuine multi-statement orchestration.

**Architecture level: count concepts, not lines.** One mechanism parameterized by data beats N special mechanisms; a component made unnecessary by enriching a neighbor's data model gets deleted. If correctness needs a paragraph about interleavings or firing order, you are on the wrong rung — climb back up.

## Iteration Protocol

Runs in two places: while designing — every piece starts at rung 0 and falls only as far as forced — and after a working solution, as a mandatory simplify-and-optimize pass before anything is called done. Deadline pressure defers applying a fix, never running the pass: name every finding, schedule every deferred deletion. Red-flag code is a failure mode, not aesthetics, and "skip the pass" is never among the options offered.

A pass asks of every unit: what reaches rung 0 — deletable outright? what climbs a rung? what did the latest change make unnecessary? If the pass substantially improved the result, run another; stop at the first pass without substantial improvement. One such loop deleted ten working functions — every deletion removed a failure mode with it.

Optimization obeys the same direction: prefer optimizations that also simplify (set-based rewrite, predicate pushdown, batching). The only sanctioned cache: derived table + refresh trigger + reconciliation test against a stated reference query — never a second source of truth. An optimization that adds a concept requires a measurement to justify it.

Probes that force honesty:

- **Explain test.** Explain each unit aloud. If the explanation is machinery ("guards against…", "re-checks…", "handles the case where…") rather than domain meaning, the unit is a modeling error surfacing as code. Every defensive guard — regex validation, safe casts, null-checks on values your own types already guarantee — indicts the model that allows the bad state; fix the model first, keep a guard only for inputs the model truly cannot forbid. A one-off migration that repairs old rows is repair, not a guard.
- **Translation test.** Can the name be said as one plain domain word? `folds_fact` couldn't — the concept was wrong — it became `is_answer`. Renaming is design: keep renaming until the domain vocabulary is coherent.
- **Walkthrough test.** Tell one concrete end-to-end scenario — a new user's first action — as actual data and operations (rows and statements in SQL). Every step that needs narration beyond the visible cascade is a design gap.

## SQL Hard Rules

- **DML is the API.** Never wrap a single INSERT/UPDATE/upsert in a function — a wrapper is a second API you must keep in sync. Tables + GRANT/RLS with column lists (`GRANT INSERT (col1, col2) ON t`) are the stable API. Functions exist only for multi-statement orchestration or to expose a read-side relation (next rule).
- **One relation, not N getters.** Expose the whole relation — a parameterless set-returning function or view; callers restrict with WHERE. No parameterized scalar getters (`is_visible(user, item)`), no chains of tiny functions each called only by the next: in SQL the unit of composition is the query (CTEs in one statement), not the function — function ladders blind the planner and scatter semantics. Verify inlining and predicate pushdown with EXPLAIN. In any language: one derivation callers filter beats N boolean getters.
- **Set-based, single-statement.** `IF TG_OP = 'DELETE' THEN OLD ELSE NEW` plumbing → `COALESCE(NEW.col, OLD.col)` inside the statement. PERFORM-per-row → one INSERT ... SELECT. Check-then-act → upsert.
- **Entities over strings.** Finite-domain values are rows referenced by FK; comparison becomes an equality join; numbers live in numeric columns. IDs join things — humans get names via a label table.
- **One mechanism, N configs.** Exclusion = weight 0, not a special rule. N actor kinds = one supertype table, so one fact table serves all.

## Rationalizations vs Reality

| Excuse | Reality |
|---|---|
| "We might need it later" | You own it now: bugs, tests, reading cost. Build it when the need is a fact; until then it is rung 0. |
| "This case is special" | Weight/flag/config-row first — a special case in code is configuration that escaped into the wrong layer. |
| "The guard is safe — review even approved it" | A passing review proves the guard works, not that it should exist; the next model fix makes it meaningless. |
| "Deleting it wastes work already done" | Sunk cost. The system gets stronger with each deletion. |
| "Ship now, simplify later" — yours or the user's | Later never arrives on its own. The pass runs before "done"; a deadline defers a named, scheduled fix — never the pass. |

## Red Flags — stop and redesign

- A helper called by exactly one caller
- A name you cannot translate into one domain word
- A guard against a state your own model or types already forbid
- Logic that re-derives what a lower layer already guarantees
- A mechanism where a row of config data could do it
- A cache that is not a derivation of a stated reference truth
- Correctness that depends on event or trigger firing order
- Destroying user-entered data to maintain a derived invariant

SQL:

- `CREATE FUNCTION` around one DML statement
- A regex or safe-cast on data your own schema produced
- `IF TG_OP = ...` branches, check-then-insert, or per-row PERFORM in a trigger
- A parameterized getter where a relation + WHERE would do
