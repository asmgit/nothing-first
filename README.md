# nothing-first

**What is the best code? — The code that does not exist.**

An [Agent Skill](https://agentskills.io) built on one principle: **the ultimate optimization of any entity is its absence.** An entity is anything you create and then must own. The need is the asset; every entity serving it is a liability. The strongest change is a deletion.

Works for any language, any architecture (even with no code at all), any algorithm, any task — including non-code work like docs and team processes.

**Not YAGNI.** YAGNI is a pragmatic bet about the future: don't build what is not yet needed. This skill states the fundamental principle behind it. YAGNI is its projection onto the time axis ("the need is not yet a fact" — one clause of rung 0); KISS projects it onto complexity, DRY onto information, Occam's razor onto concepts. The ladder operationalizes the principle itself — which is why it also covers what YAGNI never touches: dissolving the need, refusing duplicates, deriving instead of maintaining by hand, and deleting what already exists.

## The Existence Ladder

Start every entity at rung 0. Fall one rung only when the current rung provably cannot meet the need.

0. **Nothing** — does the entity need to exist at all? The need may dissolve on reformulation, be covered by another solution's side effect, or not yet be a fact
1. **Reuse** — it already exists, or a near-equivalent adapts with minimal changes; search nearest scope first: this project, the session context, the platform and stdlib, the wider world
2. **Structure** — reshape what exists so the invalid state is unrepresentable and the need disappears
3. **Declaration** — state the rule once to an engine that enforces it: types, schema, constraint, config, CI gate
4. **Derivation** — one pure transformation over the whole input; derivable things are never maintained by hand
5. **Reaction** — automatic response to change, only at boundaries where the outside world changes
6. **Orchestration** — imperative glue you own; last resort

Condensed from [SKILL.md](SKILL.md) — the canonical text.

The skill also carries a mandatory deletion pass before anything is called done, honesty probes, red flags, and counters for the standard rationalizations — every one observed verbatim in baseline tests of agents working without the skill. Domain annex: [references/sql-postgres.md](references/sql-postgres.md) instantiates the ladder as hard rules for SQL/Postgres.

## Prior art

The ladder's first two rungs apply to this skill itself: does it need to exist, and does an equivalent already exist? The check was run late — an early version was written without it, which is exactly the failure mode rung 1 (Reuse) names. What it found:

- [Ponytail](https://github.com/DietrichGebert/ponytail) — the closest neighbor: the same maxim ("the best code is the code never written") and a source-of-code ladder starting at "does this need to exist at all?", always-on, deletion over addition. Scoped to coding tasks; its derivative `minimalist` and a family of YAGNI/KISS guard skills cover the same rungs 0–1 territory as principle summaries.
- Built-in `/simplify` and published code-simplification skills — post-hoc, behavior-preserving cleanup of a diff, no existence questioning.

What none of them contained at the time of the check (2026-07-25): the mechanism rungs of the Existence Ladder (2–6: Structure > Declaration > Derivation > Reaction > Orchestration), the any-entity/any-domain scope (docs, processes, architecture with no code), the reality-audited deletion pass ("an entity refused in prose but still present on disk"), the baseline-observed rationalization table, and the SQL/Postgres annex. That difference is why this skill exists as a separate entity. If it ever stops being a difference, this skill's own ladder says: delete it and point here to the survivor.

## Install (Claude Code)

```bash
git clone https://github.com/asmgit/nothing-first ~/.claude/skills/nothing-first
```

Or clone anywhere and symlink:

```bash
ln -s /path/to/nothing-first ~/.claude/skills/nothing-first
```

The core lives in [SKILL.md](SKILL.md).
