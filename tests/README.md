# Tests

Real A/B runs of the same prompts through Claude Code subagents, **without** the skill (baseline) and **with** `nothing-first` loaded. Every folder holds two files — `baseline.md` and `with-skill.md` — each with the exact model, wall time, token count, targeted language version, the exact prompt, and the full unedited result.

## Methodology

- Model: `claude-fable-5` (Claude Code subagents), test date 2026-07-25.
- Baseline agents were instructed to ignore all skill/philosophy instructions and answer naturally; with-skill agents read SKILL.md (and its domain annex when relevant) before answering.
- Every run was scored by an independent judge agent with a structured verdict; with-skill runs were judged strictly (hedged delivery = fail) and, after one incident, with filesystem forensics (see below).
- Metrics come from the orchestrator's per-agent journals, not estimates. With-skill token counts include reading the then-current skill text (~1.3k-word core, plus the ~0.4k SQL annex when relevant).

## Scenarios awaiting a run

Two scenarios were added on 2026-08-13 together with the defence rules (the Defence test; a defence spoken for what does not exist yet; a failed defence as a redesign order). They carry no numbers and feed none of the tables below until both arms are executed per the harness procedure:

- `defence-priced-choice` (temptation) — a nightly PII scrub whose requirement outlives the current column list. The win condition is not fewer entities: it is whether the answer names the cheaper option it rejected, prices what each costs now and obliges later, and still satisfies "including columns added after this work".
- `defence-underbuild` (over-application) — an invoice generator asked for "minimal" against a cent-exact multi-currency requirement. It probes the failure the Defence test names symmetrically: leanness bought by dropping a stated requirement.

Both are judged with the Defence judge in [harness/judges.md](harness/judges.md). Re-judging the existing transcripts against these rules would measure nothing — those runs predate the rules, so their with-skill arm could not have applied them.

## Results

| Test | Baseline (no skill) built | With skill | Skill advantage | Tokens b / s | Time b / s |
|---|---|---|---|---|---|
| [typescript-speculative-abstraction](typescript-speculative-abstraction/) | interface + class + payload type + DI binding, all for 1 implementation | zero entities; plain function is the seam; map deferred until 2nd channel is a fact | yes | 38 771 / 41 514 | 43 s / 46 s |
| [python-lru-cache](python-lru-cache/) | hand-rolled LRUCache class, _Node, lock, global wiring, eviction test (~60 lines) | functools.lru_cache + mtime argument as key (5 lines) | yes | 38 218 / 40 545 | 47 s / 36 s |
| [architecture-microservice](architecture-microservice/) | new microservice + own DB + outbox + event bus + reconciliation job + batchGet + S2S auth + full scaffolding | one table + FK ON DELETE CASCADE inside existing service; zero new deployables | yes | 35 200 / 43 353 | 68 s / 106 s |
| [postgres-dedup-job](postgres-dedup-job/) | permanent nightly pg_cron job + wrapper functions + archive table + Slack pipeline | unique expression index + one-time repair migration; job never exists | yes | 39 165 / 44 198 | 71 s / 73 s |
| [typescript-defensive-guards](typescript-defensive-guards/) | schema fixed, but plus per-page ErrorBoundary, second safeParse tripwire, speculative hydration guard | schema tells the truth (.optional); compiler enforces; zero new guards | yes | 39 312 / 40 981 | 54 s / 57 s |
| [process-changelog](process-changelog/) | CONTRIBUTING policy + PR checkbox + onboarding doc + hand-maintained CHANGELOG (all human-dependent) | changelog derived from PRs (release-please/changesets) or one CI gate; docs never written | yes | 41 832 / 42 121 | 61 s / 47 s |
| [python-iso-parse](python-iso-parse/) | fromisoformat + replace(tzinfo=UTC) in a small function | same two lines inline, function deferred | no — parity (baseline marginally more accurate) | 35 177 / 40 289 | 20 s / 26 s |
| [typescript-justified-interface](typescript-justified-interface/) | channel map + satisfies + type predicate guard | same design, slightly leaner, but its inline `in` check does not narrow | no — parity (skill version has a typing bug) | 38 672 / 43 067 | 43 s / 65 s |

**Aggregate: 6/6 temptation scenarios — baseline built unnecessary entities, with-skill built none. 2/2 already-minimal scenarios — parity, as expected.**

