#!/usr/bin/env python3
"""Generate city pages at /virginia/[region]/[city-slug]/ for all 125 VA contractor cities."""
import os, re, html as html_mod

ROOT = "/home/user/virginiabasementwaterproofing.com"
PHONE_TEL = "+17577439050"
PHONE_DISP = "(757) 743-9050"

def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return re.sub(r'-+', '-', s) or 'city'

def esc(x):
    return html_mod.escape(str(x), quote=True) if x is not None else ''

# City -> (region_slug, region_label)
CITY_REGION = {
    # Hampton Roads
    "Virginia Beach":           ("hampton-roads", "Hampton Roads"),
    "Norfolk":                  ("hampton-roads", "Hampton Roads"),
    "Chesapeake":               ("hampton-roads", "Hampton Roads"),
    "Suffolk":                  ("hampton-roads", "Hampton Roads"),
    "Portsmouth":               ("hampton-roads", "Hampton Roads"),
    "Newport News":             ("hampton-roads", "Hampton Roads"),
    "Hampton":                  ("hampton-roads", "Hampton Roads"),
    "Williamsburg":             ("hampton-roads", "Hampton Roads"),
    "Yorktown":                 ("hampton-roads", "Hampton Roads"),
    "Smithfield":               ("hampton-roads", "Hampton Roads"),
    "Franklin":                 ("hampton-roads", "Hampton Roads"),
    "Hopewell":                 ("hampton-roads", "Hampton Roads"),
    "Fort Monroe":              ("hampton-roads", "Hampton Roads"),
    "Grafton":                  ("hampton-roads", "Hampton Roads"),
    "Toano":                    ("hampton-roads", "Hampton Roads"),
    "Hartfield":                ("hampton-roads", "Hampton Roads"),
    "Heathsville":              ("hampton-roads", "Hampton Roads"),
    "Topping":                  ("hampton-roads", "Hampton Roads"),
    "Eastville":                ("hampton-roads", "Hampton Roads"),
    # Northern Virginia
    "Alexandria":               ("northern-virginia", "Northern Virginia"),
    "Arlington":                ("northern-virginia", "Northern Virginia"),
    "Fairfax":                  ("northern-virginia", "Northern Virginia"),
    "Falls Church":             ("northern-virginia", "Northern Virginia"),
    "McLean":                   ("northern-virginia", "Northern Virginia"),
    "Reston":                   ("northern-virginia", "Northern Virginia"),
    "Herndon":                  ("northern-virginia", "Northern Virginia"),
    "Vienna":                   ("northern-virginia", "Northern Virginia"),
    "Sterling":                 ("northern-virginia", "Northern Virginia"),
    "Leesburg":                 ("northern-virginia", "Northern Virginia"),
    "Ashburn":                  ("northern-virginia", "Northern Virginia"),
    "Centreville":              ("northern-virginia", "Northern Virginia"),
    "Chantilly":                ("northern-virginia", "Northern Virginia"),
    "Manassas":                 ("northern-virginia", "Northern Virginia"),
    "Manassas Park":            ("northern-virginia", "Northern Virginia"),
    "Gainesville":              ("northern-virginia", "Northern Virginia"),
    "Woodbridge":               ("northern-virginia", "Northern Virginia"),
    "Springfield":              ("northern-virginia", "Northern Virginia"),
    "Lorton":                   ("northern-virginia", "Northern Virginia"),
    "Dumfries":                 ("northern-virginia", "Northern Virginia"),
    "South Riding":             ("northern-virginia", "Northern Virginia"),
    "Purcellville":             ("northern-virginia", "Northern Virginia"),
    "Hamilton":                 ("northern-virginia", "Northern Virginia"),
    "Waterford":                ("northern-virginia", "Northern Virginia"),
    "Lovettsville":             ("northern-virginia", "Northern Virginia"),
    "Warrenton":                ("northern-virginia", "Northern Virginia"),
    "Bristow":                  ("northern-virginia", "Northern Virginia"),
    "Broad Run":                ("northern-virginia", "Northern Virginia"),
    "Paris":                    ("northern-virginia", "Northern Virginia"),
    "Marshall":                 ("northern-virginia", "Northern Virginia"),
    "Midland":                  ("northern-virginia", "Northern Virginia"),
    "Remington":                ("northern-virginia", "Northern Virginia"),
    "Amissville":               ("northern-virginia", "Northern Virginia"),
    "Goldvein":                 ("northern-virginia", "Northern Virginia"),
    # Greater Richmond
    "Richmond":                 ("richmond", "Greater Richmond"),
    "Henrico":                  ("richmond", "Greater Richmond"),
    "Midlothian":               ("richmond", "Greater Richmond"),
    "Glen Allen":               ("richmond", "Greater Richmond"),
    "Mechanicsville":           ("richmond", "Greater Richmond"),
    "Chester":                  ("richmond", "Greater Richmond"),
    "North Chesterfield":       ("richmond", "Greater Richmond"),
    "South Chesterfield":       ("richmond", "Greater Richmond"),
    "Ashland":                  ("richmond", "Greater Richmond"),
    "Powhatan":                 ("richmond", "Greater Richmond"),
    "Dinwiddie":                ("richmond", "Greater Richmond"),
    "Prince George":            ("richmond", "Greater Richmond"),
    "Montpelier":               ("richmond", "Greater Richmond"),
    "Rockville":                ("richmond", "Greater Richmond"),
    "Charles City":             ("richmond", "Greater Richmond"),
    "Manquin":                  ("richmond", "Greater Richmond"),
    "Troy":                     ("richmond", "Greater Richmond"),
    # Shenandoah Valley
    "Winchester":               ("shenandoah-valley", "Shenandoah Valley"),
    "Harrisonburg":             ("shenandoah-valley", "Shenandoah Valley"),
    "Staunton":                 ("shenandoah-valley", "Shenandoah Valley"),
    "Waynesboro":               ("shenandoah-valley", "Shenandoah Valley"),
    "Front Royal":              ("shenandoah-valley", "Shenandoah Valley"),
    "New Market":               ("shenandoah-valley", "Shenandoah Valley"),
    "Mt Sidney":                ("shenandoah-valley", "Shenandoah Valley"),
    "Dayton":                   ("shenandoah-valley", "Shenandoah Valley"),
    "Churchville":              ("shenandoah-valley", "Shenandoah Valley"),
    "Linden":                   ("shenandoah-valley", "Shenandoah Valley"),
    # Western Virginia
    "Roanoke":                  ("western-virginia", "Western Virginia"),
    "Lynchburg":                ("western-virginia", "Western Virginia"),
    "Blacksburg":               ("western-virginia", "Western Virginia"),
    "Christiansburg":           ("western-virginia", "Western Virginia"),
    "Salem":                    ("western-virginia", "Western Virginia"),
    "Vinton":                   ("western-virginia", "Western Virginia"),
    "Bedford":                  ("western-virginia", "Western Virginia"),
    "Amherst":                  ("western-virginia", "Western Virginia"),
    "Troutville":               ("western-virginia", "Western Virginia"),
    "Cave Spring":              ("western-virginia", "Western Virginia"),
    "Moneta":                   ("western-virginia", "Western Virginia"),
    "Wirtz":                    ("western-virginia", "Western Virginia"),
    "Hardy":                    ("western-virginia", "Western Virginia"),
    "Gladstone":                ("western-virginia", "Western Virginia"),
    "Evington":                 ("western-virginia", "Western Virginia"),
    "Rustburg":                 ("western-virginia", "Western Virginia"),
    "Hollins":                  ("western-virginia", "Western Virginia"),
    "Forest":                   ("western-virginia", "Western Virginia"),
    "Max Meadows":              ("western-virginia", "Western Virginia"),
    "Glade Spring":             ("western-virginia", "Western Virginia"),
    "Wytheville":               ("western-virginia", "Western Virginia"),
    "Bristol":                  ("western-virginia", "Western Virginia"),
    "Richlands":                ("western-virginia", "Western Virginia"),
    "Clintwood":                ("western-virginia", "Western Virginia"),
    "Coeburn":                  ("western-virginia", "Western Virginia"),
    # Central / Southern Virginia
    "Charlottesville":          ("central-virginia", "Central Virginia"),
    "Fredericksburg":           ("central-virginia", "Central Virginia"),
    "Stafford":                 ("central-virginia", "Central Virginia"),
    "Orange":                   ("central-virginia", "Central Virginia"),
    "Madison":                  ("central-virginia", "Central Virginia"),
    "Culpeper":                 ("central-virginia", "Central Virginia"),
    "King George":              ("central-virginia", "Central Virginia"),
    "Spotsylvania Courthouse":  ("central-virginia", "Central Virginia"),
    "Farmville":                ("central-virginia", "Central Virginia"),
    "Kenbridge":                ("central-virginia", "Central Virginia"),
    "Keysville":                ("central-virginia", "Central Virginia"),
    "South Hill":               ("central-virginia", "Central Virginia"),
    "Clarksville":              ("central-virginia", "Central Virginia"),
    "Halifax":                  ("central-virginia", "Central Virginia"),
    "Ruckersville":             ("central-virginia", "Central Virginia"),
    "Danville":                 ("central-virginia", "Central Virginia"),
    "Martinsville":             ("central-virginia", "Central Virginia"),
    "Collinsville":             ("central-virginia", "Central Virginia"),
    "Lancaster":                ("central-virginia", "Central Virginia"),
    "Gloucester":               ("central-virginia", "Central Virginia"),
}

