#!/usr/bin/env python3
"""Insert a ZIP-code chip section into each /services/[slug]/index.html,
just before the existing CTA band. Idempotent — re-running replaces the
section rather than duplicating it."""

import os, json, re

ROOT = "/home/user/virginiabasementwaterproofing.com"

# ── data ──────────────────────────────────────────────────────────────────────
zip_city = json.load(open(os.path.join(ROOT, "scripts", "zip_city_map.json")))

urls = json.load(open(os.path.join(ROOT, "scripts", "zip_service_urls.json")))
# group zip codes per service slug
from collections import defaultdict
svc_zips = defaultdict(list)
for url in urls:
    parts = url.strip("/").split("/")  # [zip, service-slug]
    if len(parts) == 2:
        svc_zips[parts[1]].append(parts[0])

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

SECTION_START = "<!-- zip-links-start -->"
SECTION_END   = "<!-- zip-links-end -->"

updated = 0
for slug, name in SERVICES:
    path = os.path.join(ROOT, "services", slug, "index.html")
    if not os.path.exists(path):
        print(f"  SKIP (not found): {path}")
        continue

    zips = sorted(svc_zips.get(slug, []))
    if not zips:
        print(f"  SKIP (no zips): {slug}")
        continue

    # build chip HTML: "23320 (Chesapeake)" — label shows zip + city
    chips = []
    for pc in zips:
        city = zip_city.get(pc, "")
        label = f"{pc} ({city})" if city else pc
        chips.append(f'<a href="/{pc}/{slug}/" class="city-chip">{label}</a>')

    section = (
        f"\n{SECTION_START}\n"
        f'    <h2>Find {name} Contractors by ZIP Code</h2>\n'
        f'    <p class="text-muted" style="margin-bottom:16px;">Select your ZIP code to see licensed {name.lower()} contractors in your area with ratings, reviews, and profiles.</p>\n'
        f'    <div class="city-chip-row">\n'
        f'      ' + "\n      ".join(chips) + "\n"
        f"    </div>\n"
        f"    {SECTION_END}\n\n"
        f"    "
    )

    html = open(path).read()

    # remove existing section if present (idempotent)
    html = re.sub(
        r"\n" + re.escape(SECTION_START) + r".*?" + re.escape(SECTION_END) + r"\n",
        "",
        html,
        flags=re.DOTALL,
    )

    # insert just before the cta-band div
    anchor = '<div class="cta-band"'
    if anchor not in html:
        print(f"  WARN (no cta-band): {slug}")
        continue

    html = html.replace(anchor, section + anchor, 1)
    open(path, "w").write(html)
    updated += 1
    print(f"  Updated {slug} — {len(zips)} ZIP chips")

print(f"\nDone: updated {updated} service pages")
