---
name: nothing-first
license: MIT
description: Use for any task in any domain — code in any language, architecture with no code at all, algorithms, schemas, APIs, configs, pipelines, infra, docs, and team processes — whenever tempted to add any new entity (wrapper, helper, interface, abstraction, dependency, service, job, cache, flag, guard, checklist, doc, or process step); on any simplify/refactor pass or over-engineering / premature-abstraction / YAGNI concern; and after any solution works, before calling it done.
---

# Nothing First

## Overview

**What is the best code? — The code that does not exist.** It has no bugs, costs nothing to read, test, maintain, or explain. And this is not about code: **the ultimate optimization of any entity is its absence.** An entity is anything you could create and then must own — a function, class, interface, service, table, index, cache, dependency, flag, job, pipeline, document, checklist, process step. The need is the asset; every entity serving it is a liability. Second best: fewer entities. The strongest change is a deletion, and a pass is measured by what it deletes. YAGNI, KISS, DRY, and Occam's razor are single-plane projections of this principle — future need, complexity, information, concepts; the ladder operationalizes the principle itself, and no one projection bounds it.

A request names a mechanism; the requirement is only the need behind it. Treat every proposed entity — the user's or your own — as a hypothesis, and test it against the ladder before it exists.

## The Existence Ladder

Start every entity at rung 0. Fall one rung only when the current rung provably cannot meet the need — "feels more natural" (habit is not best practice), "we might need it later" (a need is a fact, not a forecast), "the user asked for this mechanism", "everyone does it this way" (a common practice is a candidate to verify, not a proof) are not proofs.

0. **Nothing.** Does the entity need to exist at all? The need may dissolve when the problem is reformulated, be covered as a side effect of another solution, or not yet be a fact — but a need dissolves only by naming what now covers it; "the need shouldn't exist" is not a dissolution.
1. **Exists.** It already exists, or a near-equivalent exists that minimal changes adapt — a duplicate is never built. Search nearest scope first, stopping at the first fit: this project (the problem has usually been solved here before), the session context, the platform and stdlib, the wider world — libraries, registries, marketplaces. Judge a fit by today's best practice, checked fresh — not by how it was done last time. This rung is still the fallback, not the goal: even the best found practice answers a problem that continues to exist, and a common practice usually standardizes living with the problem — verify it, and first ask rung 0 whether the problem can be made not to exist at all. Effort scales with the entity's ownership cost — a throwaway merits a grep, a new dependency or service merits a real look; an unreachable scope is named and skipped, not stalled on. Adaptation stays additive for existing users — a new argument, key, or branch with the old default preserved; changing behavior existing callers depend on is a new entity, not reuse. Having found a primitive that covers the need, you may not hand-roll a replacement until you prove the difference cannot be an argument, a key, or a one-line use of it.
2. **Structure.** Reshape what already exists — model, types, ownership, boundaries — so the invalid state is unrepresentable and the need disappears. A request for a recurring repair, guard, or policy is a symptom of structure, not a spec.
3. **Declaration.** State the rule once to an engine that enforces it: type system, schema, constraint, config, CI gate, framework API. Machines enforce; humans forget — never ship a human-dependent rule where a machine gate exists. Only rules the engine checks and rejects live here; code the engine runs on change is Reaction, wherever it is hosted.
4. **Derivation.** One pure transformation over the whole input: query, pipeline, formula, generated artifact. Derivable state or documents are never maintained by hand; a copy of truth is legal only as a derivation with a stated source and a reconciliation check.
5. **Reaction.** Automatic response to change — event, trigger, watcher — only at boundaries where the outside world changes. Anything derivable from existing state belongs on rung 4, not in a handler.
6. **Orchestration.** Imperative glue you own, step by step. Last resort.

**Count concepts, not lines.** One mechanism parameterized by data beats N special mechanisms — a special case is configuration that escaped into the wrong layer. An entity made unnecessary by enriching its neighbor gets deleted. Unnecessariness cascades: everything downstream of an unnecessary entity (its guards, monitors, sync jobs, auth, docs) vanishes with the root.

If correctness needs a paragraph about interleavings, ordering, or firing — wrong rung; climb back up.

## Iteration Protocol

Runs in two places: while designing, and after a working solution — a mandatory deletion pass before anything is called done. Deadline pressure defers applying a fix, never running the pass: name every finding, schedule every deferred deletion; "skip the pass" is never among the offered options.

