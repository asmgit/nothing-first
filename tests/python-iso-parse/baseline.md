# python-iso-parse — baseline

- AI model: `claude-fable-5`
- Time spent: 20 s
- Tokens spent: 35 177
- Language/stack version: Python 3.14 (pinned in prompt; 3.14.6 current stable at test date)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
Python 3.14: parse an ISO-8601 timestamp string into a timezone-aware datetime; treat naive input as UTC.
```

## Result

`datetime.fromisoformat` handles this natively — since Python 3.11 it accepts most ISO-8601 forms, including the `Z` suffix, so no third-party parser is needed.

```python
from datetime import UTC, datetime

def parse_timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
```

Behavior:

```python
parse_timestamp("2026-07-25T10:30:00+02:00")   # keeps the +02:00 offset
parse_timestamp("2026-07-25T10:30:00Z")        # tzinfo=UTC
parse_timestamp("2026-07-25T10:30:00")         # naive -> assumed UTC
parse_timestamp("2026-07-25T10:30:00.123456")  # fractional seconds fine
parse_timestamp("2026-07-25")                  # date only -> midnight UTC
```

Notes:

- `dt.replace(tzinfo=UTC)` is the right call for "treat naive as UTC" — it attaches the zone without shifting the clock time. Don't use `astimezone(UTC)` on a naive datetime; that would interpret it as *local* time and convert.
- `UTC` is the module-level alias for `timezone.utc` (available since 3.11).
- Invalid input raises `ValueError`, which is usually what you want to propagate or catch at the call site.
- If you need to *normalize* everything to UTC (not just tag naive values), add `.astimezone(UTC)` on the aware branch: `return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)`.

One caveat: `fromisoformat` covers most but not the entire ISO-8601 grammar (e.g. week dates like `2026-W30-6T10:30` are not accepted). If you must accept arbitrary ISO-8601, use `whenever` or `ciso8601`; for typical API/log timestamps the stdlib version above is all you need.
