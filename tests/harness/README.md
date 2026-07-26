# Test harness

Everything needed to re-run the suite. Prompts are the single source in [scenarios.json](scenarios.json); each test folder's files are generated output (metadata + prompt + full transcript). Judges run per [judges.md](judges.md) and must pass [calibration.md](calibration.md) before their counts are recorded.

## Procedure

1. For each scenario, run two arms as independent agent sessions: **baseline** (no skill; instruct the agent to ignore all skill/philosophy instructions and answer naturally) and **with-skill** (the agent reads `skills/nothing-first/SKILL.md` first and follows it, including annexes when relevant). Use the arm preambles from scenarios.json verbatim; record model, wall time, and token count per run.
2. Judge every run with the matching template from judges.md. With-skill runs are judged strictly (hedged delivery = fail) and forensically: the judge inspects the working tree (`git status`, timestamps) so narrative claims are checked against reality.
3. Code gates: when a run ships code, extract it and execute the gate from judges.md (compile + one failing-if-broken check, adversarial input for safety scenarios). "The judge believes it works" never substitutes for "it ran".
4. Headline scenarios run n=3; report per-run verdicts and the spread. Expensive scenarios may run n=1 with an explicit single-run note.
5. Metrics are counted over the shipped part of the answer only, per the counting rules in judges.md, and aggregated into [../README.md](../README.md). Results are append-only: a superseded run is kept with a one-line reason, never silently replaced.
