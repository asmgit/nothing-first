# typescript-justified-interface — with-skill

- AI model: `claude-fable-5`
- Time spent: 65 s
- Tokens spent: 43 067
- Language/stack version: TypeScript 7 (pinned in prompt; 7.0.2 current stable at test date)
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
TypeScript 7: we now have two real notifier implementations in prod — EmailNotifier and SmsNotifier — with duplicated switch logic at 6 call sites choosing between them. Unify the call sites behind one Notifier interface and a channel map.
```

## Result

В репо кода нотифаеров нет — отвечаю предлагаемым дизайном.

По лестнице: второй имплементатор — уже факт, значит шов заработан и унификация легитимна. Но запрошен механизм (interface + map), а требование — «6 колл-сайтов не должны дублировать выбор канала». Проверка каждой сущности:

- **Номинальный `interface Notifier` + `implements` — rung 0.** В TypeScript типизация структурная: если у обоих классов уже есть одинаковый `send`, общий тип существует неявно. Достаточно type alias, прод-классы не трогаем.
- **Если нотифаеры по сути функции — интерфейс схлопывается в function type.** Интерфейс с одним методом — это функция в маскараде.
- **Channel map — да, это правильный ход:** один механизм, параметризованный данными, вместо 6 специальных. Но тип `Channel` не объявляем руками — **выводим из карты** (`keyof typeof`), тогда исчерпываемость форсит компилятор (rung 2), а не ручной `default: throw` в каждом switch.
- **Обёртка `notify(channel, msg)` — не нужна.** Лукап и так одно выражение; экспортируем карту.

```ts
export type Message = { to: string; body: string }
export type Notify = (msg: Message) => Promise<void>

export const notifiers = {
  email: sendEmail,
  sms: sendSms,
} satisfies Record<string, Notify>

export type Channel = keyof typeof notifiers
```

Колл-сайты (все 6):

```ts
await notifiers[channel](msg)
```

Если имплементации — классы, держащие сконфигурированные клиенты (SMTP, Twilio), и в функции их не свести:

```ts
export type Notifier = { send(msg: Message): Promise<void> }

export const notifiers = {
  email: new EmailNotifier(emailCfg),
  sms: new SmsNotifier(smsCfg),
} satisfies Record<string, Notifier>
```

`EmailNotifier`/`SmsNotifier` не объявляют `implements` — структурная типизация покрывает.

Что удаляет пасс:

- 6 switch-блоков и все их `default`-ветки с throw
- ручные exhaustiveness-проверки (`never`-трюки) — `keyof typeof` делает это декларативно
- пер-сайтовую валидацию канала: параметр типа `Channel` запрещает невалидный канал на компиляции; если строка приходит извне (API/БД) — один `channel in notifiers` на границе, не шесть

Новый канал = одна строка в карте, ноль правок в колл-сайтах. Кросс-каттинг (retry, логирование) заворачивается в одном месте, когда станет фактом — не раньше.

Absence test пройден: без карты сегодня ломается реальное — 6 дублей уже разъезжаются. Interface-механизм из запроса ужат до type alias с нулевым рантаймом; единственная новая рантайм-сущность — сама карта.
