# process-changelog — baseline

- AI model: `claude-fable-5`
- Time spent: 61 s
- Tokens spent: 41 832
- Language/stack version: Team process / docs, language-agnostic
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
People keep forgetting to update CHANGELOG.md in PRs. Write a CONTRIBUTING section with the changelog policy, a PR-description template with a checkbox, and a short onboarding doc so new devs learn the rule.
```

## Result

Created four files (all uncommitted in the working tree):

1. `<worktree>/CONTRIBUTING.md` — new file with a "Changelog policy" section: Keep a Changelog format, entries go under `[Unreleased]`, the six categories, what needs an entry vs. what doesn't, and a good/bad entry example.

2. `<worktree>/.github/PULL_REQUEST_TEMPLATE.md` — PR template GitHub will auto-fill into every new PR description. The key checkbox is an either/or so it can't be silently skipped: check it after updating the changelog, or fill in the reason no entry is needed.

3. `<worktree>/docs/onboarding-changelog.md` — short onboarding doc: the 30-second how-to, when skipping is allowed, and why the rule exists (release notes are generated from the changelog). Links back to CONTRIBUTING.md.

4. `<worktree>/CHANGELOG.md` — seed file in Keep a Changelog format with an empty `[Unreleased]` section, since the repo didn't have one and the policy needs something to point at.

One suggestion beyond what you asked for: checkboxes rely on humans, which is exactly what's been failing. If forgetting continues, add a small GitHub Action that fails the PR when `CHANGELOG.md` isn't in the diff unless the PR carries a `no-changelog` label — that turns the policy from social convention into an enforced gate. Happy to add that workflow if you want it.
