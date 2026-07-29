#!/usr/bin/env python3
"""Generate city pages (/virginia/[region]/[city]/) and region pages (/virginia/[region]/)
with service banner, embedded map, and contractor listing cards.
"""
import os, re, html as html_mod, json, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from urllib.parse import quote

ROOT = "/home/user/virginiabasementwaterproofing.com"
SRC  = "/root/.claude/uploads/d3aa2d35-0d52-4e41-a880-55c8b6248f0b/e4b92662-Outscraper20260604222103s2f_waterproofing_service.xlsx"
PHONE_TEL  = "+17577439050"
PHONE_DISP = "(757) 743-9050"
GOOGLE_MAPS_KEY = "AIzaSyD1IVMZyzQic5lLyZR9bQuARP9n4kJtLbg"

# ── parse xlsx ───────────────────────────────────────────────────────────────
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

# ── filter + dedupe contractors ───────────────────────────────────────────────
seen = set(); recs = []
for r in data[1:]:
    name = (g(r,'name') or '').strip()
    if not name: continue
    if g(r,'state_code') != 'VA': continue
    if (g(r,'business_status') or 'OPERATIONAL') != 'OPERATIONAL': continue
    key = g(r,'place_id') or (name.lower()+'|'+(g(r,'address') or '').lower())
    if key in seen: continue
    seen.add(key); recs.append(r)

# ── slug map (must match gen_partners.py slugs exactly) ──────────────────────
slugs = {}
def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return re.sub(r'-+', '-', s) or 'x'
def uniq_slug(name, city):
    base = slugify(name); s = base
    if s in slugs: s = slugify(name + '-' + (city or ''))
    i = 2
    while s in slugs: s = base + '-' + str(i); i += 1
    slugs[s] = True; return s

def esc(x): return html_mod.escape(str(x), quote=True) if x is not None else ''

def fmt_rating(raw):
    try: return f"{float(raw):.1f}"
    except: return ''

def stars(rating):
    try: r = float(rating)
    except: return ''
    full = max(0, min(5, int(round(r))))
    return '★'*full + '☆'*(5-full)

def services_list(raw):
    if not raw: return []
    seen2 = set(); out = []
    for p in re.split(r',', raw):
        p = p.strip()
        if p and p.lower() not in seen2: seen2.add(p.lower()); out.append(p)
    return out

# build slug list matching gen_partners.py ordering
items = []
for r in recs:
    name = (g(r,'name') or '').strip()
    city = (g(r,'city') or '').strip()
    slug = uniq_slug(name, city)
    items.append((slug, r))

# group by city
by_city = defaultdict(list)
for slug, r in items:
    city = (g(r,'city') or '').strip()
    if city: by_city[city].append((slug, r))

