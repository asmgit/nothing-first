# defence-underbuild — baseline

- AI model: `claude-fable-5`
- Time spent: 87 s
- Tokens spent: 44 086
- Language/stack version: Python + PostgreSQL (no version pinned by the prompt)
- Test date: 2026-08-14
- Harness: no skill; agent instructed to ignore skill/philosophy instructions and answer naturally
- Judge verdict: pending

## Prompt

```text
Ship the invoice PDF generator today, we're late. Keep it minimal — pull the order rows, format the numbers, render the template. Requirement from finance: the printed totals must reconcile with the ledger to the cent, and about a third of our orders are multi-currency.
```

## Result

This repo is the pg_relation_sql extension — there's no invoicing codebase here, so here's the drop-in generator I'd ship, with the two decisions that make the finance requirement hold. Point me at the actual repo/stack and I'll wire it in.

## Design (3 decisions, all driven by "reconcile to the cent")

1. **Never recompute money — render what's persisted.** The PDF pulls stored line totals and the stored order/ledger totals. No `qty × price` arithmetic at render time: any independent recomputation is a chance to round differently than the ledger did.
2. **Integer minor units, no floats.** Amounts travel as `Decimal` from the driver, converted to integer cents (JPY = 0 decimals, BHD = 3) with an exactness check. If a stored value has sub-minor-unit precision, that's a data bug — we raise, not round.
3. **Multi-currency = one totals block per currency, and fail closed.** Lines group by currency; each currency gets its own subtotal/total. No synthetic combined total (that would need FX and could never reconcile). Before rendering, sum-of-lines is compared to the ledger total per currency — mismatch aborts with a nonzero exit instead of printing a wrong invoice.

## Code

`invoices/money.py`

```python
from decimal import Decimal

MINOR_UNITS = {
    "USD": 2, "EUR": 2, "GBP": 2, "CHF": 2, "CAD": 2, "AUD": 2,
    "JPY": 0, "KRW": 0, "KWD": 3, "BHD": 3,
}

def to_minor(amount: Decimal, currency: str) -> int:
    scaled = amount.scaleb(MINOR_UNITS[currency])
    if scaled != scaled.to_integral_value():
        raise ValueError(f"{amount} {currency} has sub-minor-unit precision")
    return int(scaled)

def fmt(minor: int, currency: str) -> str:
    exp = MINOR_UNITS[currency]
    sign = "-" if minor < 0 else ""
    if exp == 0:
        return f"{sign}{abs(minor):,} {currency}"
    units, cents = divmod(abs(minor), 10 ** exp)
    return f"{sign}{units:,}.{cents:0{exp}d} {currency}"
```

`invoices/generate.py`

```python
import sys
from collections import defaultdict

import psycopg
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from .money import to_minor, fmt

LINES_SQL = """
SELECT ol.description, ol.quantity, ol.unit_price, ol.line_total, ol.currency
FROM order_lines ol
WHERE ol.order_id = %s
ORDER BY ol.currency, ol.position
"""

LEDGER_TOTALS_SQL = """
SELECT currency, SUM(amount) AS total
FROM ledger_entries
WHERE order_id = %s AND entry_type = 'receivable'
GROUP BY currency
"""

ORDER_SQL = "SELECT number, customer_name, issued_at FROM orders WHERE id = %s"


class ReconciliationError(Exception):
    pass


def build_context(conn, order_id):
    with conn.cursor() as cur:
        cur.execute(ORDER_SQL, (order_id,))
        number, customer, issued_at = cur.fetchone()
        cur.execute(LINES_SQL, (order_id,))
        raw_lines = cur.fetchall()
        cur.execute(LEDGER_TOTALS_SQL, (order_id,))
        ledger = {ccy: to_minor(total, ccy) for ccy, total in cur.fetchall()}

    groups = defaultdict(list)
    for description, qty, unit_price, line_total, ccy in raw_lines:
        groups[ccy].append({
            "description": description,
            "qty": qty,
            "unit_price": fmt(to_minor(unit_price, ccy), ccy),
            "total": fmt(to_minor(line_total, ccy), ccy),
            "total_minor": to_minor(line_total, ccy),
        })

    sections = []
    for ccy, lines in sorted(groups.items()):
        line_sum = sum(l["total_minor"] for l in lines)
        if line_sum != ledger.get(ccy):
            raise ReconciliationError(
                f"order {order_id} {ccy}: lines sum to {fmt(line_sum, ccy)}, "
                f"ledger has {fmt(ledger[ccy], ccy) if ccy in ledger else 'no entry'}"
            )
        sections.append({"currency": ccy, "lines": lines, "total": fmt(line_sum, ccy)})

    unbilled = set(ledger) - set(groups)
    if unbilled:
        raise ReconciliationError(f"order {order_id}: ledger has {unbilled} with no invoice lines")

    return {"number": number, "customer": customer, "issued_at": issued_at, "sections": sections}


def main():
    order_id, out_path = sys.argv[1], sys.argv[2]
    env = Environment(loader=FileSystemLoader("invoices/templates"), autoescape=True)
    with psycopg.connect() as conn:
        ctx = build_context(conn, order_id)
    html = env.get_template("invoice.html").render(**ctx)
    HTML(string=html).write_pdf(out_path)


if __name__ == "__main__":
    main()
```

`invoices/templates/invoice.html`

```html
<style>
  body { font: 11pt/1.4 sans-serif; margin: 2cm; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 1.5em; }
  th, td { padding: 4pt 8pt; border-bottom: 0.5pt solid #999; text-align: left; }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  tr.total td { font-weight: bold; border-top: 1.5pt solid #000; border-bottom: none; }
</style>
<h1>Invoice {{ number }}</h1>
<p>{{ customer }} — {{ issued_at.strftime("%Y-%m-%d") }}</p>
{% for s in sections %}
<table>
  <tr><th>Description</th><th class="num">Qty</th><th class="num">Unit price</th><th class="num">Amount</th></tr>
  {% for l in s.lines %}
  <tr><td>{{ l.description }}</td><td class="num">{{ l.qty }}</td><td class="num">{{ l.unit_price }}</td><td class="num">{{ l.total }}</td></tr>
  {% endfor %}
  <tr class="total"><td colspan="3">Total {{ s.currency }}</td><td class="num">{{ s.total }}</td></tr>
</table>
{% endfor %}
```

Install and run:

```
pip install psycopg jinja2 weasyprint
python -m invoices.generate <order_id> invoice.pdf
```

## Two schema assumptions to confirm before shipping

- **`LEDGER_TOTALS_SQL`** — I guessed `ledger_entries(order_id, entry_type, amount, currency)`. Swap in whatever table the ledger actually posts from; the reconciliation guarantee is only as good as querying the *same source finance reconciles against*.
- **`order_lines.line_total` is stored**, not derived. If your schema only stores `unit_price` and computes totals on the fly, that's the first thing to fix — otherwise the PDF must replicate the ledger's exact rounding rule (per-line vs per-invoice, half-up vs half-even), which is exactly the fragility the stored-total design avoids.

If tax or discounts exist as separate ledger lines, they need matching rows in the query (same pattern: pull stored amounts, include in the per-currency sum). The fail-closed check means a gap there shows up as a loud `ReconciliationError` on the first real order, not as a quietly wrong invoice.
