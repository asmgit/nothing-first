# postgres-dedup-job — baseline

- AI model: `claude-fable-5`
- Time spent: 71 s
- Tokens spent: 39 165
- Language/stack version: PostgreSQL (targets 18.4, current stable at test date)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
We keep getting duplicate signups (same email, different casing/whitespace). Write a nightly cleanup job that scans the users table, groups by normalized email, keeps the oldest row and deletes the rest. Also a Slack alert with the count.
```

## Result

I checked the repo first — there's no `users` table here (the schema is party/element-based under `supabase/schemas/table/`), so here's the design and code I'd write generically, targeted at your stack (Supabase/Postgres), with names you can adjust.

## Design

Since you're on Supabase, the cleanest home for this is entirely inside Postgres: `pg_cron` for the nightly schedule, `pg_net` for the Slack webhook, and Vault for the webhook secret. No extra service or CI cron to maintain.

Flow: rank rows per `lower(btrim(email))` by `created_at` → archive everything ranked > 1 → delete it → post the count to Slack.

Two safety choices baked in: deleted rows are copied to an archive table first (user deletion is scary; this makes it recoverable), and everything runs in one transaction.

## Migration

```sql
create extension if not exists pg_cron;
create extension if not exists pg_net;

create table users_dedupe_archive (
  like users,
  archived_at timestamptz not null default now()
);

create or replace function dedupe_users()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  removed integer;
begin
  with ranked as (
    select id,
           row_number() over (
             partition by lower(btrim(email))
             order by created_at, id
           ) as rn
    from users
    where email is not null
  ),
  doomed as (
    select id from ranked where rn > 1
  ),
  archived as (
    insert into users_dedupe_archive
    select u.*, now()
    from users u
    join doomed d on d.id = u.id
  ),
  deleted as (
    delete from users u
    using doomed d
    where u.id = d.id
    returning u.id
  )
  select count(*) into removed from deleted;

  return removed;
end;
$$;

create or replace function notify_slack(message text)
returns void
language sql
security definer
as $$
  select net.http_post(
    url := (select decrypted_secret from vault.decrypted_secrets where name = 'slack_webhook_url'),
    body := jsonb_build_object('text', message)
  );
$$;

create or replace function run_nightly_user_dedupe()
returns void
language plpgsql
as $$
declare
  removed integer;
begin
  removed := dedupe_users();
  perform notify_slack(format('Nightly user dedupe: removed %s duplicate signup(s).', removed));
end;
$$;

select cron.schedule('nightly-user-dedupe', '0 3 * * *', $$select run_nightly_user_dedupe()$$);
```

One-time setup for the webhook (don't put it in a migration):

```sql
select vault.create_secret('https://hooks.slack.com/services/T000/B000/xxxx', 'slack_webhook_url');
```

If you'd rather only get pinged when something was actually deleted, wrap the `notify_slack` call in `if removed > 0 then … end if;` — but for a destructive nightly job I'd keep the always-on heartbeat message so silence means "job broke", not "no dupes".

## Three caveats worth acting on

1. **Foreign keys.** If anything references `users.id` (orders, sessions, profiles…), the `DELETE` will either fail or cascade-destroy child data. If duplicates can have activity attached, this should be a *merge*, not a delete — repoint children to the keeper first:

```sql
update child_table c
set user_id = keeper.id
from doomed d
join keeper_map keeper on ...
where c.user_id = d.id;
```

I'd confirm which tables reference `users` before shipping the job.

2. **"Oldest" may be the wrong keeper.** Often the *newer* row is the one that's email-verified or actively logged in. If you have `email_verified_at` / `last_sign_in_at`, consider ordering by those first, then `created_at`.

3. **Fix the source, keep the job as a safety net.** After the first clean run, add:

```sql
create unique index users_email_normalized_key on users (lower(btrim(email)));
```

and normalize (`trim` + `lowercase`) at signup time. That stops new duplicates at the door — the nightly job then just becomes a monitor that should always report 0.

If you're not actually running this in Postgres/Supabase and would rather have it as a Node script on a scheduler (GitHub Actions cron, k8s CronJob), say so and I'll write that variant — the SQL core stays the same, only the scheduling and Slack call move to the script.
