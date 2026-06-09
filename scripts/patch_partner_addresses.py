#!/usr/bin/env python3
"""Batch-patch existing partner pages to link city and ZIP in the Address row.

Idempotent — skips pages where links are already present.
"""
import os, re, json, html as html_mod

ROOT = "/home/user/virginiabasementwaterproofing.com"

city_urls = json.load(open(os.path.join(ROOT, "scripts", "city_urls.json")))
zip_urls  = json.load(open(os.path.join(ROOT, "scripts", "zip_service_urls.json")))
zip_set   = set(u.strip("/").split("/")[0] for u in zip_urls)

ADDR_RE = re.compile(
    r'(<li><span class="lbl">Address</span>)(.*?)(</li>)',
    re.DOTALL
)
# Extract city and ZIP from an address string like "Street, City, VA 12345"
CITY_ZIP_RE = re.compile(r',\s*([^,]+),\s*VA\s+(\d{5})\s*$', re.IGNORECASE)

def link_addr(raw_text):
    m = CITY_ZIP_RE.search(html_mod.unescape(raw_text))
    if not m:
        return raw_text  # can't parse — leave unchanged

    city = m.group(1).strip()
    pc   = m.group(2).strip()
    result = raw_text

    # Link ZIP (replace the 5-digit run at the end)
    if pc in zip_set:
        result = re.sub(
            r'\b' + re.escape(pc) + r'\b',
            f'<a href="/{pc}/basement-waterproofing/">{pc}</a>',
            result, count=1
        )

    # Link city (replace first occurrence of the city name in the text)
    city_url = city_urls.get(city)
    if city_url:
        city_esc = html_mod.escape(city, quote=True)
        result = result.replace(
            city_esc,
            f'<a href="{city_url}">{city_esc}</a>',
            1
        )

    return result

updated = skipped = already = 0
partners_dir = os.path.join(ROOT, "partners")

for slug in os.listdir(partners_dir):
    path = os.path.join(partners_dir, slug, "index.html")
    if not os.path.isfile(path):
        continue

    html = open(path).read()
    m = ADDR_RE.search(html)
    if not m:
        skipped += 1
        continue

    prefix, addr_text, suffix = m.group(1), m.group(2), m.group(3)

    # Skip if already linked
    if '<a href=' in addr_text:
        already += 1
        continue

    new_addr = link_addr(addr_text)
    if new_addr == addr_text:
        skipped += 1
        continue

    new_html = html.replace(
        prefix + addr_text + suffix,
        prefix + new_addr + suffix,
        1
    )
    open(path, "w").write(new_html)
    updated += 1

print(f"Updated: {updated}  Already linked: {already}  Skipped (no addr / unparseable): {skipped}")
