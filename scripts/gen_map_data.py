#!/usr/bin/env python3
"""Build the static, pre-fetched provider dataset for the homepage map.

Source: the Outscraper (Google Maps) export already on the site — so the data
"lives on the site" with ZERO live API cost. Phone/website/email are intentionally
omitted (leads route to our number); popups link to the partner profile page.

Outputs:
  data/va-providers.json   – array of {name, slug, city, zip, county, lat, lng,
                             rating, reviews, cats[]}
  data/va-zip-centroids.json – {zip: [lat, lng]} for the ZIP search box
  data/map-categories.json – ordered list of {key, label} filter options
"""
import zipfile, re, json, os, html
import xml.etree.ElementTree as ET

ROOT = "/home/user/virginiabasementwaterproofing.com"
SRC  = "/root/.claude/uploads/d3aa2d35-0d52-4e41-a880-55c8b6248f0b/e4b92662-Outscraper20260604222103s2f_waterproofing_service.xlsx"
ZCTA = "/tmp/va_test.json"   # full VA ZCTA geojson (downloaded), used only for centroids

# ── parse xlsx (same approach as the other generators) ─────────────────────────
ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
z  = zipfile.ZipFile(SRC)
ss = ["".join(t.text or "" for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'))
      for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', ns)]
ws   = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
rows = ws.findall('.//m:sheetData/m:row', ns)

def colnum(ref):
    s = re.match(r'([A-Z]+)', ref).group(1); n = 0
    for ch in s: n = n*26 + (ord(ch)-64)
    return n-1

def rowvals(r):
    cells = {}
    for c in r.findall('m:c', ns):
        ref = c.get('r'); t = c.get('t'); v = c.find('m:v', ns)
        if v is not None:
            cells[colnum(ref)] = ss[int(v.text)] if t == 's' else v.text
    return cells

data = [rowvals(r) for r in rows]
hdr  = data[0]; maxc = max(hdr.keys())
H    = {hdr[i]: i for i in range(maxc+1) if hdr.get(i)}
def g(row, col):
    i = H.get(col); return row.get(i) if i is not None else None

# ── slug logic (MUST match gen_partners.py so /partners/<slug>/ links resolve) ──
slugs = {}
def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')
    return re.sub(r'-+', '-', s) or 'x'
def uniq_slug(name, city):
    base = slugify(name); s = base
    if s in slugs: s = slugify(name + '-' + (city or ''))
    i = 2
    while s in slugs: s = base + '-' + str(i); i += 1
    slugs[s] = True; return s

# ── service category mapping (curated filter options) ──────────────────────────
# canonical key -> (label, [substrings matched against raw subtypes, lowercased])
CATEGORIES = [
    ("waterproofing",  "Basement Waterproofing",      ["waterproofing"]),
    ("water-damage",   "Water Damage Restoration",    ["water damage restoration"]),
    ("drainage",       "Drainage & French Drains",    ["drainage"]),
    ("foundation",     "Foundation Repair",           ["foundation"]),
    ("crawl-space",    "Crawl Space & Insulation",    ["insulation", "crawl"]),
    ("mold",           "Mold & Air Quality",          ["mold", "air duct", "indoor air"]),
    ("concrete",       "Concrete & Masonry",          ["concrete", "masonry"]),
    ("restoration",    "Fire & Building Restoration",  ["fire damage", "building restoration", "restoration service"]),
    ("plumbing",       "Plumbing & Sump Pumps",       ["plumber", "pump"]),
    ("general",        "General Contractor",          ["general contractor", "construction", "remodel", "contractor"]),
]

def cats_for(subtypes_raw):
    s = (subtypes_raw or "").lower()
    out = []
    for key, _label, needles in CATEGORIES:
        if any(n in s for n in needles):
            out.append(key)
    return out

# ── filter + dedupe (mirror gen_partners.py exactly) ───────────────────────────
seen = set()
providers = []
cat_counts = {k: 0 for k, _, _ in CATEGORIES}

for r in data[1:]:
    name = (g(r, 'name') or '').strip()
    if not name: continue
    if g(r, 'state_code') != 'VA': continue
    if (g(r, 'business_status') or 'OPERATIONAL') != 'OPERATIONAL': continue
    key = g(r, 'place_id') or (name.lower() + '|' + (g(r, 'address') or '').lower())
    if key in seen: continue
    seen.add(key)

    city = (g(r, 'city') or '').strip()
    slug = uniq_slug(name, city)

    try:
        lat = round(float(g(r, 'latitude')), 6); lng = round(float(g(r, 'longitude')), 6)
    except (TypeError, ValueError):
        continue

    zip5 = (g(r, 'postal_code') or '').strip()[:5]
    try:    rating = round(float(g(r, 'rating')), 1)
    except: rating = None
    try:    reviews = int(float(g(r, 'reviews')))
    except: reviews = None

    cats = cats_for(g(r, 'subtypes'))
    for c in cats: cat_counts[c] += 1

    providers.append({
        "name": name,
        "slug": slug,
        "city": city,
        "zip": zip5 if (zip5.isdigit() and len(zip5) == 5) else "",
        "county": (g(r, 'county') or '').strip(),
        "lat": lat, "lng": lng,
        "rating": rating, "reviews": reviews,
        "cats": cats,
    })

os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
with open(os.path.join(ROOT, "data", "va-providers.json"), "w") as f:
    json.dump(providers, f, separators=(",", ":"))
print(f"Wrote va-providers.json — {len(providers)} providers")

# categories that actually have providers, in defined order
cat_out = [{"key": k, "label": lbl, "count": cat_counts[k]}
           for k, lbl, _ in CATEGORIES if cat_counts[k] > 0]
with open(os.path.join(ROOT, "data", "map-categories.json"), "w") as f:
    json.dump(cat_out, f, indent=2)
print("Wrote map-categories.json —", ", ".join(f'{c["label"]}({c["count"]})' for c in cat_out))

# ── ZIP centroids for the search box (from ZCTA INTPTLAT/LON props) ─────────────
centroids = {}
if os.path.exists(ZCTA):
    gj = json.load(open(ZCTA))
    for feat in gj.get("features", []):
        p = feat.get("properties", {})
        z5 = p.get("ZCTA5CE10") or p.get("ZCTA5CE20")
        la = p.get("INTPTLAT10") or p.get("INTPTLAT20")
        lo = p.get("INTPTLON10") or p.get("INTPTLON20")
        if z5 and la and lo:
            try:
                centroids[z5] = [round(float(la), 5), round(float(lo), 5)]
            except ValueError:
                pass
with open(os.path.join(ROOT, "data", "va-zip-centroids.json"), "w") as f:
    json.dump(centroids, f, separators=(",", ":"))
print(f"Wrote va-zip-centroids.json — {len(centroids)} ZIP centroids")
