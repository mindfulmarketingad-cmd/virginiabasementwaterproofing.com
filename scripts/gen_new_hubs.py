#!/usr/bin/env python3
"""Generate service hub pages at /services/[slug]/ for the 3 new services,
mirroring the structure of the existing black-mold-treatment hub."""
import os, re, html as html_mod
from collections import OrderedDict

# reuse city/region data + services from the money-page generator module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "gmp", os.path.join(os.path.dirname(__file__), "gen_money_pages.py"))

ROOT = "/home/user/virginiabasementwaterproofing.com"
PHONE_TEL  = "+17577439050"
PHONE_DISP = "(757) 743-9050"

def esc(x): return html_mod.escape(str(x), quote=True) if x is not None else ''
def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return re.sub(r'-+', '-', s) or 'x'

# city -> (region_slug, region_label), grouped in region display order
CITY_REGION = __import__("importlib").import_module
# load CITY_REGION + SERVICES by exec of the source (avoid running its generation)
src = open(os.path.join(ROOT, "scripts", "gen_money_pages.py")).read()
# cut the module at the "# ── generate" marker so importing constants is cheap-ish
ns = {}
# We need CITY_REGION and SERVICES; exec only the safe top portion up to "# ── shared components"
head = src.split("# ── shared components")[0]
# head still references zipfile parsing of the xlsx; strip that block
head = head.split("# ── city → region map")[1]
head = "CITY_REGION = {" + head.split("CITY_REGION = {",1)[1]
# head now contains CITY_REGION ... SERVICES ... helpers (slugify/esc/REGION_FALLBACK/REASONS)
exec(head, ns)
CITY_REGION = ns["CITY_REGION"]
SERVICES = {s["slug"]: s for s in ns["SERVICES"]}

REGION_ORDER = ["hampton-roads","northern-virginia","richmond",
                "shenandoah-valley","western-virginia","central-virginia"]
REGION_LABEL = {
    "hampton-roads":"Hampton Roads","northern-virginia":"Northern Virginia",
    "richmond":"Greater Richmond","shenandoah-valley":"Shenandoah Valley",
    "western-virginia":"Western Virginia","central-virginia":"Central Virginia",
}

SITE_HEADER = f'''<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <span class="brand__mark"><span class="bm-v">V</span><span class="bm-bw">BW</span></span>
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
      <div class="header-phone">
        <small>Call For a Free Quote</small>
        <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a>
      </div>
      <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false" aria-controls="main-nav">&#9776;</button>
    </div>
  </div>
</header>'''

BANNER = f'''<div class="service-banner" id="dealer-card" aria-live="polite">
  <div class="container">
    <div class="service-banner__inner">
      <div class="service-banner__left">
        <p class="service-banner__tagline">A dry, healthy home starts here.</p>
        <p class="service-banner__sub">Contact your <a href="/partners/">local contractor</a> or call <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></p>
      </div>
      <div class="service-banner__right">
        <div class="service-banner__zip" id="dealer-zip"></div>
        <div class="service-banner__dealer">Your Local Contractor is <strong><span id="dealer-name">Detecting location&hellip;</span></strong></div>
        <a href="#" class="service-banner__change" id="dealer-change">&#9679; Change Location</a>
      </div>
    </div>
  </div>
</div>'''

