"""Shared HTML components for all generator scripts.
No phone numbers anywhere. 'Instant Free Quote' is the only CTA.
Primary nav: Home | Find | Reviews | Partners | About.
"""

import os

GOOGLE_MAPS_KEY = "AIzaSyD1IVMZyzQic5lLyZR9bQuARP9n4kJtLbg"

# The 12 services, keyed by the legacy /services/<slug>/ directory name.
#   find : URL fragment used by the /find/ searchmap pages
#          statewide -> /find/<find>-va/      city -> /find/<find>-<city>-va/
#   cat  : matching map-category key in data/va-providers.json (preselects the
#          service filter on the searchmap)
SERVICES = [
    # slug,                                find,                             label,                           cat
    ("basement-waterproofing",             "waterproofing",                  "Basement Waterproofing",        "waterproofing"),
    ("crawl-space-encapsulation",          "crawl-space-encapsulation",      "Crawl Space Encapsulation",     "crawl-space"),
    ("foundation-repair",                  "foundation-repair",              "Foundation Repair",             "foundation"),
    ("sump-pump-installation",             "sump-pump-installation",         "Sump Pump Installation",        "plumbing"),
    ("french-drain-installation",          "french-drain-installation",      "French Drain Installation",     "drainage"),
    ("basement-crack-repair",              "basement-crack-repair",          "Basement Crack Repair",         "foundation"),
    ("basement-water-damage-restoration",  "basement-water-damage-restoration", "Water Damage Restoration",   "water-damage"),
    ("emergency-water-clean-up",           "emergency-water-clean-up",       "Emergency Water Clean Up",      "water-damage"),
    ("basement-remodeling",                "basement-remodeling",            "Basement Remodeling",           "general"),
    ("black-mold-treatment",               "black-mold-treatment",           "Black Mold Treatment",          "mold"),
    ("mobile-home-vapor-barrier",          "mobile-home-vapor-barrier",      "Mobile Home Vapor Barrier",     "crawl-space"),
    ("thermal-dry-floor-installation",     "thermal-dry-floor-installation", "Thermal Dry Floor Installation", "waterproofing"),
    # New /find/-only services (no legacy /services/ or /<city>/<slug>/ page ever
    # existed, so gen_find.py falls back to covering every city in city_urls.json).
    ("basement-finishing",                 "basement-finishing",              "Basement Finishing",           "general"),
    ("mold-removal",                       "mold-removal",                    "Mold Removal",                  "mold"),
    ("mold-remediation",                   "mold-remediation",                "Mold Remediation",              "mold"),
]

SERVICE_BY_SLUG = {s[0]: {"slug": s[0], "find": s[1], "label": s[2], "cat": s[3]} for s in SERVICES}

# Preference order for "link to this city in general" (not tied to one service).
# basement-finishing / mold-removal / mold-remediation cover every named city
# (gen_find.py falls back to full coverage for /find/-only services), so this
# chain always resolves to a real page -- there is no need for a final fallback
# to the /find/ hub.
_FIND_CITY_PREFERENCE = [s[1] for s in SERVICES]


def best_city_find_url(root, city_slug, preferred=None):
    """Best available /find/<service>-<city_slug>-va/ page for a city, used
    wherever a page used to link to the retired /virginia/<region>/<city>/ page.
    """
    order = ([preferred] if preferred else []) + _FIND_CITY_PREFERENCE
    seen = set()
    for find in order:
        if not find or find in seen:
            continue
        seen.add(find)
        if os.path.isdir(os.path.join(root, "find", f"{find}-{city_slug}-va")):
            return f"/find/{find}-{city_slug}-va/"
    return "/find/"

# Primary navigation. Keep in sync with scripts/batch_patch_nav.py, which
# rewrites the same block across every already-generated page.
MAIN_NAV = '''<nav class="main-nav" id="main-nav" aria-label="Primary">
      <a href="/">Home</a>
      <a href="/find/">Find</a>
      <a href="/reviews/">Reviews</a>
      <a href="/partners/">Partners</a>
      <a href="/blog/">Blog</a>
      <a href="/about/">About</a>
    </nav>'''

