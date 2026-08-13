# nothing-first

**What is the best code? — The code that does not exist.**

An [Agent Skill](https://agentskills.io) built on one principle: **the ultimate optimization of any entity is its absence.** An entity is anything you create and then must own. The need is the asset; every entity serving it is a liability. The strongest change is a deletion.

Works for any language, any architecture (even with no code at all), any algorithm, any task — including non-code work like docs and team processes.

## The Existence Ladder

Start every entity at rung 0. Fall one rung only when the current rung provably cannot meet the need.

0. **Nothing** — does the entity need to exist at all? The need may dissolve on reformulation, be covered by another solution's side effect, or not yet be a fact
1. **Exists** — it already exists, or a near-equivalent adapts with minimal changes; search nearest scope first: this project, the session context, the platform and stdlib, the wider world
2. **Structure** — reshape what exists so the invalid state is unrepresentable and the need disappears
3. **Declaration** — state the rule once to an engine that enforces it: types, schema, constraint, config, CI gate
4. **Derivation** — one pure transformation over the whole input; derivable things are never maintained by hand
5. **Reaction** — automatic response to change, only at boundaries where the outside world changes
6. **Orchestration** — imperative glue you own; last resort

Condensed from [SKILL.md](skills/nothing-first/SKILL.md) — the canonical text.

The skill also carries a mandatory deletion pass before anything is called done and honesty probes; every rule is armed with its counter-rationalization inline — each observed verbatim in baseline tests of agents working without the skill. The deletion direction has a floor: trust-boundary validation, data-loss protections, security controls, and accessibility are never simplified away. Domain annex: [sql-postgres.md](skills/nothing-first/references/sql-postgres.md) — proven Postgres entries, each with its grounds.

## The defence

The ladder decides whether an entity exists. It never decided which of the surviving ways to build it — so the cheapest-looking option won by default, and the thorough-looking one won whenever thoroughness read as diligence. Both are choices made without pricing the alternative.

A defence is spoken for what does not exist yet. Nothing is built, so nothing can be shown: the case rests on the need it would serve, the cheaper option you are not taking with what each costs now and obliges someone to carry later, the limits the work will not reach, and the objection you would rather not hear — raised by you, then answered or conceded. The standard is result per unit of cost. Doubling the work for a refinement nobody asked for fails exactly as hard as saving an hour by leaving a stated requirement unmet.

Delivery afterwards reports against that defence instead of repeating it: which claim the evidence carried, which it did not, which limit turned out narrower. An unverified claim is undelivered. A limit conceded in the defence is a boundary; the same limit found later by someone else is a defect. And a defence that fails is a redesign order, not a disclosure — an objection you cannot answer changes the design, not the wording around it.

## Measured

Real A/B runs — same prompts, baseline vs with-skill, full unedited transcripts and metrics in [tests/](tests/): **6/6 temptation scenarios** where the baseline built unnecessary entities and the with-skill run built none — entities **49 → 10 (−80%)**, failure modes **27 → 7 (−74%)**, LOC **237 → 54 (−77%)** — and **2/2 already-minimal scenarios** reported as honest parity.

One pair from [tests/python-lru-cache](tests/python-lru-cache/): asked for a ~60-line hand-rolled LRU cache, the baseline ships a 73-line class with locks and an eviction test; with the skill — `@functools.lru_cache` on the parse function. Five lines, zero new entities, one failure mode instead of four.

## Prior art

The ladder's first two rungs apply to this skill itself: does it need to exist, and does an equivalent already exist? The check was run late — an early version was written without it, which is exactly the failure mode rung 1 (Exists) names. What it found:

- [Ponytail](https://github.com/DietrichGebert/ponytail) — the closest neighbor: the same maxim ("the best code is the code never written") and a source-of-code ladder starting at "does this need to exist at all?", always-on, deletion over addition. Scoped to coding tasks; its derivative `minimalist` and a family of YAGNI/KISS guard skills cover the same rungs 0–1 territory as principle summaries.
- Built-in `/simplify` and published code-simplification skills — post-hoc, behavior-preserving cleanup of a diff, no existence questioning.

What none of them contained at the time of the check (2026-07-25): the mechanism rungs of the Existence Ladder (2–6: Structure > Declaration > Derivation > Reaction > Orchestration), the any-entity/any-domain scope (docs, processes, architecture with no code), the reality-audited deletion pass ("a refusal that leaves the refused entity on disk is a falsified pass"), the baseline-observed counter-rationalizations woven into the rules, and the SQL/Postgres annex. That difference is why this skill exists as a separate entity. If it ever stops being a difference, this skill's own ladder says: delete it and point here to the survivor.

## Install

One command, with an update channel (`/plugin marketplace update`):

**Claude Code**

```
/plugin marketplace add asmgit/nothing-first
/plugin install nothing-first@nothing-first
```

**Codex**

```bash
codex plugin marketplace add asmgit/nothing-first
codex plugin add nothing-first@nothing-first
```

**GitHub Copilot CLI**

```bash
copilot plugin marketplace add asmgit/nothing-first
copilot plugin install nothing-first@nothing-first
```

**Cursor, Windsurf, Cline, and other AGENTS.md-aware agents** pick the skill up from [AGENTS.md](AGENTS.md) when this repo is cloned into or referenced by the workspace.

**Manual (any setup):**

```bash
git clone https://github.com/asmgit/nothing-first
ln -s "$(pwd)/nothing-first/skills/nothing-first" ~/.claude/skills/nothing-first
```

The core lives in [SKILL.md](skills/nothing-first/SKILL.md).
