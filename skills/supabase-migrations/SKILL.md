---
name: supabase-migrations
description: Write and review Postgres migrations for a self-hosted Supabase project — numbering, RLS policies, grants, idempotency and the PostgREST schema reload. Use when adding a table, changing a column, writing an RPC, or reviewing a migration before it runs against production.
---

# Supabase migrations

Self-hosted Supabase fails differently from managed Supabase. The failures are quiet: the
migration succeeds, the API returns an empty array, and nothing anywhere reports an error.
This skill is the checklist that catches those before they ship.

## When to use this

Writing a migration, reviewing one, or debugging "the table exists but the API says it
does not".

## The order that matters

1. **Take the next free number.** Never reuse one, never renumber an applied migration.

   ```bash
   ls migrations/ | sort -V | tail -1
   ```

2. **Write the DDL idempotently.** `create table if not exists`, `add column if not
   exists`, `drop policy if exists` before `create policy`. A migration that cannot be
   run twice will eventually be run twice.

3. **Grant, then policy, then enable.** Row Level Security without a grant returns
   permission-denied; a grant without RLS exposes every row. Both, in that order.

4. **End with the schema reload.**

   ```sql
   notify pgrst, 'reload schema';
   ```

   This is the one that gets forgotten. PostgREST caches the schema at boot. Without this
   line the table exists in Postgres and does not exist over the API, and every symptom
   points at your client code.

5. **Verify against the database, not against the file.**

   ```bash
   bash scripts/verify.sh <table_name>
   ```

## Template

```sql
-- 00NN_<what_it_does>.sql
-- <one line: why this exists>

create table if not exists public.thing (
  id          uuid primary key default gen_random_uuid(),
  slug        text unique not null,
  status      text not null default 'draft'
                check (status in ('draft', 'published', 'archived')),
  payload     jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index if not exists thing_status_idx on public.thing (status)
  where status = 'published';

alter table public.thing enable row level security;

grant select on public.thing to anon, authenticated;
grant all    on public.thing to service_role;

drop policy if exists "thing: public reads published" on public.thing;
create policy "thing: public reads published"
  on public.thing for select
  to anon, authenticated
  using (status = 'published');

drop policy if exists "thing: service_role full access" on public.thing;
create policy "thing: service_role full access"
  on public.thing for all
  to service_role
  using (true) with check (true);

notify pgrst, 'reload schema';
```

## RPCs

A function the API can call needs `security definer` only when it must bypass RLS, and
then it needs a pinned `search_path` or it is an escalation path:

```sql
create or replace function public.increment_counter(p_slug text, p_kind text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.thing
     set payload = jsonb_set(
           payload, array['counts', p_kind],
           to_jsonb(coalesce((payload->'counts'->>p_kind)::int, 0) + 1)),
         updated_at = now()
   where slug = p_slug;
end;
$$;

revoke all on function public.increment_counter(text, text) from public;
grant execute on function public.increment_counter(text, text) to anon, authenticated;
```

`revoke ... from public` first, then grant to the roles that need it. Creating a function
grants execute to `public` by default, which is almost never what you want for a
`security definer`.

## Failure modes, and what they actually mean

| Symptom | Cause |
|---------|-------|
| API returns `[]`, table has rows | RLS on, no policy for that role. Not a query bug |
| API returns "relation does not exist" | Missing `notify pgrst, 'reload schema'` |
| Works as service_role, not as anon | Grant present, policy missing (or the reverse) |
| Insert silently drops rows | Policy has `using` but no `with check` |
| Migration passes locally, fails in prod | Different extension set. Check `gen_random_uuid` |

## Before it runs against production

- Read the whole file top to bottom, out of the diff.
- Confirm nothing is destructive: no bare `drop table`, no `alter column ... type` without
  a `using`, no `delete from` without a `where`.
- Confirm it ends with the notify line.
- Run it against a scratch database first if one exists.
- Never run it as part of the same step that writes it.

## Files

- `scripts/verify.sh` — post-migration verification: table exists, RLS on, policies
  present, and the anon role can actually read what it should.
