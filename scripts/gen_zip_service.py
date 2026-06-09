#!/usr/bin/env python3
"""Generate programmatic "[zip code] [service]" pages at /[zip]/[service-slug]/.

Same layout as the city/region pages: interactive Leaflet map with a dot at each
contractor location, contractor listing cards, and the standard CTA band.

  H1:    [zip] [service]
  Title: [zip] [service] professionals | Submit a Job Request

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

# ── generate pages ────────────────────────────────────────────────────────────
generated = []
for pc in sorted(by_zip):
    contractors = by_zip[pc]
    n_co  = len(contractors)
    city  = zip_city.get(pc, "")
    place = f"{city}, VA" if city else "Virginia"
    mk    = markers_for(contractors)

    for svc_slug, svc_name in SERVICES:
        url       = f"/{pc}/{svc_slug}/"
        canonical = f"https://www.virginiabasementwaterproofing.org{url}"
        h1        = f"{pc} {svc_name}"
        title     = f"{esc(h1)} professionals | Submit a Job Request"
        desc      = (f"Find licensed {svc_name.lower()} professionals serving ZIP code {pc}"
                     f"{(' (' + esc(city) + ', VA)') if city else ''}. "
                     f"Compare ratings, view profiles, and submit a job request.")

        schema = json.dumps({
            "@context": "https://schema.org", "@type": "Service",
            "name": f"{svc_name} in {pc}",
            "serviceType": svc_name,
            "areaServed": {"@type": "PostalCodeArea" if False else "PostalAddress",
                           "postalCode": pc, "addressRegion": "VA",
                           "addressLocality": city, "addressCountry": "US"},
            "telephone": PHONE_TEL, "url": canonical,
        })

        page = page_head(title=title, description=desc, canonical=canonical, schema_json=schema)
        page += f'''
<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / <a href="/virginia/">Virginia</a> / <a href="/services/{svc_slug}/">{esc(svc_name)}</a> / {pc}</div>
    <h1>{pc} {esc(svc_name)}</h1>
    <p>Connect with vetted, licensed {esc(svc_name.lower())} professionals serving the {pc} area{(" of " + esc(place)) if city else ""}. Free estimates, no obligation &mdash; submit a job request and we'll match you with the right contractor.</p>
  </div>
</div>

<main>
<section class="section">
  <div class="container">
    {map_embed(pc, mk)}

    <div style="margin-top:40px;">
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

print(f"Generated {len(generated)} zip+service pages across {len(by_zip)} zip codes")

with open(os.path.join(ROOT, "scripts", "zip_service_urls.json"), "w") as fh:
    json.dump(generated, fh, indent=2)
print("Wrote zip_service_urls.json")
