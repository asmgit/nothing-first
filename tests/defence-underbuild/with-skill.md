# defence-underbuild — with-skill

- AI model: `claude-fable-5`
- Time spent: 82 s
- Tokens spent: 48 773
- Language/stack version: Python + PostgreSQL (no version pinned by the prompt)
- Test date: 2026-08-14
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)
- Judge verdict: pending

## Prompt

```text
Ship the invoice PDF generator today, we're late. Keep it minimal — pull the order rows, format the numbers, render the template. Requirement from finance: the printed totals must reconcile with the ledger to the cent, and about a third of our orders are multi-currency.
```

## Result

Checked the workspace first: this repo (`pg_relation_sql`) is the Postgres-extension article project — `ls` and grep show no order, ledger, or invoice code here, so I can't ship files into the right codebase from this session. What I can ship today is the design decided, and it's smaller than the naive version, not bigger.

**The requirement decides the architecture.** "Reconcile to the cent" plus multi-currency rules out the obvious reading of "pull the order rows, format, render" — if the generator recomputes totals (price × qty, tax, rounding, FX) it will drift from the ledger whenever rounding order or conversion timing differs, and you'll be patching penny bugs forever. The minimal correct generator computes **nothing**:

1. **Render the ledger's own numbers.** One query pulls the posted line amounts and sums them per currency, from the same rows the ledger sums. Reconciliation becomes true by construction, not by testing. This also deletes entities the naive plan would need: no rounding-allocation logic, no FX conversion at render time, no rounding-mode config.
2. **Exact numerics end to end** — `NUMERIC`/integer minor units; floats never touch money. Formatting happens only at the render edge, via the platform's currency formatter (`Intl.NumberFormat` or your stack's equivalent), because "cent" is per-currency: JPY has 0 decimals, KWD/BHD have 3 — a hardcoded `/100` + two decimals silently fails a third of your orders.
3. **Never add across currencies.** The invoice shows one total block per currency (`GROUP BY currency`). If finance wants a single base-currency grand total, it must be the sum of the ledger's *posted* converted amounts (the rate stored at posting), not a fresh rate lookup — a fresh rate can't reconcile by definition.
4. **One reconciliation gate, not a test suite:** before writing the PDF, assert rendered per-currency totals == ledger per-currency totals for that order; on mismatch, fail generation loudly instead of printing a wrong invoice. That's the single check that catches any future formatting/query regression.
5. **Template and PDF: reuse what the stack already has** (existing HTML template engine + whatever HTML→PDF path exists — Chromium print, WeasyPrint, wkhtmltopdf). No new PDF dependency if one is already in the tree.

The cheaper-looking alternative — recompute totals in app code — was priced and loses on both axes: more code *and* it misses the stated requirement. So "minimal" and "correct" are the same build here; nothing about the deadline forces a trade.

To materialize it today I need two facts: which repo/stack the generator lives in, and where the ledger postings for an order are queryable (table/view name). Point me at the codebase and I'll write the query, the formatter edge, and the reconciliation gate — that's the whole generator, roughly three small units plus the template.
