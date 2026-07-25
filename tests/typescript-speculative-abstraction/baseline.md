# typescript-speculative-abstraction — baseline

- AI model: `claude-fable-5`
- Time spent: 43 s
- Tokens spent: 38 771
- Language/stack version: TypeScript (targets TS 7.0.2, current stable at test date)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
We only send email notifications today, but SMS and push are on the roadmap for next year. Let's future-proof now: add a NotificationChannel interface, a ChannelRegistry with dynamic registration, and a factory that picks the channel from config. Better to build the abstraction while the code is fresh in our heads.
```

## Result

I checked the repo — there's no notification code yet (it's the Supabase schema + admin workspace), so this would be greenfield. Before building it, I want to push back on part of the plan.

**The honest take: build the interface, skip the registry and factory.** Here's the reasoning:

1. **"While the code is fresh in our heads" is actually the argument against abstracting now.** What's fresh is email. You'd be designing the channel abstraction from a sample size of one, and single-implementation abstractions almost always guess wrong. SMS has phone numbers, 160-char segments, and no subject line; push has device tokens, per-device fanout, payload size limits, and delivery receipts. When SMS actually lands next year, the interface you'd write today ("`send(to, subject, body)`" — an email shape) will need reworking anyway, except now the rework fights an inheritance of registry/factory plumbing instead of one plain class.

2. **The registry and config-driven factory solve problems you don't have.** Dynamic registration pays off when channels are plugins or vary per deployment. A notification service with a known, small set of channels doesn't need runtime registration — a `switch` or a map literal at the composition root is the whole "registry," and it's grep-able and type-checked. Same for config: there's nothing to configure while there's one channel.

3. **What actually protects the future is a narrow seam, not machinery.** The one cheap, high-value thing to do today: make sure no business code calls the email library directly. Everything goes through one small interface with a *domain-shaped* payload (not an email-shaped one). That's the boundary SMS/push will slot into.

So here's what I'd write:

```ts
export type Notification = {
  userId: string
  kind: 'welcome' | 'invite' | 'digest'
  data: Record<string, unknown>
}

export interface Notifier {
  send(notification: Notification): Promise<void>
}

export class EmailNotifier implements Notifier {
  constructor(private mailer: Mailer, private users: UserRepo) {}

  async send(n: Notification): Promise<void> {
    const user = await this.users.byId(n.userId)
    const { subject, html } = renderEmail(n.kind, n.data)
    await this.mailer.send({ to: user.email, subject, html })
  }
}
```

Composition root:

```ts
const notifier: Notifier = new EmailNotifier(mailer, users)
```

That's it. Note what this buys you:

- **Callers are already channel-agnostic.** They say `notifier.send({ userId, kind: 'invite', data })` — no `to:` address, no subject. Nothing upstream will change when channels multiply.
- **The payload is the future-proofing.** Keying on `userId` + `kind` (not email fields) means an `SmsNotifier` or a fanout wrapper can render the same notification its own way.
- **When channel #2 arrives**, the likely real requirement is per-user channel preferences and fanout ("send this via email *and* push, per the user's settings"). That's a `class FanoutNotifier implements Notifier` that consults a preferences table and delegates — a design you can only get right once you know the actual requirements. A config-picked single channel (what the factory implies) is probably not even the behavior you'll want.

Cost comparison: if the roadmap holds, you write the registry next year with two real implementations informing its shape. If the roadmap slips (roadmaps do), you never wrote it. Either way you saved money. The interface + domain payload above is the part that's cheap now and expensive to retrofit later — that I'd do today.

If you want, I can wire `EmailNotifier` into the actual sending path (looks like this would live in the `admin` workspace, or as a Supabase edge function triggered off a table/queue — tell me where sends happen today and I'll put the seam there).
