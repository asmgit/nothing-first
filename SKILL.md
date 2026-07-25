---
name: nothing-first
license: MIT
description: Use for any task in any domain — code in any language, architecture with no code at all, algorithms, schemas, APIs, configs, pipelines, infra, docs, and team processes — whenever tempted to add any new entity: wrapper, helper, interface, abstraction, dependency, service, job, cache, flag, guard, checklist, doc, or process step; on any simplify/refactor pass or over-engineering / premature-abstraction / YAGNI concern; and after any solution works, before calling it done. Goal: the ultimate optimization of any entity is its absence — the best code is the code that does not exist.
---

# Nothing First

## Overview

**What is the best code? — The code that does not exist.** It has no bugs, costs nothing to read, test, maintain, or explain. And this is not about code: **the ultimate optimization of any entity is its absence.** An entity is anything you could create and then must own — a function, class, interface, service, table, index, cache, dependency, flag, job, pipeline, document, checklist, process step. The need is the asset; every entity serving it is a liability. Second best: fewer entities. The strongest change is a deletion, and a pass is measured by what it deletes.

A request names a mechanism; the requirement is only the need behind it. Treat every proposed entity — the user's or your own — as a hypothesis, and test it against the ladder before it exists.

ALWAYS ON: any language, any domain, pure architecture with no code, non-code work alike.

## The Existence Ladder

Start every entity at rung 0. Fall one rung only when the current rung provably cannot meet the need — "feels more natural", "we might need it later", "the user asked for this mechanism" are not proofs.

0. **Nothing.** Does the entity need to exist at all? The need may dissolve when the problem is reformulated, be covered as a side effect of another solution, or not yet be a fact. Never built — or deleted — is the goal reached: zero code, zero failure modes.
1. **Reuse.** It already exists, or a near-equivalent exists that minimal changes adapt — a duplicate is never built. Search nearest scope first: this project (the problem has usually been solved here before), your own memory and session context, the platform and stdlib, the wider world — libraries, registries, marketplaces. Searching means looking, not recalling. Having found a primitive that covers the need, you may not hand-roll a replacement until you prove the difference cannot be an argument, a key, or a one-line use of it.
2. **Structure.** Reshape what already exists — model, types, ownership, boundaries — so the invalid state is unrepresentable and the need disappears. A request for a recurring repair, guard, or policy is a symptom of structure, not a spec.
3. **Declaration.** State the rule once to an engine that enforces it: type system, schema, constraint, config, CI gate, framework API. Machines enforce; humans forget — never ship a human-dependent rule where a machine gate exists.
4. **Derivation.** One pure transformation over the whole input: query, pipeline, formula, generated artifact. Derivable state or documents are never maintained by hand; a copy of truth is legal only as a derivation with a stated source and a reconciliation check.
5. **Reaction.** Automatic response to change — event, trigger, watcher — only at boundaries where the outside world changes. Anything derivable from existing state belongs on rung 4, not in a handler.
6. **Orchestration.** Imperative glue you own, step by step. Last resort.

**Count concepts, not lines.** One mechanism parameterized by data beats N special mechanisms — a special case is configuration that escaped into the wrong layer. An entity made unnecessary by enriching its neighbor gets deleted. Unnecessariness cascades: everything downstream of an unnecessary entity (its guards, monitors, sync jobs, auth, docs) vanishes with the root.

If correctness needs a paragraph about interleavings, ordering, or firing — wrong rung; climb back up.

## Iteration Protocol

Runs in two places: while designing — every entity starts at rung 0 and falls only as far as forced — and after a working solution, as a mandatory deletion pass before anything is called done. Deadline pressure defers applying a fix, never running the pass: name every finding, schedule every deferred deletion; "skip the pass" is never among the offered options.

A pass asks of every entity: deletable outright? climbs a rung? made unnecessary by the latest change? Substantial improvement — run another pass; stop at the first pass without one.

The pass runs over reality, not the narrative: inventory what actually materialized during the work (git status, new files and objects) and delete from disk whatever the accepted design rejects. A refusal that leaves the refused entity in place is a falsified pass.

Optimization obeys the same direction: prefer optimizations that also delete. An optimization that adds an entity requires a measurement.

Probes that force honesty:

- **Absence test.** Say what concretely breaks today if the entity never exists. No current, named breakage — rung 0; a hypothetical future one — rung 0 until it is a fact. Existence claims are verified by looking (ls, git status, grep) — never asserted from memory or narrative.
- **Explain test.** Explain the entity aloud. If the explanation is machinery ("guards against…", "re-checks…", "handles the case where…") rather than the need's own language, it is a structure error surfacing as an entity. A guard is legal only against states the model truly cannot forbid; a one-off repair of old data is repair, not a guard.
- **Translation test.** Can the name be said as one plain domain word? If not, the concept is wrong — renaming is design; rename until the vocabulary is coherent.

## Rationalizations vs Reality

Every row was observed verbatim in baseline tests of agents without this skill.

| Excuse | Reality |
|---|---|
| "We might need it later" | You own it now: bugs, tests, reading. Build when the need is a fact; until then it is rung 0. |
| "I skipped the big abstraction — just a small seam" (interface, base class, wrapper with one implementation) | Half the machinery is still speculative machinery. The plain function or signature IS the seam; promote it the day the second implementation is a fact. |
| "The stdlib/platform one is fine unless you need X" — then hand-rolling | Naming the primitive obliges you to use it. Prove X cannot be an argument, key, or one-liner over the primitive — it almost always can. |
| "Here's the design as requested" (after one paragraph flagging the simpler option) | Mention-then-capitulate. The rung-0 design is the answer; the named mechanism is built only after the user confirms a concrete driver. |
| "Keep it as a safety net" | Machinery you predict will always report zero guards a state the engine already forbids. Delete it. |
| "This case is special" | Weight, flag, config row first. |
| "Review approved it" | A passing review proves it works, not that it should exist. |
| "Deleting wastes the work already done" | Sunk cost; the system gets stronger with each deletion. |
| "Ship now, simplify later" — yours or the user's | Later never arrives on its own. The pass runs before "done"; a deadline defers a named, scheduled fix — never the pass. |

## Red Flags — stop and delete

- An interface, base class, wrapper, or helper with exactly one implementation or caller
- A twin of an entity that already exists — in the codebase, the platform, the stdlib, or published elsewhere — built without searching first
- A recurring job, checklist, or policy doc that repairs or polices what a constraint could forbid
- A monitor or net expected to always report zero
- Re-validation of what a boundary or lower layer already guarantees
- A hand-maintained artifact derivable from existing data
- A copy of truth without a stated source and reconciliation check
- A mechanism where a row of config data could do
- A name you cannot translate into one domain word
- Destroying source data to maintain derived state
- An entity refused in prose but still present on disk

## Domain annexes

Working in SQL/Postgres/Supabase — read [references/sql-postgres.md](references/sql-postgres.md) before designing schemas, queries, triggers, or RLS: it instantiates the ladder as hard rules.