SITE_HEADER = f'''<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <img class="brand__logo" src="/img/vbw-logo.svg" alt="VBW &mdash; Virginia Basement Waterproofing" width="62" height="26">
      <span class="brand__name">Virginia Basement Waterproofing<span>Statewide Contractor Directory</span></span>
    </a>
    {MAIN_NAV}
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
      <div><h4>Explore</h4><ul><li><a href="/find/">Find a Pro</a></li><li><a href="/reviews/">Reviews</a></li><li><a href="/partners/">Partners</a></li><li><a href="/virginia/">Cities</a></li><li><a href="/get-a-quote/">Free Estimate</a></li><li><a href="/blog/">Blog</a></li></ul></div>
      <div><h4>Services</h4><ul><li><a href="/find/waterproofing-va/">Basement Waterproofing</a></li><li><a href="/find/crawl-space-encapsulation-va/">Crawl Space Encapsulation</a></li><li><a href="/find/foundation-repair-va/">Foundation Repair</a></li><li><a href="/find/sump-pump-installation-va/">Sump Pump Installation</a></li><li><a href="/find/french-drain-installation-va/">French Drain Installation</a></li><li><a href="/find/basement-crack-repair-va/">Basement Crack Repair</a></li><li><a href="/find/basement-water-damage-restoration-va/">Water Damage Restoration</a></li><li><a href="/find/basement-remodeling-va/">Basement Remodeling</a></li><li><a href="/find/basement-finishing-va/">Basement Finishing</a></li><li><a href="/find/black-mold-treatment-va/">Black Mold Treatment</a></li><li><a href="/find/mold-removal-va/">Mold Removal</a></li><li><a href="/find/mold-remediation-va/">Mold Remediation</a></li><li><a href="/find/emergency-water-clean-up-va/">Emergency Water Clean Up</a></li><li><a href="/find/mobile-home-vapor-barrier-va/">Mobile Home Vapor Barrier</a></li><li><a href="/find/thermal-dry-floor-installation-va/">Thermal Dry Floor Installation</a></li></ul></div>
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


SEARCHMAP_HEAD = '''<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">'''

SEARCHMAP_SCRIPTS = '''<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script src="/js/map-hero.js" defer></script>'''


def searchmap_section(h1, intro_html, breadcrumb_html=""):
    """The exact homepage searchmap (Leaflet + provider list + detail panel).

    map-hero.js reads window.FIND_CONFIG (emitted separately) to preselect a
    service filter and recenter on a city.
    """
    crumb = f"      {breadcrumb_html}\n" if breadcrumb_html else ""
    return f'''<section class="map-hero">
  <div class="map-hero__bar">
    <div class="container">
{crumb}      <h1>{h1}</h1>
      <p>{intro_html}</p>
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
</section>'''


def google_maps_head_scripts(map_config_js):
    """Returns <script> tags for the Leaflet map + MarkerCluster + map-local.js.
    map_config_js: a JS object literal string, e.g. '{city:"Virginia Beach"}'
    (Name kept for backwards compatibility; uses free Leaflet/OSM tiles now.)
    """
    return f'''<script>window.MAP_CONFIG = {map_config_js};</script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script src="/js/map-local.js" defer></script>'''


def map_hero_section(breadcrumb_html, h1_text, description_html, cta_label="Instant Free Quote"):
    """Returns the full .map-hero section HTML for city/region/service pages."""
    return f'''<section class="map-hero">
  <div class="map-hero__bar">
    <div class="container">
      {breadcrumb_html}
      <h1>{h1_text}</h1>
      <p>{description_html}</p>
      <a href="/get-a-quote/" class="btn btn--primary" style="margin-top:14px;">{cta_label}</a>
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
    </aside>
    <div class="map-canvas-wrap">
      <div id="vaMap" class="map-canvas"></div>
      <div class="map-loading" id="mapLoading">Loading map&hellip;</div>
    </div>
  </div>
</section>'''
