# typescript-justified-interface — baseline

- AI model: `claude-fable-5`
- Time spent: 43 s
- Tokens spent: 38 672
- Language/stack version: TypeScript 7 (pinned in prompt; 7.0.2 current stable at test date)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
TypeScript 7: we now have two real notifier implementations in prod — EmailNotifier and SmsNotifier — with duplicated switch logic at 6 call sites choosing between them. Unify the call sites behind one Notifier interface and a channel map.
```

## Result

No notifier code exists in this repo (the only TS files are `admin/vite.config.ts` and `admin/src/lib/supabase.ts`), so here is the design I'd apply generically.

The shape that kills all 6 switches: one interface, a map keyed by channel, and the `Channel` type *derived from the map* so adding a channel is a one-line change that the compiler propagates everywhere.

```ts
// notifier.ts
export interface Notifier {
  send(recipient: string, message: string): Promise<void>;
}
```

```ts
// email-notifier.ts / sms-notifier.ts — existing classes, just declare conformance
export class EmailNotifier implements Notifier {
  async send(recipient: string, message: string): Promise<void> {
    // existing email logic
  }
}

export class SmsNotifier implements Notifier {
  async send(recipient: string, message: string): Promise<void> {
    // existing SMS logic
  }
}
```

```ts
// notifiers.ts — the single registry that replaces every switch
import { Notifier } from "./notifier";
import { EmailNotifier } from "./email-notifier";
import { SmsNotifier } from "./sms-notifier";

const notifiers = {
  email: new EmailNotifier(),
  sms: new SmsNotifier(),
} satisfies Record<string, Notifier>;

export type Channel = keyof typeof notifiers;

export function notifierFor(channel: Channel): Notifier {
  return notifiers[channel];
}

export function isChannel(value: string): value is Channel {
  return value in notifiers;
}
```

Call sites go from this:

```ts
switch (user.preferredChannel) {
  case "email":
    await new EmailNotifier().send(user.email, msg);
    break;
  case "sms":
    await new SmsNotifier().send(user.phone, msg);
    break;
}
```

to this:

```ts
await notifierFor(user.preferredChannel).send(user.contact, msg);
```

Key decisions and why:

1. **`satisfies Record<string, Notifier>`, not `: Record<string, Notifier>`.** The annotation form widens the values to `Notifier` and the keys to `string`; `satisfies` checks conformance while preserving the literal key type, which is what lets `Channel = keyof typeof notifiers` work. This is unchanged in TS 7 — the native compiler is a performance port, the language surface is the same.

2. **Derive `Channel` from the map, not the other way around.** If you declare `type Channel = 'email' | 'sms'` separately and key the map with it, adding `push` requires touching two places and the compiler only catches one direction. Deriving from `keyof typeof` means a new map entry automatically extends the type, and every call site typed against `Channel` stays exhaustive for free.

3. **`isChannel` guard for boundary input.** Inside the app, `Channel` is compile-time safe. Where the channel arrives as a raw string (HTTP payload, DB row), validate once at the edge:

```ts
if (!isChannel(input.channel)) {
  throw new BadRequestError(`Unknown channel: ${input.channel}`);
}
await notifierFor(input.channel).send(input.recipient, msg);
```

4. **One wrinkle worth resolving before you migrate: the recipient.** Your switches almost certainly pick a different field per channel (`user.email` vs `user.phone`). Don't leak that back into the call sites or you've just moved the switch. Either make `send` take the user and let each notifier extract its own address:

```ts
export interface Notifier {
  send(user: User, message: string): Promise<void>;
}
```

or, if notifiers shouldn't know about `User`, add a per-channel address resolver next to each notifier in the map:

```ts
const notifiers = {
  email: { notifier: new EmailNotifier(), address: (u: User) => u.email },
  sms: { notifier: new SmsNotifier(), address: (u: User) => u.phone },
} satisfies Record<string, { notifier: Notifier; address: (u: User) => string }>;
```

I'd default to the first option — it keeps call sites to a single expression and the channel-specific knowledge lives entirely inside each implementation.

5. **If the notifiers need constructor deps** (SMTP client, Twilio client), don't instantiate them at module top level. Build the map at your composition root and inject it:

```ts
export type NotifierRegistry = Record<Channel, Notifier>;

export function createNotifiers(deps: AppDeps): NotifierRegistry {
  return {
    email: new EmailNotifier(deps.smtp),
    sms: new SmsNotifier(deps.twilio),
  };
}
```

Tests then swap in fakes per channel without module mocking.

Migration path for the 6 call sites: land `notifier.ts` + `notifiers.ts` first (pure addition, no behavior change), convert call sites one per commit replacing each switch with `notifierFor(...)`, then delete any now-unused direct imports of `EmailNotifier`/`SmsNotifier` outside the registry — ideally enforce that with an ESLint `no-restricted-imports` rule so future call sites can't bypass the map.
