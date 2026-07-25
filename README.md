# nothing-first

**What is the best code? — The code that does not exist.**

An [Agent Skill](https://agentskills.io) built on one principle: **the ultimate optimization of any entity is its absence.** An entity is anything you create and then must own — a function, class, interface, service, table, cache, dependency, flag, job, document, checklist, process step. The need is the asset; every entity serving it is a liability. The strongest change is a deletion.

Works for any language, any architecture (even with no code at all), any algorithm, any task — including non-code work like docs and team processes.

## The Existence Ladder

Start every entity at rung 0. Fall one rung only when the current rung provably cannot meet the need.

0. **Nothing** — does the entity need to exist at all?
1. **Structure** — reshape what exists so the invalid state is unrepresentable and the need disappears
2. **Declaration** — state the rule once to an engine that enforces it: types, constraint, config, CI gate
3. **Derivation** — one pure transformation over the whole input; derivable things are never maintained by hand
4. **Reaction** — automatic response to change, only at boundaries where the outside world changes
5. **Orchestration** — imperative glue you own; last resort

The skill also carries a mandatory deletion pass before anything is called done, honesty probes, red flags, and counters for the standard rationalizations — every one observed verbatim in baseline tests of agents working without the skill. Domain annex: [references/sql-postgres.md](references/sql-postgres.md) instantiates the ladder as hard rules for SQL/Postgres.

## Prior art

Rung 0 applies to this skill itself: before owning it, check what already exists. The check was run late — an early version was written without it, which is exactly the failure mode rung 0 names. What it found:

- [Ponytail](https://github.com/DietrichGebert/ponytail) — the closest neighbor: the same maxim ("the best code is the code never written") and a source-of-code ladder starting at "does this need to exist at all?", always-on, deletion over addition. Scoped to coding tasks; its derivative `minimalist` and a family of YAGNI/KISS guard skills cover the same rung-0 territory as principle summaries.
- Built-in `/simplify` and published code-simplification skills — post-hoc, behavior-preserving cleanup of a diff, no existence questioning.

What none of them contained at the time of the check (2026-07-25): the mechanism-class Existence Ladder (Structure > Declaration > Derivation > Reaction > Orchestration), the any-entity/any-domain scope (docs, processes, architecture with no code), the reality-audited deletion pass ("an entity refused in prose but still present on disk"), the baseline-observed rationalization table, and the SQL/Postgres annex. That difference is why this skill exists as a separate entity. If it ever stops being a difference, this skill's own ladder says: delete it and point here to the survivor.

## Install (Claude Code)

```bash
git clone https://github.com/asmgit/nothing-first ~/.claude/skills/nothing-first
```

Or clone anywhere and symlink:

```bash
ln -s /path/to/nothing-first ~/.claude/skills/nothing-first
```

The core lives in [SKILL.md](SKILL.md).
