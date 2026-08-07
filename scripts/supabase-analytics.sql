-- ============================================================================
-- Analytics events table for virginiabasementwaterproofing.org
--
-- Table name is site-specific (`virginiabasementwaterproofing_dashboard`) so it
-- can live in the same Supabase project as the dashboards for your other
-- directory sites without colliding.
--
-- HOW TO RUN: Supabase dashboard -> SQL Editor -> paste -> Run.
-- Safe to re-run: every statement is guarded with IF NOT EXISTS or a DO block.
--
-- PRIVACY NOTE: this table intentionally holds NO personally identifying
-- information -- only URL paths, event type names, and two random ids the
-- browser generates for itself (session_id / visitor_id). That is what makes
-- the public SELECT policy below acceptable: the dashboard at /dashboard/ is
-- deliberately public (no login), and Supabase Realtime requires a readable
-- policy for the browser to subscribe to postgres_changes.
-- Real lead data with contact details stays in the separate `leads` table,
-- which is NOT publicly readable.
-- ============================================================================

create table if not exists public.virginiabasementwaterproofing_dashboard (
  id           bigint generated always as identity primary key,
  created_at   timestamptz  not null default now(),
  event_type   text         not null,
  path         text,
  referrer     text,
  session_id   text,
  visitor_id   text,
  listing_slug text,
  listing_name text,
  city         text,
  query        text
);

-- ---- allowed event types ---------------------------------------------------
-- The first six are the shared vocabulary across all of your directory
-- dashboards, kept identical so the sites stay comparable.
--
-- Two are intentionally never emitted by THIS site and will always read zero:
--   call_click       - this site publishes no phone numbers anywhere; every
--                      conversion path is the lead form by design.
--   directions_click - this site has no map/directions links on listings.
--
-- quote_click and claim_click are this site's actual conversion actions and
-- are additive to the shared vocabulary.
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'virginiabasementwaterproofing_dashboard_event_type_check'
  ) then
    alter table public.virginiabasementwaterproofing_dashboard
      add constraint virginiabasementwaterproofing_dashboard_event_type_check
      check (event_type in (
        'pageview',
        'listing_view',
        'call_click',
        'directions_click',
        'search',
        'review_click',
        'quote_click',
        'claim_click'
      ));
  end if;
end $$;

-- ---- indexes ---------------------------------------------------------------
create index if not exists vbw_dashboard_created_at_idx
  on public.virginiabasementwaterproofing_dashboard (created_at desc);
create index if not exists vbw_dashboard_event_type_idx
  on public.virginiabasementwaterproofing_dashboard (event_type);
create index if not exists vbw_dashboard_listing_slug_idx
  on public.virginiabasementwaterproofing_dashboard (listing_slug);
create index if not exists vbw_dashboard_path_idx
  on public.virginiabasementwaterproofing_dashboard (path);
create index if not exists vbw_dashboard_session_id_idx
  on public.virginiabasementwaterproofing_dashboard (session_id);

-- ---- row level security ----------------------------------------------------
alter table public.virginiabasementwaterproofing_dashboard enable row level security;

-- Public read. Required for the /dashboard/ page (no login) to query totals and
-- to hold a Realtime postgres_changes subscription from the browser.
do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename  = 'virginiabasementwaterproofing_dashboard'
      and policyname = 'vbw_dashboard_public_select'
  ) then
    create policy vbw_dashboard_public_select
      on public.virginiabasementwaterproofing_dashboard
      for select using (true);
  end if;
end $$;

-- NOTE: there is deliberately NO public INSERT policy. Writes go through the
-- serverless function at /api/analytics/track, which authenticates with the
-- service-role key and bypasses RLS. See api/analytics/track.js.
--
-- If you would rather skip the serverless function and let the browser write
-- directly with the publishable key (the same pattern js/supabase-forms.js uses
-- for leads), uncomment the policy below and set ANALYTICS_DIRECT_INSERT = true
-- in js/analytics-client.js. Doing so lets anyone insert arbitrary rows into
-- your analytics, which is why it is not the default.
--
-- do $$
-- begin
--   if not exists (
--     select 1 from pg_policies
--     where schemaname = 'public'
--       and tablename  = 'virginiabasementwaterproofing_dashboard'
--       and policyname = 'vbw_dashboard_public_insert'
--   ) then
--     create policy vbw_dashboard_public_insert
--       on public.virginiabasementwaterproofing_dashboard
--       for insert with check (true);
--   end if;
-- end $$;

-- ---- realtime --------------------------------------------------------------
-- Add to the supabase_realtime publication so the dashboard's live panel
-- receives inserts. Guarded so re-running is a no-op.
do $$
begin
  if not exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    create publication supabase_realtime;
  end if;

  if not exists (
    select 1 from pg_publication_tables
    where pubname    = 'supabase_realtime'
      and schemaname = 'public'
      and tablename  = 'virginiabasementwaterproofing_dashboard'
  ) then
    alter publication supabase_realtime
      add table public.virginiabasementwaterproofing_dashboard;
  end if;
end $$;

-- Realtime delivers the full new row to subscribers rather than just the id.
alter table public.virginiabasementwaterproofing_dashboard replica identity full;

-- ============================================================================
-- Leads Received counter
--
-- The `leads` table holds real contact details and must NOT become publicly
-- readable. This SECURITY DEFINER function exposes exactly one integer -- the
-- number of leads this site received in the last N days -- and nothing else.
-- It also filters to this site's source value, so it never leaks the volume of
-- your other properties sharing the same table.
--
-- If your leads table is named something other than `leads`, change it here to
-- match js/supabase-forms.js.
-- ============================================================================
create or replace function public.vbw_dashboard_lead_count(days integer default 30)
returns integer
language sql
security definer
set search_path = public
stable
as $$
  select count(*)::int
  from public.leads
  where source = 'virginiabasementwaterproofing.org'
    and created_at >= now() - (greatest(days, 1) || ' days')::interval;
$$;

revoke all on function public.vbw_dashboard_lead_count(integer) from public;
grant execute on function public.vbw_dashboard_lead_count(integer) to anon, authenticated;

-- If your `leads` table uses a different timestamp column than created_at, the
-- function above will error. Check with:
--   select column_name from information_schema.columns
--   where table_name = 'leads' and data_type like 'timestamp%';
