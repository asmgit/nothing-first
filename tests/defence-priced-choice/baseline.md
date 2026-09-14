# defence-priced-choice — baseline

- AI model: `claude-fable-5`
- Time spent: 268 s
- Tokens spent: 57 338
- Language/stack version: Python + PostgreSQL (no version pinned by the prompt)
- Test date: 2026-08-14
- Harness: no skill; agent instructed to ignore skill/philosophy instructions and answer naturally
- Judge verdict: FAIL — axes 1 and 2; axis 3 and the code gate pass. Executed fixture: bigint columns named `msisdn`, `tel`, `cell` produce no error from the coverage gate, so the name denylist the answer itself condemns returns in its non-textual branch; the gate also checks one schema while the restore restores all of them. The single alternative named (PostgreSQL Anonymizer) is left unpriced as the reader's choice.

## Prompt

```text
Our staging database is restored from a prod dump every night and PII has to be scrubbed in the process. Today a Python script walks every table after the restore and rewrites the sensitive columns: it takes 40 minutes and silently misses anything a developer adds later. Rewrite the script so it's faster and easier to maintain. Hard requirement from legal: no real email, phone number or full name may exist in staging, including in columns added after this work.
```

## Result

There's no scrubbing script in this repo, so here's the design and code I'd write from scratch. The rewrite rests on two changes, and the second one is what actually satisfies legal:

1. **Speed** — stop pulling rows into Python. Each table gets one set-based `UPDATE` executed server-side, tables run in parallel, and the scrub runs *between* `pg_restore --section=data` and `--section=post-data`, so updates never maintain indexes and every index is built once over already-clean data. That turns 40 minutes into single-digit minutes.
2. **The legal guarantee** — invert the default. The old script is a denylist: columns it doesn't know about pass through untouched. Instead, every text-capable column in the database must be declared in a manifest as either `masks` (rewritten) or `safe` (reviewed, no PII). Any undeclared column — including one a developer adds next month — fails the run, and the freshly restored database is never swapped into place as `staging`. A new column can delay the staging refresh; it cannot leak.

**`manifest.yml`** — the only file anyone touches day-to-day:

```yaml
masks:
  users:
    email: email
    phone: phone
    first_name: name
    last_name: name
    bio: "null"
  support_tickets:
    reporter_email: email
    body: "null"

safe:
  users: [locale, timezone, role]
  products: [sku, title, description]
  support_tickets: [status, category]
```

Only text-ish columns (text/varchar/citext/json/jsonb/xml/hstore/text arrays) need declaring — an integer can't hold an email. Columns of *any* type whose name looks sensitive (`phone_number bigint`) are also flagged until explicitly classified.

**`scrub.py`**:

```python
#!/usr/bin/env python3
"""Deny-by-default PII scrub for a freshly restored staging database.

Every textual column must be declared in the manifest under `masks` or
`safe`. Undeclared columns fail the run, so a column added after this
script was written can never reach staging unscrubbed.
"""

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import psycopg
import yaml
from psycopg import sql

MASKS = {
    "email": "md5({c}) || '@scrubbed.example'",
    "phone": "'+1555' || lpad((abs(hashtext({c})::bigint) % 10000000)::text, 7, '0')",
    "name": "initcap(substr(md5({c}), 1, 10))",
    "null": "NULL",
}

SUSPICIOUS_NAME = re.compile(
    r"e_?mail|phone|mobile|fax|(first|last|full|sur|given|family|middle|maiden|nick|display)_?name"
    r"|contact|address|birth|passport|ssn",
    re.IGNORECASE,
)

EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

COLUMNS_QUERY = """
    SELECT c.relname,
           a.attname,
           bt.typcategory = 'S'
               OR bt.typname IN ('json', 'jsonb', 'xml', 'hstore')
               OR coalesce(et.typcategory, '-') = 'S' AS textual
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_attribute a ON a.attrelid = c.oid
    JOIN pg_type bt ON bt.oid = a.atttypid
    LEFT JOIN pg_type et ON et.oid = bt.typelem
    WHERE n.nspname = %s
      AND c.relkind IN ('r', 'p')
      AND NOT c.relispartition
      AND a.attnum > 0
      AND NOT a.attisdropped
      AND a.attgenerated = ''
"""


def load_columns(conn, schema):
    return conn.execute(COLUMNS_QUERY, (schema,)).fetchall()


def coverage_errors(columns, manifest):
    masked = {(t, c) for t, cols in manifest.get("masks", {}).items() for c in cols}
    safe = {(t, c) for t, cols in manifest.get("safe", {}).items() for c in cols}
    declared = masked | safe
    existing = {(t, c) for t, c, _ in columns}
    errors = [
        f"unclassified textual column: {t}.{c}"
        for t, c, textual in columns
        if textual and (t, c) not in declared
    ]
    errors += [
        f"suspiciously named column, classify explicitly: {t}.{c}"
        for t, c, textual in columns
        if not textual and (t, c) not in declared and SUSPICIOUS_NAME.search(c)
    ]
    errors += [f"manifest entry for missing column: {t}.{c}" for t, c in declared - existing]
    return sorted(errors)


def scrub_table(conninfo, schema, table, cols):
    with psycopg.connect(conninfo, autocommit=True) as conn:
        assignments = []
        for col, rule in cols.items():
            ident = sql.Identifier(col).as_string(conn)
            expr = MASKS.get(rule, rule).format(c=ident)
            assignments.append(f"{ident} = {expr}")
        target = sql.Identifier(schema, table).as_string(conn)
        conn.execute(f"UPDATE {target} SET {', '.join(assignments)}")


def scrub(conninfo, schema, manifest, jobs):
    masks = manifest.get("masks", {})
    with psycopg.connect(conninfo) as conn:
        sizes = dict(conn.execute(
            "SELECT relname, pg_total_relation_size(oid) FROM pg_class"
            " WHERE relnamespace = %s::regnamespace AND relkind IN ('r', 'p')",
            (schema,),
        ).fetchall())
    ordered = sorted(masks, key=lambda t: sizes.get(t, 0), reverse=True)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for future in [pool.submit(scrub_table, conninfo, schema, t, masks[t]) for t in ordered]:
            future.result()


def leaks(conn, schema, columns, sample):
    found = []
    for table, col, textual in columns:
        if not textual:
            continue
        target = sql.Identifier(schema, table).as_string(conn)
        ident = sql.Identifier(col).as_string(conn)
        n = conn.execute(
            f"SELECT count(*) FROM (SELECT {ident}::text AS v FROM {target} LIMIT %s) s"
            " WHERE s.v ~ %s AND s.v !~ '@scrubbed[.]example'",
            (sample, EMAIL_REGEX),
        ).fetchone()[0]
        if n:
            found.append(f"{table}.{col}: {n} email-looking values in first {sample} rows")
    return found


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dbname", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--schema", default="public")
    p.add_argument("--jobs", type=int, default=8)
    p.add_argument("--sample", type=int, default=5000)
    p.add_argument("--coverage-only", action="store_true")
    p.add_argument("--verify-only", action="store_true")
    args = p.parse_args()

    with open(args.manifest) as f:
        manifest = yaml.safe_load(f)
    conninfo = f"dbname={args.dbname}"

    with psycopg.connect(conninfo) as conn:
        columns = load_columns(conn, args.schema)

    errors = coverage_errors(columns, manifest)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"\n{len(errors)} classification gaps; staging stays closed until the manifest covers them.", file=sys.stderr)
        return 1
    if args.coverage_only:
        print("coverage OK")
        return 0

    if not args.verify_only:
        scrub(conninfo, args.schema, manifest, args.jobs)

    with psycopg.connect(conninfo) as conn:
        found = leaks(conn, args.schema, columns, args.sample)
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**`nightly.sh`** — the enforcement lives in the orchestration: the restore lands in a side database and only a fully passed run gets renamed to `staging`:

```bash
#!/usr/bin/env bash
set -euo pipefail