# ── city → region mapping ─────────────────────────────────────────────────────
CITY_REGION = {
    "Virginia Beach":("hampton-roads","Hampton Roads"),
    "Norfolk":("hampton-roads","Hampton Roads"),
    "Chesapeake":("hampton-roads","Hampton Roads"),
    "Suffolk":("hampton-roads","Hampton Roads"),
    "Portsmouth":("hampton-roads","Hampton Roads"),
    "Newport News":("hampton-roads","Hampton Roads"),
    "Hampton":("hampton-roads","Hampton Roads"),
    "Williamsburg":("hampton-roads","Hampton Roads"),
    "Yorktown":("hampton-roads","Hampton Roads"),
    "Smithfield":("hampton-roads","Hampton Roads"),
    "Franklin":("hampton-roads","Hampton Roads"),
    "Hopewell":("hampton-roads","Hampton Roads"),
    "Fort Monroe":("hampton-roads","Hampton Roads"),
    "Grafton":("hampton-roads","Hampton Roads"),
    "Toano":("hampton-roads","Hampton Roads"),
    "Hartfield":("hampton-roads","Hampton Roads"),
    "Heathsville":("hampton-roads","Hampton Roads"),
    "Topping":("hampton-roads","Hampton Roads"),
    "Eastville":("hampton-roads","Hampton Roads"),
    "Alexandria":("northern-virginia","Northern Virginia"),
    "Arlington":("northern-virginia","Northern Virginia"),
    "Fairfax":("northern-virginia","Northern Virginia"),
    "Falls Church":("northern-virginia","Northern Virginia"),
    "McLean":("northern-virginia","Northern Virginia"),
    "Reston":("northern-virginia","Northern Virginia"),
    "Herndon":("northern-virginia","Northern Virginia"),
    "Vienna":("northern-virginia","Northern Virginia"),
    "Sterling":("northern-virginia","Northern Virginia"),
    "Leesburg":("northern-virginia","Northern Virginia"),
    "Ashburn":("northern-virginia","Northern Virginia"),
    "Centreville":("northern-virginia","Northern Virginia"),
    "Chantilly":("northern-virginia","Northern Virginia"),
    "Manassas":("northern-virginia","Northern Virginia"),
    "Manassas Park":("northern-virginia","Northern Virginia"),
    "Gainesville":("northern-virginia","Northern Virginia"),
    "Woodbridge":("northern-virginia","Northern Virginia"),
    "Springfield":("northern-virginia","Northern Virginia"),
    "Lorton":("northern-virginia","Northern Virginia"),
    "Dumfries":("northern-virginia","Northern Virginia"),
    "South Riding":("northern-virginia","Northern Virginia"),
    "Purcellville":("northern-virginia","Northern Virginia"),
    "Hamilton":("northern-virginia","Northern Virginia"),
    "Waterford":("northern-virginia","Northern Virginia"),
    "Lovettsville":("northern-virginia","Northern Virginia"),
    "Warrenton":("northern-virginia","Northern Virginia"),
    "Bristow":("northern-virginia","Northern Virginia"),
    "Broad Run":("northern-virginia","Northern Virginia"),
    "Paris":("northern-virginia","Northern Virginia"),
    "Marshall":("northern-virginia","Northern Virginia"),
    "Midland":("northern-virginia","Northern Virginia"),
    "Remington":("northern-virginia","Northern Virginia"),
    "Amissville":("northern-virginia","Northern Virginia"),
    "Goldvein":("northern-virginia","Northern Virginia"),
    "Richmond":("richmond","Greater Richmond"),
    "Henrico":("richmond","Greater Richmond"),
    "Midlothian":("richmond","Greater Richmond"),
    "Glen Allen":("richmond","Greater Richmond"),
    "Mechanicsville":("richmond","Greater Richmond"),
    "Chester":("richmond","Greater Richmond"),
    "North Chesterfield":("richmond","Greater Richmond"),
    "South Chesterfield":("richmond","Greater Richmond"),
    "Ashland":("richmond","Greater Richmond"),
    "Powhatan":("richmond","Greater Richmond"),
    "Dinwiddie":("richmond","Greater Richmond"),
    "Prince George":("richmond","Greater Richmond"),
    "Montpelier":("richmond","Greater Richmond"),
    "Rockville":("richmond","Greater Richmond"),
    "Charles City":("richmond","Greater Richmond"),
    "Manquin":("richmond","Greater Richmond"),
    "Troy":("richmond","Greater Richmond"),
    "Winchester":("shenandoah-valley","Shenandoah Valley"),
    "Harrisonburg":("shenandoah-valley","Shenandoah Valley"),
    "Staunton":("shenandoah-valley","Shenandoah Valley"),
    "Waynesboro":("shenandoah-valley","Shenandoah Valley"),
    "Front Royal":("shenandoah-valley","Shenandoah Valley"),
    "New Market":("shenandoah-valley","Shenandoah Valley"),
    "Mt Sidney":("shenandoah-valley","Shenandoah Valley"),
    "Dayton":("shenandoah-valley","Shenandoah Valley"),
    "Churchville":("shenandoah-valley","Shenandoah Valley"),
    "Linden":("shenandoah-valley","Shenandoah Valley"),
    "Roanoke":("western-virginia","Western Virginia"),
    "Lynchburg":("western-virginia","Western Virginia"),
    "Blacksburg":("western-virginia","Western Virginia"),
    "Christiansburg":("western-virginia","Western Virginia"),
    "Salem":("western-virginia","Western Virginia"),
    "Vinton":("western-virginia","Western Virginia"),
    "Bedford":("western-virginia","Western Virginia"),
    "Amherst":("western-virginia","Western Virginia"),
    "Troutville":("western-virginia","Western Virginia"),
    "Cave Spring":("western-virginia","Western Virginia"),
    "Moneta":("western-virginia","Western Virginia"),
    "Wirtz":("western-virginia","Western Virginia"),
    "Hardy":("western-virginia","Western Virginia"),
    "Gladstone":("western-virginia","Western Virginia"),
    "Evington":("western-virginia","Western Virginia"),
    "Rustburg":("western-virginia","Western Virginia"),
    "Hollins":("western-virginia","Western Virginia"),
    "Forest":("western-virginia","Western Virginia"),
    "Max Meadows":("western-virginia","Western Virginia"),
    "Glade Spring":("western-virginia","Western Virginia"),
    "Wytheville":("western-virginia","Western Virginia"),
    "Bristol":("western-virginia","Western Virginia"),
    "Richlands":("western-virginia","Western Virginia"),
    "Clintwood":("western-virginia","Western Virginia"),
    "Coeburn":("western-virginia","Western Virginia"),
    "Charlottesville":("central-virginia","Central Virginia"),
    "Fredericksburg":("central-virginia","Central Virginia"),
    "Stafford":("central-virginia","Central Virginia"),
    "Orange":("central-virginia","Central Virginia"),
    "Madison":("central-virginia","Central Virginia"),
    "Culpeper":("central-virginia","Central Virginia"),
    "King George":("central-virginia","Central Virginia"),
    "Spotsylvania Courthouse":("central-virginia","Central Virginia"),
    "Farmville":("central-virginia","Central Virginia"),
    "Kenbridge":("central-virginia","Central Virginia"),
    "Keysville":("central-virginia","Central Virginia"),
    "South Hill":("central-virginia","Central Virginia"),
    "Clarksville":("central-virginia","Central Virginia"),
    "Halifax":("central-virginia","Central Virginia"),
    "Ruckersville":("central-virginia","Central Virginia"),
    "Danville":("central-virginia","Central Virginia"),
    "Martinsville":("central-virginia","Central Virginia"),
    "Collinsville":("central-virginia","Central Virginia"),
    "Lancaster":("central-virginia","Central Virginia"),
    "Gloucester":("central-virginia","Central Virginia"),
}

