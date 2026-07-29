-- ============================================================================
-- Adds the columns virginiabasementwaterproofing.org needs to your existing
-- cross-site `leads` table.
--
-- Every statement is additive and guarded with IF NOT EXISTS, so this is safe
-- to run against a table that already holds leads from your other sites, and
-- safe to run more than once. It does not drop, rename, or alter any existing
-- column, and it does not touch existing rows.
--
-- HOW TO RUN: Supabase dashboard -> SQL Editor -> paste -> Run.
-- If your table is not named "leads", change it here AND set LEADS_TABLE in
-- js/supabase-forms.js to match.
-- ============================================================================

-- ---- routing / segmentation ------------------------------------------------
alter table public.leads add column if not exists source        text;  -- 'virginiabasementwaterproofing.org'
alter table public.leads add column if not exists lead_type     text;  -- 'job_request' | 'claim_listing'

-- ---- contact ---------------------------------------------------------------
alter table public.leads add column if not exists name          text;
alter table public.leads add column if not exists email         text;
alter table public.leads add column if not exists phone         text;
alter table public.leads add column if not exists message       text;

-- ---- job details -----------------------------------------------------------
alter table public.leads add column if not exists city          text;
alter table public.leads add column if not exists state         text;
alter table public.leads add column if not exists zip           text;
alter table public.leads add column if not exists service       text;

-- ---- directory linkage -----------------------------------------------------
alter table public.leads add column if not exists provider_slug text;  -- which listing the lead came from
alter table public.leads add column if not exists business_name text;  -- claim-listing submissions

-- ---- attribution -----------------------------------------------------------
alter table public.leads add column if not exists page_url      text;
alter table public.leads add column if not exists referrer      text;
alter table public.leads add column if not exists utm_source    text;
alter table public.leads add column if not exists utm_medium    text;
alter table public.leads add column if not exists utm_campaign  text;
alter table public.leads add column if not exists utm_term      text;
alter table public.leads add column if not exists utm_content   text;
alter table public.leads add column if not exists gclid         text;

-- ---- timestamp (only if your table doesn't already have one) ---------------
alter table public.leads add column if not exists created_at    timestamptz default now();

-- ---- helpful indexes -------------------------------------------------------
create index if not exists leads_source_idx        on public.leads (source);
create index if not exists leads_lead_type_idx     on public.leads (lead_type);
create index if not exists leads_provider_slug_idx on public.leads (provider_slug);
create index if not exists leads_created_at_idx    on public.leads (created_at desc);

-- ============================================================================
-- RLS: allow anonymous INSERT only (the site uses the publishable/anon key).
-- Nobody can read leads with that key — reads stay restricted to your
-- service-role key and dashboard.
--
-- Skip this block if your other sites already have an equivalent insert policy.
-- ============================================================================
alter table public.leads enable row level security;

drop policy if exists "anon can insert leads" on public.leads;
create policy "anon can insert leads"
  on public.leads
  for insert
  to anon
  with check (true);

-- Deliberately NO select/update/delete policy for anon:
-- the publishable key can write leads but can never read them back.