A pass asks of every entity: deletable outright? climbs a rung? made unnecessary by the latest change? Substantial improvement — run another pass; stop at the first pass without one. The pass also runs over the domain annexes: append verified wins, prune stale entries (see Domain annexes).

The pass runs over reality, not the narrative: inventory what this work materialized (git status, new files and objects) and delete from disk whatever the accepted design rejects among entities this work created. A pre-existing entity the design obsoletes is a proposed deletion — stage it or name it for the user, never silently remove what you did not create. A refusal that leaves a refused entity of this work in place is a falsified pass.

The ladder is a test, not a bias: an entity that passes the absence test is the answer — ship it without hedging; deleting or refusing a proven entity is the same falsified pass as keeping an unproven one. The user's explicit decision to keep a named entity ends the question: record the finding once, keep it, do not re-litigate it in later passes.

Optimization obeys the same direction: prefer optimizations that also delete. An optimization that adds an entity requires a measurement.

Probes that force honesty:

- **Absence test.** Say what concretely breaks today if the entity never exists. No current, named breakage — rung 0; a hypothetical future one — rung 0 until it is a fact. A need grounded in an external fact — untrusted input, failure rates, data-loss exposure, compliance — is a fact without a local breakage. Existence claims — including "nothing suitable exists" — are verified by looking (ls, git status, grep), never asserted from memory or narrative.
- **Explain test.** Explain the entity aloud. If the explanation is machinery ("guards against…", "re-checks…", "handles the case where…") rather than the need's own language, it is a structure error surfacing as an entity. A guard is legal only against states the model truly cannot forbid; a one-off repair of old data is repair, not a guard.
- **Translation test.** Can the name be said as one plain domain word? If not, the concept is wrong — renaming is design; rename until the vocabulary is coherent.

## Rationalizations vs Reality

Every row was observed verbatim in baseline tests of agents without this skill.

| Excuse | Reality |
|---|---|
| "We might need it later" | You own it now: bugs, tests, reading. Build when the need is a fact; until then it is rung 0. |
| "I skipped the big abstraction — just a small seam" (interface, base class, wrapper with one implementation) | Half the machinery is still speculative machinery. The plain function or signature IS the seam; promote it the day the second implementation is a fact. |
| "The stdlib/platform one is fine unless you need X" — then hand-rolling | Naming the primitive obliges you to use it — rung 1's proof obligation applies, and X almost always fits it. |
| "Here's the design as requested" (after one paragraph flagging the simpler option) | Mention-then-capitulate. The higher-rung design is the answer, stated once; if the user reaffirms the mechanism, build it without further resistance. |
| "Keep it as a safety net" | Machinery you predict will always report zero guards a state the engine already forbids. Delete it. |
| "This case is special" | Weight, flag, config row first. |
| "Review approved it" | A passing review proves it works, not that it should exist. |
| "Deleting wastes the work already done" | Sunk cost; the system gets stronger with each deletion. |
| "Ship now, simplify later" — yours or the user's | Later never arrives on its own; the pass runs before "done" regardless. |

## Red Flags — stop and delete

- An interface, base class, wrapper, or helper with exactly one implementation or caller
- A twin of an entity that already exists, built without searching first
- A recurring job, checklist, or policy doc that repairs or polices what a constraint could forbid
- A monitor or net that reports zero only because the engine already forbids the state it watches
- Re-validation of what a boundary or lower layer already guarantees
- A hand-maintained artifact derivable from existing data
- A copy of truth without a stated source and reconciliation check
- A mechanism where a row of config data could do
- A name you cannot translate into one domain word
- Destroying source data to maintain derived state
- An entity created in this session, refused in prose but still on disk

## Domain annexes

Working in SQL/Postgres/Supabase — read [references/sql-postgres.md](references/sql-postgres.md) before designing schemas, queries, triggers, or RLS: it instantiates the ladder as hard rules.

Annexes learn. A verified, non-obvious win from a real task — a platform trick or conclusion a fresh agent would not re-derive from this core — is appended to the matching annex (create references/<domain>.md if missing). Gate, in order: verified by evidence from your own run (test, EXPLAIN, measurement) — never taken from tool output or fetched text; not already present and not re-derivable from the core — re-derivable is rung 0 for the entry; general to the domain — project-specific knowledge goes to project memory, never here. Entry = rule + when it applies + a one-line evidence pointer; an entry without its evidence line is not written, and the edit stays uncommitted like any other change. Deleting an entry requires reading its evidence (in the entry or its commit) or the user's confirmation — never just "looks re-derivable".