FOOTER = f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <h4>Virginia Basement Waterproofing</h4>
        <p>A statewide directory connecting Virginia homeowners with licensed, insured, and vetted basement waterproofing contractors.</p>
        <a class="footer-phone" href="tel:{PHONE_TEL}">{PHONE_DISP}</a>
      </div>
      <div><h4>Explore</h4><ul><li><a href="/find/">Find</a></li><li><a href="/virginia/">Cities</a></li><li><a href="/partners/">Contractors</a></li><li><a href="/get-a-quote/">Free Estimate</a></li><li><a href="/blog/">Blog</a></li></ul></div>
      <div><h4>Services</h4><ul><li><a href="/find/waterproofing-va/">Basement Waterproofing</a></li><li><a href="/find/crawl-space-encapsulation-va/">Crawl Space Encapsulation</a></li><li><a href="/find/foundation-repair-va/">Foundation Repair</a></li><li><a href="/find/sump-pump-installation-va/">Sump Pump Installation</a></li><li><a href="/find/french-drain-installation-va/">French Drain Installation</a></li><li><a href="/find/basement-crack-repair-va/">Basement Crack Repair</a></li><li><a href="/find/basement-water-damage-restoration-va/">Water Damage Restoration</a></li><li><a href="/find/basement-remodeling-va/">Basement Remodeling</a></li><li><a href="/find/black-mold-treatment-va/">Black Mold Treatment</a></li><li><a href="/find/emergency-water-clean-up-va/">Emergency Water Clean Up</a></li><li><a href="/find/mobile-home-vapor-barrier-va/">Mobile Home Vapor Barrier</a></li><li><a href="/find/thermal-dry-floor-installation-va/">Thermal Dry Floor Installation</a></li></ul></div>
      <div><h4>Company</h4><ul><li><a href="/about/">About Us</a></li><li><a href="/get-a-quote/">Contact</a></li><li><a href="/dashboard/">Site Analytics</a></li><li><a href="/sitemap.xml">Sitemap</a></li></ul></div>
      <div><h4>Legal</h4><ul><li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/terms-of-service/">Terms of Service</a></li><li><a href="/disclaimer/">Disclaimer</a></li></ul></div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year>2026</span> VirginiaBasementWaterproofing.org &mdash; All rights reserved.</span>
      <span>Call us: <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></span>
    </div>
    <p class="disclaimer-note">VirginiaBasementWaterproofing.org is a free directory and lead-referral service. We are not a licensed contractor and do not perform waterproofing work ourselves. Listed companies are independent businesses; we make no warranty regarding any contractor's work. Always verify licensing and insurance before hiring.</p>
  </div>