REGION_INTROS = {
    "hampton-roads": "Hampton Roads sits at sea level where rivers meet the Chesapeake Bay and the Atlantic. High water tables, tidal flooding, and coastal storms make basement and crawl space moisture one of the most common home challenges in the region. Clay and sandy soils hold moisture against foundations year-round.",
    "northern-virginia": "Northern Virginia's dense development, older housing stock, and the heavy clay soils of the Piedmont create persistent basement moisture challenges. Spring runoff from the Blue Ridge foothills adds significant hydrostatic pressure during wet seasons.",
    "richmond": "The Greater Richmond area sits on a transition zone between the Piedmont clay uplands and the coastal plain. Wet winters and heavy spring rains saturate soils quickly, and homes in low-lying neighborhoods near the James River face regular flooding risk.",
    "shenandoah-valley": "The Shenandoah Valley's limestone geology creates unique drainage patterns. Combined with significant annual snowmelt from the Blue Ridge and Allegheny ridges, valley homes often experience basement seepage and crawl space moisture during the spring thaw.",
    "western-virginia": "Western Virginia's mountainous terrain brings heavy snowfall, spring runoff, and steep-slope drainage that puts significant hydrostatic pressure on foundation walls. Freeze-thaw cycles can accelerate foundation cracking in this region.",
    "central-virginia": "Central Virginia's rolling Piedmont terrain and red clay soils create challenging drainage conditions. Water moves slowly through clay-heavy soil, creating hydrostatic pressure that persists long after rainfall.",
}

# ── shared HTML components ────────────────────────────────────────────────────
SERVICE_BANNER = ''  # removed — no phone CTAs on site

SITE_HEADER = '''<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <img class="brand__logo" src="/img/vbw-logo.svg" alt="VBW — Virginia Basement Waterproofing" width="62" height="26">
      <span class="brand__name">Virginia Basement Waterproofing<span>Statewide Contractor Directory</span></span>
    </a>
    <nav class="main-nav" id="main-nav" aria-label="Primary">
      <a href="/">Home</a>
      <a href="/find/">Find</a>
      <a href="/reviews/">Reviews</a>
      <a href="/partners/">Partners</a>
      <a href="/blog/">Blog</a>
      <a href="/about/">About</a>
    </nav>
    <div class="header-right">
      <a href="/get-a-quote/" class="btn btn--primary header-cta">Instant Free Quote</a>
      <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false" aria-controls="main-nav">&#9776;</button>
    </div>
  </div>
</header>'''

