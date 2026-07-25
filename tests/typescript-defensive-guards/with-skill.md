# typescript-defensive-guards — with-skill

- AI model: `claude-fable-5`
- Time spent: 57 s
- Tokens spent: 40 981
- Language/stack version: TypeScript (targets TS 7.0.2) + zod
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
Our TS API layer parses responses with zod at the boundary into typed DTOs. Deep in the app a component crashed once on user.profile.address being undefined. Add defensive checks: re-validate the DTO with zod inside the component and optional-chain every access, so it can never crash again.
```

## Result

This repo (Supabase admin app) has no such TS API layer, so here is the design I would apply, reasoned through the ladder.

**The need is "never crash on missing `address`" — not "re-validate and optional-chain".** Both requested mechanisms fail the absence test:

- **In-component zod re-parse** re-validates what the boundary already guarantees. It will either always pass (dead machinery, plus a render-path parse cost and a second copy of the shape to keep in sync) or it papers over a real hole in the boundary — and then the fix is closing the hole, not duplicating the check downstream.
- **Blanket `?.`** guards a state the type either forbids (dead guards) or allows (in which case `strictNullChecks` already forces narrowing at exactly the accesses that need it). It also converts a loud, localized crash into silently blank UI — strictly worse to debug.

The crash proves exactly one of two structural bugs. Check the schema and the failing payload to tell which:

**Case A — address is genuinely sometimes absent.** Then the schema is lying. Fix the model once:

```ts
const UserSchema = z.object({
  profile: z.object({
    address: AddressSchema.optional()
  })
})
```

Now `user.profile.address` is `Address | undefined` and tsc rejects every unguarded access in the whole app — the compiler enforces the rule, no per-component discipline needed. Handle absence in the one component that renders it:

```tsx
if (!user.profile.address) return <AddressMissing />
```

**Case B — address is contractually required.** Keep it required in the schema; then a missing address fails at the boundary with a precise zod error instead of deep in a component. The crash means data reached the component without passing the parse — hunt for the bypass: a `as User` cast, `z.any()`/`.passthrough()` in the schema, a fetch path or cache that skips parsing. Close it structurally so unparsed data is unrepresentable outside the API module:

```ts
export type User = z.infer<typeof UserSchema>

export async function getUser(id: string): Promise<User> {
  return UserSchema.parse(await api(`/users/${id}`))
}
```

Export only the parsed type; keep raw-response types module-private so the boundary is the only code that can touch unparsed JSON.

If you want a machine gate against future regressions, add declaration-rung guards instead of runtime ones: `strict: true`, and eslint `@typescript-eslint/no-unsafe-*` + banning `as` on API data.

Net result: zero new runtime entities. One schema line (A) or one deleted cast/closed bypass (B), and the class of bug — not just this crash — becomes unrepresentable. Tell me which case your schema/payload shows and I'll apply the corresponding fix; I would not ship the in-component re-validation or blanket optional chaining.
