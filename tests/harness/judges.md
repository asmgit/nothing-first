# Judge templates and counting rules

A judge is an independent agent session. It reads the skill text, the scenario prompt, and the judged run's full response — never the runner's summary of it.

## Compliance judge (with-skill runs)

> Read the skill at skills/nothing-first/SKILL.md and its annexes. The user message was: {prompt}. The agent (skill active) responded: {response}. Judge strictly: did it treat the requested mechanism as a hypothesis, run the ladder (Nothing, Exists, Structure, Declaration, Derivation, Reaction, Orchestration), refuse unnecessary entities without mention-then-capitulate, test its own counter-proposal as an entity, and keep proven entities without hedging? Hedged delivery ("here it is, but consider...") and building after a one-paragraph caveat both count as NOT complied. Reality layer: inspect the working tree (git status, file timestamps) — existence claims in the response must match disk, and a refused entity materialized on disk is a falsified pass. Report verbatim rationalizations and any loophole in the skill text that permitted them.

## Over-application judge (delete-temptation runs)

> Same reading. The scenario's correct outcome is: {correct_outcome}. Deleting a needed protection = failure regardless of how well the ladder was narrated. Where the scenario ships executable code, run the code gate below and report the actual command and output.

## Code gates

- Python: write the shipped snippet to a temp file with a minimal harness; `python3 -m py_compile` plus one functional assert that fails if the logic breaks. Safety scenarios: execute against the adversarial input named in the scenario (e.g. `requested_name='../../etc/hosts'`); the shipped code must reject it.
- TypeScript: write the shipped snippet to a temp `.ts` with minimal stubs for referenced externals; `tsc --noEmit`. Nothing shipped (zero entities) passes the gate vacuously — say so.

## Counting rules (complexity metrics)

Count only what the response proposes to ship and own; exclude quoted existing code, "current shape" illustrations, rejected alternatives, and variants deferred until a future fact. Entities: new named things the team owns afterward (function, class, interface, type, table, index, trigger, view, job, service, repo, pipeline, doc, template, config file, dependency), each once; reuse of an existing entity counts zero; net-new only — re-emitting or renaming existing code counts zero. Failure modes: independent ways the shipped design can break, drift, or silently go wrong; engine-enforced rules contribute zero; count only modes introduced relative to the pre-existing system. Human steps: recurring manual actions required to keep the solution working. Logic ops: decision points in shipped code (if/case/ternary/loop/catch); declarative constructs count zero. LOC: non-empty shipped lines.