REGION_INTROS = {
    "hampton-roads": (
        "Hampton Roads sits at sea level, where rivers meet the Chesapeake Bay and the Atlantic. High water tables, "
        "tidal flooding, and coastal storms make basement and crawl space moisture one of the most common home "
        "challenges in the region. Clay and sandy soils here hold moisture against foundations year-round, and even "
        "minor storms can raise the water table enough to cause seepage in homes that previously stayed dry."
    ),
    "northern-virginia": (
        "Northern Virginia's dense development, older housing stock, and the heavy clay soils of the Piedmont create "
        "persistent basement moisture challenges. Many homes built in the 1960s through 1990s were not waterproofed "
        "to modern standards, and spring runoff from the Blue Ridge foothills adds significant hydrostatic pressure "
        "during wet seasons. Proper drainage and foundation waterproofing are essential investments in this region."
    ),
    "richmond": (
        "The Greater Richmond area sits on a transition zone between the Piedmont clay uplands and the coastal plain. "
        "Wet winters and heavy spring rains saturate soils quickly, and homes in low-lying neighborhoods near the James "
        "River and its tributaries face regular flooding risk. Local contractors are experienced with both older brick "
        "foundation homes in the city and newer construction in the surrounding counties."
    ),
    "shenandoah-valley": (
        "The Shenandoah Valley's limestone geology creates unique drainage patterns, including sinkholes and karst "
        "features that can affect foundation stability. Combined with significant annual snowmelt from the Blue Ridge "
        "and Allegheny ridges, valley homes often experience basement seepage and crawl space moisture during the "
        "spring thaw. Local contractors understand these mountain and valley conditions well."
    ),
    "western-virginia": (
        "Western Virginia's mountainous terrain brings heavy snowfall, spring runoff, and steep-slope drainage that "
        "puts significant hydrostatic pressure on foundation walls. The region's mix of shale, sandstone, and clay "
        "soils retains moisture effectively, and freeze-thaw cycles can accelerate foundation cracking. Waterproofing "
        "contractors in this area are well-versed in the unique challenges of mountain-area homes."
    ),
    "central-virginia": (
        "Central Virginia's rolling Piedmont terrain and red clay soils create challenging drainage conditions for "
        "homeowners. Water moves slowly through clay-heavy soil, creating hydrostatic pressure that persists long "
        "after rainfall. The region also experiences significant weather variation, from heavy summer thunderstorms "
        "to winter ice events, all of which stress basement waterproofing systems."
    ),
}

