# defence-priced-choice — with-skill

- AI model: `claude-fable-5`
- Time spent: 122 s
- Tokens spent: 52 454
- Language/stack version: PostgreSQL (PostgreSQL Anonymizer extension)
- Test date: 2026-08-14
- Harness: nothing-first SKILL.md loaded and read before answering (domain annexes followed when relevant)
- Judge verdict: pending

## Prompt

```text
Our staging database is restored from a prod dump every night and PII has to be scrubbed in the process. Today a Python script walks every table after the restore and rewrites the sensitive columns: it takes 40 minutes and silently misses anything a developer adds later. Rewrite the script so it's faster and easier to maintain. Hard requirement from legal: no real email, phone number or full name may exist in staging, including in columns added after this work.
```

## Result

The script isn't in this repo (this is the pg_relation_sql extension), so here's the generic answer — and it starts with a refusal to rewrite it.

**A faster Python script can't meet the legal requirement.** Any scrubber that enumerates columns is a denylist: a column added tomorrow is unknown to it by definition, so "silently misses new columns" is not a bug in the script — it's the architecture. The fix is to invert the default (deny-by-default) and hand enforcement to an engine instead of a nightly walker. That engine already exists: **PostgreSQL Anonymizer** — don't hand-roll a twin of it.

The whole design is three declarations plus one changed dump command:

**1. Masking rules live in the schema, versioned in migrations next to the columns they mask**

```sql
SECURITY LABEL FOR anon ON COLUMN users.email IS 'MASKED WITH FUNCTION anon.fake_email()';
SECURITY LABEL FOR anon ON COLUMN users.phone IS 'MASKED WITH FUNCTION anon.random_phone()';
SECURITY LABEL FOR anon ON COLUMN users.first_name IS 'MASKED WITH FUNCTION anon.fake_first_name()';
SECURITY LABEL FOR anon ON COLUMN orders.status IS 'NOT MASKED';
```

**2. Deny by default — this is what covers columns added later**

```sql
ALTER DATABASE app SET anon.privacy_by_default = on;
```

Every column without a rule is masked to its default/NULL. A forgotten new column arrives in staging **empty**, never leaked — the failure mode flips from silent leak to visible annoyance, and the dev fixes it by adding a one-line label in the same migration that added the column.

**3. Dump through a masked role — the 40-minute post-restore pass is deleted, not sped up**

```sql
CREATE ROLE staging_dumper LOGIN;
ALTER ROLE staging_dumper SET anon.transparent_dynamic_masking = on;
SECURITY LABEL FOR anon ON ROLE staging_dumper IS 'MASKED';
GRANT pg_read_all_data TO staging_dumper;
```

Nightly job becomes `pg_dump --no-security-labels -U staging_dumper … | pg_restore/psql` into staging. Data is masked in-stream during the dump, so real PII **never exists in staging at any moment** — which today's setup violates during the restore-then-scrub window, something legal would likely care about.

**4. One end-to-end check** (the only moving part worth keeping): plant one synthetic canary row in prod with a distinctive real-looking email/phone/name; after each restore, one `psql` assertion that none of the three values exists anywhere in staging. If it ever fires, the pipeline is broken — everything else is enforced by the engine.

The cheaper option I'm rejecting explicitly: keep the Python script but convert row loops to set-based server-side `UPDATE`s. That fixes the 40 minutes for an afternoon's work — but the column list stays hand-maintained, so the hard requirement stays unmet. Since the requirement is a compliance fact, speed-only doesn't count as done.

One constraint to check on your side: anonymous dumps need the extension on the source (prod or a read replica). If installing on prod is off the table, run the dump from a replica; failing that, restore into a quarantine database no developer can reach, run `SELECT anon.anonymize_database()` there (same labels, same privacy-by-default), and only then expose it as staging.

Sources:
- [Anonymous Dumps — PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/en/stable/anonymous_dumps/)
- [Privacy by Default / masking rules — PostgreSQL Anonymizer docs](https://postgresql-anonymizer.readthedocs.io/en/latest/)
- [Dynamic Masking — PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io/en/latest/dynamic_masking/)
