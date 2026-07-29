#!/usr/bin/env python3
"""Generate programmatic "[zip code] [service]" pages at /[zip]/[service-slug]/.

Same layout as the city/region pages: interactive Leaflet map with a dot at each
contractor location, contractor listing cards, and the standard CTA band.

  H1:    [zip] [service]
  Title: [zip] [service] professionals | Instant Free Quote

Reuses the data layer and shared HTML helpers from gen_cities.py by exec-ing the
portion of that script that runs before its own generation loop.
"""
import os, json
from collections import defaultdict, Counter

ROOT = "/home/user/virginiabasementwaterproofing.com"

# ── reuse gen_cities.py data + helpers (everything before the generation loop) ──
with open(os.path.join(ROOT, "scripts", "gen_cities.py")) as f:
    _src = f.read()
_prefix = _src.split("\n# ── generate city pages", 1)[0]
ns = {}
exec(compile(_prefix, "gen_cities_prefix", "exec"), ns)

g               = ns["g"]
items           = ns["items"]
esc             = ns["esc"]
page_head       = ns["page_head"]
map_embed       = ns["map_embed"]
markers_for     = ns["markers_for"]
contractor_cards= ns["contractor_cards"]
cta_band        = ns["cta_band"]
FOOTER          = ns["FOOTER"]
PHONE_TEL       = ns["PHONE_TEL"]
PHONE_DISP      = ns["PHONE_DISP"]

# ── 12 services (slug + display name), matching the rest of the site ───────────
SERVICES = [
    ("basement-waterproofing",            "Basement Waterproofing"),
    ("crawl-space-encapsulation",         "Crawl Space Encapsulation"),
    ("foundation-repair",                 "Foundation Repair"),
    ("sump-pump-installation",            "Sump Pump Installation"),
    ("french-drain-installation",         "French Drain Installation"),
    ("basement-crack-repair",             "Basement Crack Repair"),
    ("basement-water-damage-restoration", "Basement Water Damage Restoration"),
    ("basement-remodeling",               "Basement Remodeling"),
    ("black-mold-treatment",              "Black Mold Treatment"),
    ("emergency-water-clean-up",          "Emergency Water Clean Up"),
    ("mobile-home-vapor-barrier",         "Mobile Home Vapor Barrier"),
    ("thermal-dry-floor-installation",    "Thermal Dry Floor Installation"),
]

# ── group contractors by 5-digit VA postal code ───────────────────────────────
by_zip = defaultdict(list)
zip_city = {}
for slug, r in items:
    pc = (g(r, "postal_code") or "").strip()[:5]
    if not (pc.isdigit() and len(pc) == 5):
        continue
    by_zip[pc].append((slug, r))

# dominant city name per zip (for copy)
for pc, lst in by_zip.items():
    cities = [(g(r, "city") or "").strip() for _, r in lst if (g(r, "city") or "").strip()]
    zip_city[pc] = Counter(cities).most_common(1)[0][0] if cities else ""

# ── provider cat index per zip for zero-result guard ─────────────────────────
import json as _json, math as _math
_providers = _json.load(open(os.path.join(ROOT, "data/va-providers.json")))
_centroids  = _json.load(open(os.path.join(ROOT, "data/va-zip-centroids.json")))

def _zip_has_cat(pc, cat_key):
    """Return True if any provider within 20 km of pc has cat_key."""
    ctr = _centroids.get(pc)
    for p in _providers:
        if cat_key not in (p.get("cats") or []):
            continue
        if p.get("zip","")[:5] == pc:
            return True
        if ctr:
            try:
                x = (p["lat"] - ctr[0]) * 111
                y = (p["lng"] - ctr[1]) * 85
                if _math.sqrt(x*x + y*y) <= 20:
                    return True
            except (KeyError, TypeError):
                pass
    return False

CAT_KEY_MAP = {
    "basement-waterproofing": "waterproofing",
    "crawl-space-encapsulation": "crawl-space",
    "foundation-repair": "foundation",
    "sump-pump-installation": "plumbing",
    "french-drain-installation": "drainage",
    "basement-crack-repair": "foundation",
    "basement-water-damage-restoration": "water-damage",
    "basement-remodeling": "general",
    "black-mold-treatment": "mold",
    "emergency-water-clean-up": "water-damage",
    "mobile-home-vapor-barrier": "crawl-space",
    "thermal-dry-floor-installation": "waterproofing",
}