SITE_HEADER = f'''<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <span class="brand__mark"><span class="bm-v">V</span><span class="bm-bw">BW</span></span>
      <span class="brand__name">Virginia Basement Waterproofing<span>Statewide Contractor Directory</span></span>
    </a>
    <nav class="main-nav" id="main-nav" aria-label="Primary">
      <a href="/services/">Services</a>
      <a href="/virginia/">Cities</a>
      <a href="/partners/">Contractors</a>
      <a href="/get-a-quote/">Free Estimate</a>
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

FOOTER = f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <h4>Virginia Basement Waterproofing</h4>
        <p>A statewide directory connecting Virginia homeowners with licensed, insured, and vetted basement waterproofing contractors.</p>
        <a class="footer-phone" href="tel:{PHONE_TEL}">{PHONE_DISP}</a>
      </div>
      <div><h4>Explore</h4><ul><li><a href="/services/">Services</a></li><li><a href="/virginia/">Cities</a></li><li><a href="/partners/">Contractors</a></li><li><a href="/get-a-quote/">Free Estimate</a></li><li><a href="/blog/">Blog</a></li></ul></div>
      <div><h4>Company</h4><ul><li><a href="/about/">About Us</a></li><li><a href="/get-a-quote/">Contact</a></li><li><a href="/sitemap.xml">Sitemap</a></li></ul></div>
      <div><h4>Legal</h4><ul><li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/terms-of-service/">Terms of Service</a></li><li><a href="/disclaimer/">Disclaimer</a></li></ul></div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year>2026</span> VirginiaBasementWaterproofing.com &mdash; All rights reserved.</span>
      <span>Call us: <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></span>
    </div>
    <p class="disclaimer-note">VirginiaBasementWaterproofing.com is a free directory and lead-referral service. We are not a licensed contractor and do not perform waterproofing work ourselves. Listed companies are independent businesses; we make no warranty regarding any contractor\'s work. Always verify licensing and insurance before hiring.</p>
  </div>
</footer>
<script src="/js/main.js"></script>
</body>
</html>'''