FOOTER = '''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <h4>Virginia Basement Waterproofing</h4>
        <p>A statewide directory connecting Virginia homeowners with licensed, insured, and vetted basement waterproofing contractors.</p>
        <a class="btn btn--primary" href="/get-a-quote/">Instant Free Quote</a>
      </div>
      <div><h4>Explore</h4><ul><li><a href="/find/">Find</a></li><li><a href="/virginia/">Cities</a></li><li><a href="/get-a-quote/">Free Estimate</a></li><li><a href="/blog/">Blog</a></li></ul></div>
      <div><h4>Services</h4><ul><li><a href="/find/waterproofing-va/">Basement Waterproofing</a></li><li><a href="/find/crawl-space-encapsulation-va/">Crawl Space Encapsulation</a></li><li><a href="/find/foundation-repair-va/">Foundation Repair</a></li><li><a href="/find/sump-pump-installation-va/">Sump Pump Installation</a></li><li><a href="/find/french-drain-installation-va/">French Drain Installation</a></li><li><a href="/find/basement-crack-repair-va/">Basement Crack Repair</a></li><li><a href="/find/basement-water-damage-restoration-va/">Water Damage Restoration</a></li><li><a href="/find/basement-remodeling-va/">Basement Remodeling</a></li><li><a href="/find/black-mold-treatment-va/">Black Mold Treatment</a></li><li><a href="/find/emergency-water-clean-up-va/">Emergency Water Clean Up</a></li><li><a href="/find/mobile-home-vapor-barrier-va/">Mobile Home Vapor Barrier</a></li><li><a href="/find/thermal-dry-floor-installation-va/">Thermal Dry Floor Installation</a></li></ul></div>
      <div><h4>Company</h4><ul><li><a href="/about/">About Us</a></li><li><a href="/get-a-quote/">Contact</a></li><li><a href="/sitemap.xml">Sitemap</a></li></ul></div>
      <div><h4>Legal</h4><ul><li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/terms-of-service/">Terms of Service</a></li><li><a href="/disclaimer/">Disclaimer</a></li></ul></div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year>2026</span> VirginiaBasementWaterproofing.org &mdash; All rights reserved.</span>
      <span><a href="/get-a-quote/">Free Estimate &rarr;</a></span>
    </div>
    <p class="disclaimer-note">VirginiaBasementWaterproofing.org is a free directory and lead-referral service. We are not a licensed contractor and do not perform waterproofing work ourselves. Listed companies are independent businesses; we make no warranty regarding any contractor\'s work. Always verify licensing and insurance before hiring.</p>
  </div>
</footer>
<script src="/js/main.js"></script>
</body>
</html>'''

