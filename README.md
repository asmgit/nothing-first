# nothing-first

**What is the best code? — The code that does not exist.**

An [Agent Skill](https://agentskills.io) that makes an agent try *nothing* before *something*: every line, concept, and mechanism is a liability; the feature is the asset. Second best: less code. The strongest change is a deletion.

## The ladder

Start every piece of logic at rung 0. Fall only when the current rung genuinely cannot express it.

0. **Nothing** — does the concept need to exist at all?
1. **Data model / types** — make the invalid state unrepresentable
2. **Declarative invariant** — constraint, type system, schema validation, declarative framework API
3. **One pure transformation** — one query / one pipeline over the whole input
4. **Reactive mechanism** — trigger, event, watcher; derived data only
5. **Imperative glue** — last resort, genuine multi-statement orchestration

The skill also carries a mandatory simplify-and-optimize pass before anything is called done, honesty probes, hard rules for SQL/Postgres, and counters for the standard rationalizations ("we might need it later", "ship now, simplify later").

## Install (Claude Code)

```bash
git clone https://github.com/asmgit/nothing-first ~/.claude/skills/nothing-first
```

Or clone anywhere and symlink:

```bash
ln -s /path/to/nothing-first ~/.claude/skills/nothing-first
```

Everything lives in [SKILL.md](SKILL.md).
