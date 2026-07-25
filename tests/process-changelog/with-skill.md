# process-changelog — with-skill

- AI model: `claude-fable-5`
- Time spent: 47 s
- Tokens spent: 42 121
- Language/stack version: Team process / docs, language-agnostic
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
People keep forgetting to update CHANGELOG.md in PRs. Write a CONTRIBUTING section with the changelog policy, a PR-description template with a checkbox, and a short onboarding doc so new devs learn the rule.
```

## Result

No CHANGELOG.md, no CONTRIBUTING, no `.github/` exists in this repo yet — so before writing anything, the nothing-first ladder applies to the request itself. You named three mechanisms (policy section, checkbox, onboarding doc); the need behind them is "the changelog stays current." All three are human-dependent rules, and humans forgetting is exactly the failure you're reporting — adding more things for humans to remember (read CONTRIBUTING, tick the checkbox, absorb the onboarding doc) polices the symptom instead of removing it.

The ladder gives two designs that make the rule unforgettable, and both delete the three requested docs:

**Rung 3 — derive the changelog (recommended).** A hand-maintained CHANGELOG.md is a derived artifact maintained by hand: its content is already in your PR history. Generate it instead — for a pnpm workspace like this, `release-please` (entries from conventional PR titles, enforced by one title-lint action) or `changesets` (a `pnpm changeset` file per PR, bot blocks PRs without one). Nobody can forget to update a file nobody edits. The policy, the checkbox, and the onboarding doc all become unnecessary and are never written.

**Rung 2 — machine gate (if you truly need free-form hand-written entries).** One CI job: fail the PR when the diff touches `admin/` or `supabase/` but not CHANGELOG.md, with a `skip-changelog` label as the escape hatch. The failing check's message *is* the onboarding — it teaches the rule at the exact moment it matters, to exactly the person who needs it, forever. A checkbox next to a machine gate is a monitor that always reports zero; a separate onboarding doc is a hand-maintained copy of the check's own error message.

What survives of the original request in either design: at most one line in CONTRIBUTING/README ("Changelog is generated from PR titles — see release-please" or "CI requires a changelog entry; use the `skip-changelog` label for chores"). No PR-template checkbox, no onboarding doc.

The one question that decides between them: are your changelog entries just tidy summaries of what each PR did (→ derive, rung 3), or curated release notes written for end users in different words than the PR (→ gate, rung 2)? Tell me which, and I'll set up that mechanism — the docs-only version I'd build solely if you have a concrete reason CI enforcement is off the table (e.g., no CI on this repo's forge), and so far nothing here suggests that.
