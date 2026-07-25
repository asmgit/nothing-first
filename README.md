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

## Install (Claude Code)

```bash
git clone https://github.com/asmgit/nothing-first ~/.claude/skills/nothing-first
```

Or clone anywhere and symlink:

```bash
ln -s /path/to/nothing-first ~/.claude/skills/nothing-first
```

The core lives in [SKILL.md](SKILL.md).
