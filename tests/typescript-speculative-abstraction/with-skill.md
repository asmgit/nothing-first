# typescript-speculative-abstraction — with-skill

- AI model: `claude-fable-5`
- Time spent: 46 s
- Tokens spent: 41 514
- Language/stack version: TypeScript (targets TS 7.0.2, current stable at test date)
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
We only send email notifications today, but SMS and push are on the roadmap for next year. Let's future-proof now: add a NotificationChannel interface, a ChannelRegistry with dynamic registration, and a factory that picks the channel from config. Better to build the abstraction while the code is fresh in our heads.
```

## Result

No notification code exists in this repo yet, so here is the design I'd propose — and it is not the interface/registry/factory.

Running the request through the ladder before anything exists:

**Absence test.** What breaks today if `NotificationChannel`, `ChannelRegistry`, and the factory never exist? Nothing — email still sends. "SMS next year" is a roadmap hypothesis, not a fact, so all three start and stay at rung 0. Each one also hits a red flag directly:

- **Interface with exactly one implementation** — speculative seam. And it would be a *wrong* seam: an interface designed from email alone will encode email's shape (subject, body, address). SMS has length limits and no subject; push has device tokens and platform payloads. When SMS actually lands, the interface gets redesigned anyway — building it now doesn't bank future work, it banks a wrong guess you'll have to undo.
- **Registry with dynamic registration** — dynamic registration solves a runtime-plugin problem you don't have. Your channel set is known at build time; a registry for it is a mechanism where a row of data could do.
- **Factory picking from config** — config with exactly one legal value is not configuration.

**The plain function IS the seam.** Future-proofing you actually get for free today:

```ts
export async function notify(userId: string, event: NotificationEvent) {
  const user = await getUser(userId)
  await sendEmail(user.email, render(event))
}
```

Every call site says `notify(user, event)` — the domain need — and exactly one file knows email exists. That call-site discipline is the entire value the abstraction was supposed to buy, at zero entities.

The day SMS is a fact, the upgrade is mechanical and still doesn't need the trio:

```ts
const send = { email: sendEmail, sms: sendSms }
await send[user.preferredChannel](user, event)
```

One mechanism parameterized by data: channel choice becomes a user-preference column, dispatch becomes a map lookup. Interface/registry/factory would only earn existence if third parties must add channels at runtime — a plugin system, which isn't on the roadmap either.

So my answer: ship `notify()` as above; promote to a map the day the second channel is real; no interface, no registry, no factory now. If there's a concrete present-day driver I'm missing — e.g. SMS work actually starts this quarter, or an external team must plug in channels without touching this code — name it and I'll build exactly the seam that driver forces, nothing more. Want me to proceed with the plain `notify()` design?
