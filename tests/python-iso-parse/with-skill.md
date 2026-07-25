# python-iso-parse — with-skill

- AI model: `claude-fable-5`
- Time spent: 26 s
- Tokens spent: 40 289
- Language/stack version: Python 3.14 (pinned in prompt; 3.14.6 current stable at test date)
- Test date: 2026-07-25
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)

## Prompt

```text
Python 3.14: parse an ISO-8601 timestamp string into a timezone-aware datetime; treat naive input as UTC.
```

## Result

Rung 0 holds: the stdlib already covers this entirely. Since 3.11, `datetime.fromisoformat` parses full ISO-8601 (including the `Z` suffix, fractional seconds, `±HH:MM` offsets), so no `dateutil`/`arrow`/`pendulum` dependency and no hand-rolled parsing. The only delta the primitive doesn't cover — naive means UTC — is a one-line use of it:

```python
from datetime import UTC, datetime

dt = datetime.fromisoformat(s)
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=UTC)
```

Notes:

- `replace(tzinfo=UTC)`, not `astimezone(UTC)` — the naive value already denotes UTC wall time; `astimezone` would reinterpret it as local time and shift it.
- `dt.tzinfo is None` is the exact awareness test for `fromisoformat` output (it only ever yields `None` or a fixed-offset `timezone`).
- No wrapper function: with one call site, these two lines are the seam. Name it (`def parse_utc(s: str) -> datetime:` returning `dt if dt.tzinfo else dt.replace(tzinfo=UTC)`) only when a second call site is a fact.