# ── generate pages ────────────────────────────────────────────────────────────
generated = []
skipped = 0
for pc in sorted(by_zip):
    contractors = by_zip[pc]
    n_co  = len(contractors)
    city  = zip_city.get(pc, "")
    place = f"{city}, VA" if city else "Virginia"
    mk    = markers_for(contractors)

    for svc_slug, svc_name in SERVICES:
        cat_key = CAT_KEY_MAP.get(svc_slug, "")
        if cat_key and not _zip_has_cat(pc, cat_key):
            skipped += 1
            continue
        url       = f"/{pc}/{svc_slug}/"
        canonical = f"https://www.virginiabasementwaterproofing.org{url}"
        h1        = f"{pc} {svc_name}"
        title     = f"{esc(h1)} professionals | Instant Free Quote"
        desc      = (f"Find licensed {svc_name.lower()} professionals serving ZIP code {pc}"
                     f"{(' (' + esc(city) + ', VA)') if city else ''}. "
                     f"Compare ratings, view profiles, and submit a job request.")

        schema = json.dumps({
            "@context": "https://schema.org", "@type": "Service",
            "name": f"{svc_name} in {pc}",
            "serviceType": svc_name,
            "areaServed": {"@type": "PostalAddress",
                           "postalCode": pc, "addressRegion": "VA",
                           "addressLocality": city, "addressCountry": "US"},
            "url": canonical,
        })

        cat_key = CAT_KEY_MAP.get(svc_slug, "")
        map_cfg = '{' + f'zip:{json.dumps(pc)}' + (f',cat:{json.dumps(cat_key)}' if cat_key else '') + '}'

        page = page_head(title=title, description=desc, canonical=canonical, schema_json=schema, map_config_js=map_cfg)
        page += f'''
<section class="map-hero">
  <div class="map-hero__bar">
    <div class="container">
      <nav class="breadcrumb"><a href="/">Home</a> / <a href="/virginia/">Virginia</a> / <a href="/services/{svc_slug}/">{esc(svc_name)}</a> / {pc}</nav>
      <h1>{pc} {esc(svc_name)}</h1>
      <p>Find vetted, licensed {esc(svc_name.lower())} professionals serving the {pc} area{(" of " + esc(place)) if city else ""}. Submit a free job request and we&rsquo;ll match you with the right contractor.</p>
    </div>
  </div>
  <div class="map-hero__app">
    <aside class="map-panel">
      <div class="map-panel__controls">
        <form class="map-search" id="zipSearch" role="search">
          <input type="text" id="zipInput" inputmode="numeric" maxlength="5" placeholder="Search a ZIP code&hellip;" aria-label="Search by ZIP code">
          <button type="submit" aria-label="Search">&#128269;</button>
        </form>
        <div class="map-filter">
          <select id="svcFilter" aria-label="Filter by service">
            <option value="">All Services</option>
          </select>
        </div>
        <div class="map-toggles">
          <button type="button" class="map-toggle" data-layer="city"><span class="dot"></span> City borders</button>
          <button type="button" class="map-toggle" data-layer="zip"><span class="dot"></span> ZIP borders</button>
        </div>
      </div>
      <div class="map-panel__meta" id="resultCount">Loading providers&hellip;</div>
      <ul class="map-results" id="resultsList"></ul>
      <div class="map-detail" id="mapDetail">
        <button class="map-detail__back" id="mapDetailBack">&#8592; Back to results</button>
        <div id="mapDetailBody"></div>
      </div>
    </aside>
    <div class="map-canvas-wrap">
      <div id="vaMap" class="map-canvas"></div>
      <div class="map-loading" id="mapLoading">Loading map&hellip;</div>
    </div>
  </div>
</section>

<main>
<section class="section">
  <div class="container">
    <div style="margin-top:12px;">
      <h2>{esc(svc_name)} Professionals in {pc}</h2>
      <p class="lead" style="margin-bottom:28px;">Showing {n_co} contractor{"s" if n_co != 1 else ""} serving ZIP code {pc}{(" in " + esc(place)) if city else ""}.</p>
      {contractor_cards(contractors, pc)}
    </div>
    {cta_band(pc)}
  </div>
</section>
</main>
'''
        page += FOOTER

        out_dir = os.path.join(ROOT, pc, svc_slug)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w") as fh:
            fh.write(page)
        generated.append(url)

print(f"Generated {len(generated)} zip+service pages across {len(by_zip)} zip codes, skipped {skipped} zero-result combos")

with open(os.path.join(ROOT, "scripts", "zip_service_urls.json"), "w") as fh:
    json.dump(generated, fh, indent=2)
print("Wrote zip_service_urls.json")