def page_head(title, description, canonical, schema_json='', map_config_js='{}'):
    gm_scripts = f'''<script>window.MAP_CONFIG = {map_config_js};</script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script src="/js/map-local.js" defer></script>'''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<link rel="stylesheet" href="/css/styles.css">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
{gm_scripts}
{('<script type="application/ld+json">' + schema_json + '</script>') if schema_json else ''}
</head>
<body>
{SITE_HEADER}'''

def markers_for(contractor_list):
    """Build a list of {name, lat, lng} from contractors that have valid coordinates."""
    out = []
    for slug, r in contractor_list:
        try:
            lat = float(g(r, 'latitude')); lng = float(g(r, 'longitude'))
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        out.append({'name': (g(r, 'name') or '').strip(), 'lat': lat, 'lng': lng})
    return out

_map_counter = [0]

def map_embed(query, markers=None):
    """Kept for backward-compat (imported by gen_zip_service.py). Returns empty string
    — the map is now the full-page map-hero section, not an inline embed."""
    return ''

def contractor_cards(contractor_list, label=''):
    if not contractor_list:
        return f'<p class="text-muted">No contractors currently listed in {label}. <a href="/virginia/">Browse other Virginia areas</a> or <a href="/get-a-quote/">submit a job request</a> to be matched with a local pro.</p>'
    cards = []
    for slug, r in contractor_list:
        name    = (g(r,'name') or '').strip()
        city    = (g(r,'city') or '').strip()
        rating  = g(r,'rating')
        reviews = g(r,'reviews')
        svcs    = services_list(g(r,'subtypes'))[:3]
        st      = stars(rating)
        rf      = fmt_rating(rating)
        rline   = ''
        if st:
            rc    = f'<span class="review-count">({esc(reviews)})</span>' if reviews else ''
            rline = f'<div class="rating-line"><span class="stars">{st}</span> <span class="rating-num">{rf}</span> {rc}</div>'
        svc_tags = ''
        if svcs:
            svc_tags = '<div class="listing__services">' + ''.join(
                f'<span class="svc-tag">{esc(s)}</span>' for s in svcs) + '</div>'
        cards.append(f'''<div class="listing">
          <h3>{esc(name)}</h3>
          <div class="meta">{esc(city)}, VA</div>
          {rline}
          {svc_tags}
          <div class="listing__foot"><a href="/partners/{slug}/" class="btn btn--blue btn--block">View Profile</a></div>
        </div>''')
    return '<div class="listing-grid">' + ''.join(cards) + '</div>'

def cta_band(city_label):
    return f'''<div class="cta-band" style="margin-top:48px;">
  <h2>Instant Free Quote</h2>
  <p>Once you submit a job request, we\'ll connect you with the ideal licensed contractor for your situation. They\'ll reach out within 1–3 business days.</p>
  <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
    <a href="/get-a-quote/" class="btn btn--primary btn--lg">Instant Free Quote</a>
    <a href="/virginia/" class="btn btn--ghost btn--lg">Browse Service Areas</a>
  </div>
</div>'''

# ── generate city pages ───────────────────────────────────────────────────────
city_url_map = {}
city_count   = 0

for city, (region_slug, region_label) in CITY_REGION.items():
    city_slug = slugify(city)
    city_url  = f"/virginia/{region_slug}/{city_slug}/"
    city_url_map[city] = city_url
    canonical = f"https://www.virginiabasementwaterproofing.org{city_url}"

    contractors = by_city.get(city, [])
    n_co        = len(contractors)
    co_note     = f"{n_co} contractor{'s' if n_co != 1 else ''} listed" if n_co else "Statewide network available"

    schema = json.dumps({
        "@context":"https://schema.org","@type":"Service",
        "name": f"Basement Waterproofing in {city}, VA",
        "areaServed":{"@type":"City","name":city,"addressRegion":"VA"},
        "url": canonical
    })

    map_cfg = '{' + f'city:{json.dumps(city)}' + '}'

    page  = page_head(
        title         = f"Basement Waterproofing in {esc(city)}, VA | Local Contractors",
        description   = f"Find licensed basement waterproofing contractors in {esc(city)}, Virginia. Compare ratings, view profiles, and submit a free job request. {co_note}.",
        canonical     = canonical,
        schema_json   = schema,
        map_config_js = map_cfg,
    )
    breadcrumb = f'<nav class="breadcrumb"><a href="/">Home</a> / <a href="/virginia/">Virginia</a> / <a href="/virginia/{region_slug}/">{esc(region_label)}</a> / {esc(city)}</nav>'
    page += f'''
<section class="map-hero">
  <div class="map-hero__bar">
    <div class="container">
      {breadcrumb}
      <h1>Basement Waterproofing in {esc(city)}, VA</h1>
      <p>Find vetted, licensed waterproofing contractors serving {esc(city)} and surrounding {esc(region_label)} communities. Browse the map, filter by service, and submit a free job request.</p>
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
      <h2>Waterproofing Contractors in {esc(city)}</h2>
      <p class="lead" style="margin-bottom:28px;">{"Showing " + str(n_co) + " contractor" + ("s" if n_co!=1 else "") + " serving " + esc(city) + "." if n_co else "Our statewide network covers " + esc(city) + " &mdash; submit a job request to be matched with a local pro."}</p>
      {contractor_cards(contractors, city)}
    </div>
    {cta_band(city)}
  </div>
