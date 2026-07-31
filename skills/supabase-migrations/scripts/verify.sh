#!/usr/bin/env bash
# Verify a table after a migration ran: it exists, RLS is on, policies are present,
# grants are right, and PostgREST has actually reloaded its schema.
#
# Usage:
#   ./verify.sh <table_name> [schema]
#
# Environment:
#   PSQL      how to reach the database (default: "psql -U postgres -d postgres")
#             self-hosted docker example:
#               PSQL="docker exec -i supabase-db psql -U postgres -d postgres"
#   REST_URL  optional PostgREST base URL; when set, the script also checks the API
#   ANON_KEY  anon JWT, required when REST_URL is set

set -euo pipefail

TABLE="${1:?usage: verify.sh <table_name> [schema]}"
SCHEMA="${2:-public}"
PSQL="${PSQL:-psql -U postgres -d postgres}"

q() { $PSQL -tAX -c "$1"; }

fail=0
note() { printf '  %-8s %s\n' "$1" "$2"; }
ok()   { note "ok" "$1"; }
bad()  { note "FAIL" "$1"; fail=1; }

echo "Verifying ${SCHEMA}.${TABLE}"

# 1. exists ------------------------------------------------------------------
if [ "$(q "select count(*) from pg_tables where schemaname='${SCHEMA}' and tablename='${TABLE}'")" = "1" ]; then
  ok "table exists"
else
  bad "table ${SCHEMA}.${TABLE} does not exist — the migration did not run"
  exit 1
fi

# 2. row level security ------------------------------------------------------
if [ "$(q "select relrowsecurity from pg_class where oid='${SCHEMA}.${TABLE}'::regclass")" = "t" ]; then
  ok "row level security enabled"
else
  bad "RLS is OFF — every row is readable by anyone holding the anon key"
fi

# 3. policies ----------------------------------------------------------------
POLICIES=$(q "select count(*) from pg_policies where schemaname='${SCHEMA}' and tablename='${TABLE}'")
if [ "$POLICIES" -gt 0 ]; then
  ok "${POLICIES} policy/policies"
  $PSQL -tAX -c "select '           - '||policyname||'  ('||cmd||' → '||array_to_string(roles,',')||')'
                   from pg_policies
                  where schemaname='${SCHEMA}' and tablename='${TABLE}'
                  order by policyname"
else
  bad "RLS is on but there are NO policies — the API will return an empty array"
fi

# 4. grants ------------------------------------------------------------------
for role in anon service_role; do
  GRANTS=$(q "select string_agg(distinct privilege_type, ',' order by privilege_type)
                from information_schema.role_table_grants
               where table_schema='${SCHEMA}' and table_name='${TABLE}' and grantee='${role}'")
  if [ -n "$GRANTS" ]; then
    ok "grants for ${role}: ${GRANTS}"
  else
    bad "no grants for ${role} — RLS policies alone are not enough"
  fi
done

# 5. postgrest sees it -------------------------------------------------------
if [ -n "${REST_URL:-}" ]; then
  if [ -z "${ANON_KEY:-}" ]; then
    bad "REST_URL is set but ANON_KEY is not"
  else
    CODE=$(curl -s -o /dev/null -w '%{http_code}' \
      -H "apikey: ${ANON_KEY}" -H "Authorization: Bearer ${ANON_KEY}" \
      "${REST_URL%/}/${TABLE}?select=*&limit=1")
    case "$CODE" in
      200) ok "PostgREST serves the table (200)" ;;
      404) bad "PostgREST returns 404 — the schema cache is stale. Run: notify pgrst, 'reload schema';" ;;
      *)   bad "PostgREST returned ${CODE}" ;;
    esac
  fi
else
  note "skip" "PostgREST check (set REST_URL and ANON_KEY to enable)"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "All checks passed."
else
  echo "Some checks FAILED — see above." >&2
fi
exit "$fail"