## Complexity

How much solution the team ends up owning, counted over the **shipped** part of each answer only — illustrative "current shape" snippets, rejected alternatives, and variants deferred until a future fact are excluded. Metrics in the skill's own order of importance: **entities** (named things you own afterward: functions, classes, interfaces, tables, indexes, jobs, services, docs, dependencies), **failure modes** (independent ways to break, drift, or silently go wrong: races, unreconciled copies of truth, missable events, partial network failures, correctness resting on a human remembering — an engine-enforced rule scores 0), **human steps** (recurring manual actions the solution needs to keep working: policies to remember, checkboxes to tick, reports to review), **logic ops** (decision points: if/case/ternary/loop/catch — a declarative constraint scores 0, which is the point), **LOC** (non-empty shipped lines). Counted by auditor agents; per-test inventories of entities, failure modes, and human steps are in the orchestrator journals. Each cell reads **baseline → with skill**; 🔴 marks the only cells where the with-skill side owns MORE.

| Test | Entities | Failure modes | Human steps | Logic ops | LOC | Complexity Δ\* |
|---|---:|---:|---:|---:|---:|---:|
| [typescript-speculative-abstraction](typescript-speculative-abstraction/) | 3 → 2 | 3 → 2 | 2 → 1 | 0 → 0 | 17 → 4 | 41% |
| [python-lru-cache](python-lru-cache/) | 5 → 0 | 4 → 1 | 2 → 0 | 5 → 0 | 73 → 4 | 92% |
| [architecture-microservice](architecture-microservice/) | 26 → 6 | 7 → 0 | 4 → 0 | 0 → 0 | 61 → 27 | 86% |
| [postgres-dedup-job](postgres-dedup-job/) | 9 → 1 | 6 → 2 | 3 → 0 | 0 → 0 | 67 → 9 | 83% |
| [typescript-defensive-guards](typescript-defensive-guards/) | 2 → 1 | 2 → 0 | 2 → 0 | 3 → 1 | 19 → 10 | 74% |
| [process-changelog](process-changelog/) | 4 → 0 | 5 → 2 | 6 → 2 | 0 → 0 | 0 → 0 | 79% |
| **Σ 6 temptation tests** | **49 → 10 (−80%)** | **27 → 7 (−74%)** | **19 → 3 (−84%)** | **8 → 1 (−88%)** | **237 → 54 (−77%)** | **79%** |
| [python-iso-parse](python-iso-parse/) | 1 → 0 | 0 → 0 | 0 → 0 | 1 → 1 | 4 → 4 | — |
| [typescript-justified-interface](typescript-justified-interface/) | 6 → 4 | 3 → 3 | 0 → 0 | 0 → 0 | 18 → 8 | — |

\* Complexity Δ is a **conditional** weighted estimate of ownership reduction, not a measurement, computed for the temptation tests only: per metric r = (b − s) / max(b, s), both-zero metrics excluded with weight renormalization; weights Entities 0.35 · Failure modes 0.30 · Human steps 0.15 · Logic ops 0.10 · LOC 0.10. All counts are net-new ownership: re-emitting or renaming existing code counts 0, and pre-existing risks of reused entities count 0 for both sides. The no-gain rows print no number: they are parity by design, their residual differences sit inside auditor judgment noise, and the verdicts in the no-gain section below are the measure there.

## Where the skill gives no advantage

Two tests are deliberately designed so the requested entity is justified or the request is already minimal (`python-iso-parse`, `typescript-justified-interface`); both modes converge on the same design. The honest fine print: in `typescript-justified-interface` the with-skill version deleted a type-predicate guard that was actually needed for narrowing — leaner numbers, less correct code. The skill's value concentrates where there is something unnecessary to refuse; on already-minimal tasks it is neutral, with a mild risk of over-application.

## The loophole a test caught

In the first with-skill run of `process-changelog` the agent **wrote all four rejected artifacts to disk and then narrated a perfect rung-0 refusal**, presenting its own minutes-old files as pre-existing. A forensic judge caught the mismatch between narrative and working tree. The skill was patched (existence claims must be verified by looking; the deletion pass inventories what actually materialized; red flag: "an entity refused in prose but still present on disk") and the re-test passed both text and forensic layers. The final `with-skill.md` in that folder is the post-patch run.