generated = []

for city, (region_slug, region_label) in CITY_REGION.items():
    city_slug = slugify(city)
    city_esc = esc(city)
    region_esc = esc(region_label)
    canonical = f"https://virginiabasementwaterproofing.com/virginia/{region_slug}/{city_slug}/"
    intro = REGION_INTROS.get(region_slug, "Virginia homeowners regularly deal with basement moisture, foundation seepage, and crawl space humidity.")

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Basement Waterproofing in {city_esc}, VA | Local Contractors</title>
<meta name="description" content="Find licensed basement waterproofing contractors in {city_esc}, Virginia. Compare ratings, request free estimates, and protect your home from water damage.">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<link rel="stylesheet" href="/css/styles.css">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Service","name":"Basement Waterproofing in {city_esc}, VA","areaServed":{{"@type":"City","name":"{city_esc}","addressRegion":"VA"}},"telephone":"{PHONE_TEL}","url":"{canonical}"}}</script>
</head>
<body>

{SITE_HEADER}

<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / <a href="/virginia/">Virginia</a> / <a href="/virginia/{region_slug}/">{region_esc}</a> / {city_esc}</div>
    <h1>Basement Waterproofing in {city_esc}, VA</h1>
    <p>Connect with licensed, vetted basement waterproofing contractors serving {city_esc} and the surrounding {region_esc} area. Free estimates, no obligation.</p>
  </div>
</div>

<main>

<section class="dealer-section">
  <div class="container">
    <div class="dealer-card" id="dealer-card" aria-live="polite">
      <div class="dealer-card__zip" id="dealer-zip"></div>
      <div class="dealer-card__label">Your Local Dealer is</div>
      <div class="dealer-card__name" id="dealer-name">Detecting your location&hellip;</div>
      <a href="#" class="dealer-card__change" id="dealer-change"><span aria-hidden="true">&#9679;</span> Change Location</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="container prose">
    <h2>Waterproofing in {city_esc}, Virginia</h2>
    <p>{esc(intro)}</p>
    <p>Homeowners in {city_esc} can experience water intrusion through foundation cracks, hydrostatic pressure at the cove joint, window well seepage, and condensation from seasonal humidity changes. The right solution depends on your home's construction, soil conditions, and the severity of the moisture problem &mdash; which is why a free, on-site inspection by a licensed contractor is always the recommended first step.</p>

    <h3>Common Waterproofing Services in {city_esc}</h3>
    <ul>
      <li>Interior perimeter drain tile systems and sump pump installation</li>
      <li>Exterior foundation waterproofing and membrane application</li>
      <li>Crawl space encapsulation and vapor barrier installation</li>
      <li>Foundation crack repair via epoxy and polyurethane injection</li>
      <li>French drain and yard drainage systems</li>
      <li>Dehumidification and moisture control systems</li>
      <li>Wall anchor and carbon fiber strap installation for bowing walls</li>
    </ul>

    <h3>Why Act Early</h3>
    <p>Basement moisture problems rarely stay the same &mdash; they get worse over time. What begins as a damp wall or musty smell can progress to active leaks, mold growth, wood rot in floor joists and sill plates, and eventually structural compromise. Early waterproofing is almost always less expensive than deferred repairs. Most {city_esc} contractors offer free, no-obligation estimates so you can understand your options before committing.</p>
  </div>

  <div class="container" style="margin-top:40px;">
    <div class="cta-band">
      <h2>Get a Free {city_esc} Waterproofing Quote</h2>
      <p>Tell us about your basement or crawl space and a licensed {city_esc} area contractor will reach out with a free, no-obligation estimate.</p>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <a href="/get-a-quote/" class="btn btn--primary btn--lg">Request a Free Quote</a>
        <a href="/partners/" class="btn btn--ghost btn--lg">Browse All Contractors</a>
      </div>
    </div>
  </div>
</section>

</main>

{FOOTER}'''

    out_dir = os.path.join(ROOT, 'virginia', region_slug, city_slug)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.html'), 'w') as f:
        f.write(page)
    generated.append((city, region_slug, city_slug))

print(f"Generated {len(generated)} city pages")

# Emit city URL map for use by gen_partners.py
city_url_map = {city: f"/virginia/{rs}/{slugify(city)}/" for city, (rs, _) in CITY_REGION.items()}
import json
with open(os.path.join(ROOT, 'scripts', 'city_urls.json'), 'w') as f:
    json.dump(city_url_map, f, indent=2)
print("Wrote scripts/city_urls.json")