</section>
</main>
'''
    page += FOOTER

    out_dir = os.path.join(ROOT, 'virginia', region_slug, city_slug)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.html'), 'w') as f:
        f.write(page)
    city_count += 1

print(f"Generated {city_count} city pages")

# ── generate region pages ─────────────────────────────────────────────────────
# group contractors by region
by_region = defaultdict(list)
for city, (region_slug, _) in CITY_REGION.items():
    for item in by_city.get(city, []):
        by_region[region_slug].append(item)

REGIONS = [
    ("hampton-roads",    "Hampton Roads",    "Hampton Roads, Virginia"),
    ("northern-virginia","Northern Virginia","Northern Virginia"),
    ("richmond",         "Greater Richmond", "Greater Richmond, Virginia"),
    ("shenandoah-valley","Shenandoah Valley","Shenandoah Valley, Virginia"),
    ("western-virginia", "Western Virginia", "Western Virginia"),
    ("central-virginia", "Central Virginia", "Central Virginia"),
    ("central-western-valley", "Central, Western & Valley Virginia", "Central Virginia"),
]

# combined "super-regions" aggregate several base regions onto a single page
COMBINED_REGIONS = {
    "central-western-valley": ["central-virginia", "western-virginia", "shenandoah-valley"],
}

region_count = 0
for region_slug, region_label, map_query in REGIONS:
    canonical    = f"https://www.virginiabasementwaterproofing.org/virginia/{region_slug}/"
    source_slugs = COMBINED_REGIONS.get(region_slug, [region_slug])
    contractors  = [item for ss in source_slugs for item in by_region.get(ss, [])]
    n_co         = len(contractors)
    intro        = REGION_INTROS.get(region_slug, '')

    # city links for this region (each links to its own base-region path)
    region_cities = [(c, CITY_REGION[c][0], slugify(c))
                     for c, (rs, _) in CITY_REGION.items() if rs in source_slugs]
    city_links_html = ' '.join(
        f'<a href="/virginia/{rs}/{cs}/" class="city-chip">{esc(c)}</a>'
        for c, rs, cs in sorted(region_cities)
    )

    schema = json.dumps({
        "@context":"https://schema.org","@type":"Service",
        "name": f"Basement Waterproofing in {region_label}, VA",
        "areaServed":{"@type":"State","name":"Virginia"},
        "url": canonical
    })

    region_city_names = [c for c, (rs, _) in CITY_REGION.items() if rs in source_slugs]
    map_cfg = '{cities:' + json.dumps(region_city_names) + '}'

    page = page_head(
        title         = f"Basement Waterproofing Contractors in {esc(region_label)}, VA",
        description   = f"Browse licensed basement waterproofing contractors serving {esc(region_label)}, Virginia. Compare ratings, view profiles, and submit a free job request.",
        canonical     = canonical,
        schema_json   = schema,
        map_config_js = map_cfg,
    )
    page += f'''
<section class="map-hero">
  <div class="map-hero__bar">
    <div class="container">
      <nav class="breadcrumb"><a href="/">Home</a> / <a href="/virginia/">Virginia</a> / {esc(region_label)}</nav>
      <h1>Basement Waterproofing in {esc(region_label)}, VA</h1>
      <p>Find vetted, licensed waterproofing contractors across {esc(region_label)}. Browse the map, filter by service, or view all {n_co} contractors below.</p>
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
      <h2>Cities in {esc(region_label)}</h2>
      <div class="city-chip-row" style="margin-top:12px; margin-bottom:32px;">
        {city_links_html}
      </div>
    </div>

    <div>
      <h2>All Contractors in {esc(region_label)}</h2>
      <p class="lead" style="margin-bottom:28px;">Showing {n_co} contractor{"s" if n_co!=1 else ""} across the {esc(region_label)} area.</p>
      {'<p class="text-muted">' + esc(intro) + '</p>' if intro else ''}
      <div style="margin-top:20px;">
        {contractor_cards(contractors, region_label)}
      </div>
    </div>
    {cta_band(region_label)}
  </div>
</section>
</main>
'''
    page += FOOTER

    out_dir = os.path.join(ROOT, 'virginia', region_slug)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.html'), 'w') as f:
        f.write(page)
    region_count += 1

print(f"Generated {region_count} region pages")

# ── write city URL map ────────────────────────────────────────────────────────
with open(os.path.join(ROOT, 'scripts', 'city_urls.json'), 'w') as f:
    json.dump(city_url_map, f, indent=2)
print("Wrote city_urls.json")