</footer>
<script src="/js/main.js"></script>
</body>
</html>'''

# long-form hub intro paragraph per new service
HUB_INTRO = {
    "emergency-water-clean-up":
        "When a pipe bursts, a sump pump fails, or a storm pushes water into your basement, every hour counts. "
        "Standing water saturates drywall, warps flooring, ruins stored belongings, and gives mold the 24-to-48-hour "
        "window it needs to take hold. Emergency water clean up is the fast, first-response phase of recovery: a crew "
        "is dispatched around the clock to extract standing water, dry the structure with industrial equipment, sanitize "
        "contaminated surfaces, and remove materials that cannot be saved. Acting quickly is what separates a "
        "manageable cleanup from a costly full reconstruction — and the licensed Virginia contractors in our network "
        "respond 24/7 across the state.",
    "mobile-home-vapor-barrier":
        "Mobile and manufactured homes sit close to the ground over a crawl area that is especially vulnerable to "
        "moisture. Without an intact vapor barrier and belly wrap, ground moisture rises freely into the floor system, "
        "soaking insulation, rotting subfloor, feeding mold, and inviting pests. The result is soft floors, musty odors, "
        "higher energy bills, and cold drafts in winter. A proper mobile home vapor barrier seals the underbelly from "
        "ground moisture, repairs or replaces torn belly wrap, restores fallen insulation, and manages skirting and "
        "ventilation so the space beneath your home stays dry and protected. Our network connects Virginia "
        "manufactured-home owners with licensed contractors who specialize in under-home moisture control.",
    "thermal-dry-floor-installation":
        "A bare concrete basement slab is cold, and it is never truly dry — moisture vapor passes right through "
        "concrete, which is why carpet and padding laid directly on a slab so often end up damp, musty, and moldy. "
        "Thermal dry floor installation solves this with an insulated, dimpled subfloor panel system that creates an "
        "air gap and a built-in vapor barrier between the slab and your finished floor. The result is a basement floor "
        "that is warmer underfoot, energy efficient, and protected from slab moisture and efflorescence. Because the "
        "panels are made of inorganic materials, they will not feed mold or rot the way wood subfloors do below grade — "
        "and they install directly over concrete, ready to accept carpet, laminate, luxury vinyl plank, or engineered "
        "flooring. Connect with a licensed Virginia contractor through our directory to get started.",
}

def city_chip_blocks(sslug):
    # group cities by region in REGION_ORDER, alphabetical within region
    by_region = OrderedDict((r, []) for r in REGION_ORDER)
    for city, (rslug, rlabel) in CITY_REGION.items():
        by_region.setdefault(rslug, []).append(city)
    blocks = []
    for rslug in REGION_ORDER:
        cities = sorted(by_region.get(rslug, []))
        if not cities: continue
        chips = ' '.join(
            f'<a href="/{slugify(c)}/{sslug}/" class="city-chip">{esc(c)}</a>' for c in cities)
        blocks.append(
            f'<div style="margin-bottom:24px;"><h3 style="font-size:1rem;color:var(--navy);'
            f'margin-bottom:10px;">{esc(REGION_LABEL[rslug])}</h3>'
            f'<div class="city-chip-row">{chips}</div></div>')
    return '\n'.join(blocks)

def build_hub(sslug):
    svc = SERVICES[sslug]
    name = svc["name"]
    canonical = f"https://www.virginiabasementwaterproofing.org/services/{sslug}/"
    title = f"{name} in Virginia | Licensed Local Contractors"
    desc = (f"{name} across Virginia. {svc['blurb']} Free estimates. Call {PHONE_DISP}.")
    off_html = ''.join(
        f'<div class="offering"><h3>{esc(o)}</h3><p>{esc(d)}</p></div>'
        for o, d in svc["offerings"])
    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<link rel="stylesheet" href="/css/styles.css">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
</head>
<body>
{SITE_HEADER}
{BANNER}
<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / <a href="/find/">Find</a> / {esc(name)}</div>
    <h1>{esc(name)} in Virginia</h1>
    <p>Licensed local contractors serving homeowners across Virginia. Free estimates, no obligation.</p>
    <div style="margin-top:18px;display:flex;gap:12px;flex-wrap:wrap;">
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Call or Text for Quote</a>
      <a href="tel:{PHONE_TEL}" class="btn btn--ghost btn--lg">Call {PHONE_DISP}</a>
    </div>
  </div>
</div>
<main>
<section class="section">
  <div class="container">
    <p class="lead">{esc(HUB_INTRO[sslug])}</p>

    <h2>{esc(name)} Services We Provide:</h2>
    <div class="offerings-grid">{off_html}</div>

    <h2>Find {esc(name)} Contractors by City</h2>
    <p>Select your city below to see licensed {esc(svc["short"])} contractors in your area, ZIP codes served, and a direct job request form.</p>
    {city_chip_blocks(sslug)}

    <div class="cta-band" style="margin-top:48px;">
      <h2>Instant Free Quote</h2>
      <p>Once you submit a job request, we'll connect you with the ideal licensed contractor for your situation. They'll reach out within 1&ndash;3 business days.</p>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <a href="/get-a-quote/" class="btn btn--primary btn--lg">Call or Text for Quote</a>
        <a href="tel:{PHONE_TEL}" class="btn btn--ghost btn--lg">Call {PHONE_DISP}</a>
      </div>
    </div>
  </div>
</section>
</main>
{FOOTER}'''
    out_dir = os.path.join(ROOT, "services", sslug)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(page)
    return out_dir

for s in ["emergency-water-clean-up","mobile-home-vapor-barrier","thermal-dry-floor-installation"]:
    print("wrote", build_hub(s))
