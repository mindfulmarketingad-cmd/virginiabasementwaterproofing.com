"""Shared HTML components for all generator scripts.
No phone numbers anywhere. 'Submit Job Request' is the only CTA.
No emoji icons in the mega menu.
"""

GOOGLE_MAPS_KEY = "AIzaSyD1IVMZyzQic5lLyZR9bQuARP9n4kJtLbg"

MEGA_MENU_GRID = '''<div class="mega-menu__grid">
            <a href="/services/basement-waterproofing/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Basement Waterproofing</strong><span>Interior drains, exterior membranes &amp; sump systems</span></span></a>
            <a href="/services/crawl-space-encapsulation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Crawl Space Encapsulation</strong><span>Vapor barriers, vent sealing &amp; dehumidifiers</span></span></a>
            <a href="/services/foundation-repair/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Foundation Repair</strong><span>Piers, wall anchors &amp; carbon-fiber straps</span></span></a>
            <a href="/services/sump-pump-installation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Sump Pump Installation</strong><span>Primary &amp; battery-backup pumps</span></span></a>
            <a href="/services/french-drain-installation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>French Drain Installation</strong><span>Interior, exterior &amp; curtain drains</span></span></a>
            <a href="/services/basement-crack-repair/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Basement Crack Repair</strong><span>Polyurethane &amp; epoxy injection</span></span></a>
            <a href="/services/basement-water-damage-restoration/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Water Damage Restoration</strong><span>Emergency extraction &amp; structural drying</span></span></a>
            <a href="/services/emergency-water-clean-up/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Emergency Water Clean Up</strong><span>24/7 flooding response &amp; sanitizing</span></span></a>
            <a href="/services/basement-remodeling/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Basement Remodeling</strong><span>Finishing, flooring &amp; egress windows</span></span></a>
            <a href="/services/black-mold-treatment/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Black Mold Treatment</strong><span>Testing, containment &amp; remediation</span></span></a>
            <a href="/services/mobile-home-vapor-barrier/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Mobile Home Vapor Barrier</strong><span>Underbelly sealing &amp; belly-wrap repair</span></span></a>
            <a href="/services/thermal-dry-floor-installation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__text"><strong>Thermal Dry Floor Installation</strong><span>Insulated, moisture-proof subfloor panels</span></span></a>
          </div>'''

SITE_HEADER = f'''<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <span class="brand__mark"><span class="bm-v">V</span><span class="bm-bw">BW</span></span>
      <span class="brand__name">Virginia Basement Waterproofing<span>Statewide Contractor Directory</span></span>
    </a>
    <nav class="main-nav" id="main-nav" aria-label="Primary">
      <div class="nav-item">
        <a href="/services/">Services <span class="nav-arrow"></span></a>
        <div class="mega-menu" role="menu">
          {MEGA_MENU_GRID}
          <div class="mega-menu__footer">
            <span>All 12 waterproofing &amp; foundation services</span>
            <a href="/services/">View All Services &rarr;</a>
          </div>
        </div>
      </div>
      <a href="/virginia/">Cities</a>
      <a href="/partners/">Contractors</a>
      <a href="/get-a-quote/">Free Estimate</a>
    </nav>
    <div class="header-right">
      <a href="/get-a-quote/" class="btn btn--primary header-cta">Submit Job Request</a>
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
        <a class="btn btn--primary" href="/get-a-quote/">Submit Job Request</a>
      </div>
      <div><h4>Explore</h4><ul><li><a href="/services/">Services</a></li><li><a href="/virginia/">Cities</a></li><li><a href="/partners/">Contractors</a></li><li><a href="/get-a-quote/">Free Estimate</a></li><li><a href="/blog/">Blog</a></li></ul></div>
      <div><h4>Services</h4><ul><li><a href="/services/basement-waterproofing/">Basement Waterproofing</a></li><li><a href="/services/crawl-space-encapsulation/">Crawl Space Encapsulation</a></li><li><a href="/services/foundation-repair/">Foundation Repair</a></li><li><a href="/services/sump-pump-installation/">Sump Pump Installation</a></li><li><a href="/services/french-drain-installation/">French Drain Installation</a></li><li><a href="/services/basement-crack-repair/">Basement Crack Repair</a></li><li><a href="/services/basement-water-damage-restoration/">Water Damage Restoration</a></li><li><a href="/services/basement-remodeling/">Basement Remodeling</a></li><li><a href="/services/black-mold-treatment/">Black Mold Treatment</a></li><li><a href="/services/emergency-water-clean-up/">Emergency Water Clean Up</a></li><li><a href="/services/mobile-home-vapor-barrier/">Mobile Home Vapor Barrier</a></li><li><a href="/services/thermal-dry-floor-installation/">Thermal Dry Floor Installation</a></li></ul></div>
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


def map_hero_section(breadcrumb_html, h1_text, description_html, cta_label="Submit Job Request"):
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