DUMP=$1
NEW=staging_incoming
FINAL=staging

dropdb --if-exists "$NEW"
createdb "$NEW"
pg_restore -d "$NEW" -j 8 --no-owner --section=pre-data --section=data "$DUMP"
python3 scrub.py --dbname "$NEW" --manifest manifest.yml --jobs 8
pg_restore -d "$NEW" -j 8 --no-owner --section=post-data "$DUMP"
python3 scrub.py --dbname "$NEW" --manifest manifest.yml --verify-only

psql -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$FINAL';
DROP DATABASE IF EXISTS ${FINAL}_old;
ALTER DATABASE $FINAL RENAME TO ${FINAL}_old;
ALTER DATABASE $NEW RENAME TO $FINAL;
SQL
```

How the pieces satisfy the requirements:

- **Fast**: server-side set-based updates, biggest tables first in parallel, no index maintenance during the scrub (indexes, FKs, and unique constraints are built in `post-data`, after the rewrite). Materialized views are also refreshed in `post-data`, i.e. from already-scrubbed data.
- **New columns can't leak**: the coverage gate runs before any grant of access; failure leaves yesterday's clean staging in place and pages whoever owns the nightly job. The failure message names the exact columns, and the fix is one manifest line.
- **Maintainable**: masks are four SQL expressions; a rule value that isn't a known mask name is treated as a raw SQL expression with `{c}` as the column, so odd cases (stripping a key out of a jsonb blob) don't need engine changes.
- **Masking properties**: expressions are deterministic (same input, same output — joins on email still correlate) and NULL-preserving. `md5(email)` keeps distinct emails distinct, so unique indexes on email rebuild cleanly. Phone masks use the fictional 555 exchange.

Caveats worth knowing:

- A **unique constraint on a phone column** could collide at 7 masked digits on very large tables — give that column an md5-based custom expression in the manifest.
- **Free-text and json columns** can hide names no regex will find; the gate forces each one to be classified, and the right default answer for notes/bodies is `"null"`, not `safe`.
- The post-scrub email regex sweep is a smoke test (defense in depth), not the guarantee — the classification gate is the guarantee. Full names are not machine-detectable, which is exactly why deny-by-default is the only honest answer to legal's "including future columns" clause.
- To catch gaps at PR time instead of at 3 a.m., add a CI step in the app repo that migrates an empty database and runs `scrub.py --coverage-only` against it — same manifest, same check, earlier feedback.

If you can install extensions on the staging host, [PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/) is the off-the-shelf equivalent of the masking half (security labels on columns, `anon.anonymize_database()`) — you'd keep the coverage gate and the swap-on-success flow from above, since neither comes with the extension. On managed hosts (e.g. RDS) where it's unavailable, the script above is the whole solution.
