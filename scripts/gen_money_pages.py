#!/usr/bin/env python3
"""Generate programmatic service+city money pages at /[city]/[service]/.

For each of the 125 Virginia cities x 6 core services, build an SEO landing
page with:
  - The ZIP-select service banner ("Your Local Contractor is [ZIP]")
  - H1 / Title: [Service] in [City], VA
  - H2: [Service] Offered in [City]
  - H2: Why More [City] Homeowners Choose Us
  - H2: Service Area ZIP Codes
  - H2: Submit a Job Request for [Service] in [City], VA  + "Submit Job Request"
  - "Get a Free Quote" CTA on every page
"""
import os, re, html as html_mod, json, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = "/home/user/virginiabasementwaterproofing.com"
SRC  = "/root/.claude/uploads/d3aa2d35-0d52-4e41-a880-55c8b6248f0b/e4b92662-Outscraper20260604222103s2f_waterproofing_service.xlsx"
PHONE_TEL  = "+17577439050"
PHONE_DISP = "(757) 743-9050"

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

# ── collect ZIP codes per city from the dataset ───────────────────────────────
city_zips = defaultdict(set)
for r in data[1:]:
    if g(r, 'state_code') != 'VA': continue
    city = (g(r, 'city') or '').strip()
    zc   = (g(r, 'postal_code') or '').strip()
    if city and re.fullmatch(r'\d{5}', zc):
        city_zips[city].add(zc)

# ── city → region map (mirrors gen_cities.py) ─────────────────────────────────
CITY_REGION = {
    "Virginia Beach":("hampton-roads","Hampton Roads"),"Norfolk":("hampton-roads","Hampton Roads"),
    "Chesapeake":("hampton-roads","Hampton Roads"),"Suffolk":("hampton-roads","Hampton Roads"),
    "Portsmouth":("hampton-roads","Hampton Roads"),"Newport News":("hampton-roads","Hampton Roads"),
    "Hampton":("hampton-roads","Hampton Roads"),"Williamsburg":("hampton-roads","Hampton Roads"),
    "Yorktown":("hampton-roads","Hampton Roads"),"Smithfield":("hampton-roads","Hampton Roads"),
    "Franklin":("hampton-roads","Hampton Roads"),"Hopewell":("hampton-roads","Hampton Roads"),
    "Fort Monroe":("hampton-roads","Hampton Roads"),"Grafton":("hampton-roads","Hampton Roads"),
    "Toano":("hampton-roads","Hampton Roads"),"Hartfield":("hampton-roads","Hampton Roads"),
    "Heathsville":("hampton-roads","Hampton Roads"),"Topping":("hampton-roads","Hampton Roads"),
    "Eastville":("hampton-roads","Hampton Roads"),
    "Alexandria":("northern-virginia","Northern Virginia"),"Arlington":("northern-virginia","Northern Virginia"),
    "Fairfax":("northern-virginia","Northern Virginia"),"Falls Church":("northern-virginia","Northern Virginia"),
    "McLean":("northern-virginia","Northern Virginia"),"Reston":("northern-virginia","Northern Virginia"),
    "Herndon":("northern-virginia","Northern Virginia"),"Vienna":("northern-virginia","Northern Virginia"),
    "Sterling":("northern-virginia","Northern Virginia"),"Leesburg":("northern-virginia","Northern Virginia"),
    "Ashburn":("northern-virginia","Northern Virginia"),"Centreville":("northern-virginia","Northern Virginia"),
    "Chantilly":("northern-virginia","Northern Virginia"),"Manassas":("northern-virginia","Northern Virginia"),
    "Manassas Park":("northern-virginia","Northern Virginia"),"Gainesville":("northern-virginia","Northern Virginia"),
    "Woodbridge":("northern-virginia","Northern Virginia"),"Springfield":("northern-virginia","Northern Virginia"),
    "Lorton":("northern-virginia","Northern Virginia"),"Dumfries":("northern-virginia","Northern Virginia"),
    "South Riding":("northern-virginia","Northern Virginia"),"Purcellville":("northern-virginia","Northern Virginia"),
    "Hamilton":("northern-virginia","Northern Virginia"),"Waterford":("northern-virginia","Northern Virginia"),
    "Lovettsville":("northern-virginia","Northern Virginia"),"Warrenton":("northern-virginia","Northern Virginia"),
    "Bristow":("northern-virginia","Northern Virginia"),"Broad Run":("northern-virginia","Northern Virginia"),
    "Paris":("northern-virginia","Northern Virginia"),"Marshall":("northern-virginia","Northern Virginia"),
    "Midland":("northern-virginia","Northern Virginia"),"Remington":("northern-virginia","Northern Virginia"),
    "Amissville":("northern-virginia","Northern Virginia"),"Goldvein":("northern-virginia","Northern Virginia"),
    "Richmond":("richmond","Greater Richmond"),"Henrico":("richmond","Greater Richmond"),
    "Midlothian":("richmond","Greater Richmond"),"Glen Allen":("richmond","Greater Richmond"),
    "Mechanicsville":("richmond","Greater Richmond"),"Chester":("richmond","Greater Richmond"),
    "North Chesterfield":("richmond","Greater Richmond"),"South Chesterfield":("richmond","Greater Richmond"),
    "Ashland":("richmond","Greater Richmond"),"Powhatan":("richmond","Greater Richmond"),
    "Dinwiddie":("richmond","Greater Richmond"),"Prince George":("richmond","Greater Richmond"),
    "Montpelier":("richmond","Greater Richmond"),"Rockville":("richmond","Greater Richmond"),
    "Charles City":("richmond","Greater Richmond"),"Manquin":("richmond","Greater Richmond"),
    "Troy":("richmond","Greater Richmond"),
    "Winchester":("shenandoah-valley","Shenandoah Valley"),"Harrisonburg":("shenandoah-valley","Shenandoah Valley"),
    "Staunton":("shenandoah-valley","Shenandoah Valley"),"Waynesboro":("shenandoah-valley","Shenandoah Valley"),
    "Front Royal":("shenandoah-valley","Shenandoah Valley"),"New Market":("shenandoah-valley","Shenandoah Valley"),
    "Mt Sidney":("shenandoah-valley","Shenandoah Valley"),"Dayton":("shenandoah-valley","Shenandoah Valley"),
    "Churchville":("shenandoah-valley","Shenandoah Valley"),"Linden":("shenandoah-valley","Shenandoah Valley"),
    "Roanoke":("western-virginia","Western Virginia"),"Lynchburg":("western-virginia","Western Virginia"),
    "Blacksburg":("western-virginia","Western Virginia"),"Christiansburg":("western-virginia","Western Virginia"),
    "Salem":("western-virginia","Western Virginia"),"Vinton":("western-virginia","Western Virginia"),
    "Bedford":("western-virginia","Western Virginia"),"Amherst":("western-virginia","Western Virginia"),
    "Troutville":("western-virginia","Western Virginia"),"Cave Spring":("western-virginia","Western Virginia"),
    "Moneta":("western-virginia","Western Virginia"),"Wirtz":("western-virginia","Western Virginia"),
    "Hardy":("western-virginia","Western Virginia"),"Gladstone":("western-virginia","Western Virginia"),
    "Evington":("western-virginia","Western Virginia"),"Rustburg":("western-virginia","Western Virginia"),
    "Hollins":("western-virginia","Western Virginia"),"Forest":("western-virginia","Western Virginia"),
    "Max Meadows":("western-virginia","Western Virginia"),"Glade Spring":("western-virginia","Western Virginia"),
    "Wytheville":("western-virginia","Western Virginia"),"Bristol":("western-virginia","Western Virginia"),
    "Richlands":("western-virginia","Western Virginia"),"Clintwood":("western-virginia","Western Virginia"),
    "Coeburn":("western-virginia","Western Virginia"),
    "Charlottesville":("central-virginia","Central Virginia"),"Fredericksburg":("central-virginia","Central Virginia"),
    "Stafford":("central-virginia","Central Virginia"),"Orange":("central-virginia","Central Virginia"),
    "Madison":("central-virginia","Central Virginia"),"Culpeper":("central-virginia","Central Virginia"),
    "King George":("central-virginia","Central Virginia"),"Spotsylvania Courthouse":("central-virginia","Central Virginia"),
    "Farmville":("central-virginia","Central Virginia"),"Kenbridge":("central-virginia","Central Virginia"),
    "Keysville":("central-virginia","Central Virginia"),"South Hill":("central-virginia","Central Virginia"),
    "Clarksville":("central-virginia","Central Virginia"),"Halifax":("central-virginia","Central Virginia"),
    "Ruckersville":("central-virginia","Central Virginia"),"Danville":("central-virginia","Central Virginia"),
    "Martinsville":("central-virginia","Central Virginia"),"Collinsville":("central-virginia","Central Virginia"),
    "Lancaster":("central-virginia","Central Virginia"),"Gloucester":("central-virginia","Central Virginia"),
}

# ── services (Core 6) ─────────────────────────────────────────────────────────
# each: slug, name, short blurb, list of (sub-service name, sub-service desc)
SERVICES = [
    {
        "slug": "basement-waterproofing",
        "name": "Basement Waterproofing",
        "short": "basement waterproofing",
        "blurb": "Keep your basement permanently dry with professional interior and exterior waterproofing systems engineered for Virginia's wet, clay-heavy soils.",
        "offerings": [
            ("Interior Drainage Systems", "Sub-floor perimeter drains that channel water to a sump pump and away from your foundation."),
            ("Exterior Waterproofing", "Below-grade membrane and drainage board applied to the outside of foundation walls to stop water before it enters."),
            ("Sump Pump Installation", "Primary and battery-backup sump pumps sized to handle Virginia's heaviest storms."),
            ("Vapor Barriers & Wall Systems", "Sealed wall liners that block humidity, efflorescence, and seepage through block and poured walls."),
            ("Foundation Crack Sealing", "Polyurethane and epoxy injection that permanently seals leaking cracks in poured-concrete walls."),
        ],
    },
    {
        "slug": "crawl-space-encapsulation",
        "name": "Crawl Space Encapsulation",
        "short": "crawl space encapsulation",
        "blurb": "Seal your crawl space from ground moisture and humid outside air with a complete encapsulation system that protects your home's structure and air quality.",
        "offerings": [
            ("Heavy-Duty Vapor Barriers", "12–20 mil reinforced liners across the floor and up foundation walls to cut off soil moisture."),
            ("Crawl Space Dehumidifiers", "Commercial-grade units that hold humidity below 55% year-round to stop mold and wood rot."),
            ("Vent Sealing & Insulation", "Closing foundation vents and insulating walls to bring the crawl space inside your thermal envelope."),
            ("Drainage & Sump Systems", "Interior drains and sump pumps that remove groundwater from under the vapor barrier."),
            ("Mold & Moisture Cleanup", "Treatment of existing mold, wood rot, and damaged insulation before sealing."),
        ],
    },
    {
        "slug": "foundation-repair",
        "name": "Foundation Repair",
        "short": "foundation repair",
        "blurb": "Stabilize settling, bowing, and cracking foundations with engineered repair solutions built for Virginia's expansive clay and sloped terrain.",
        "offerings": [
            ("Foundation Crack Repair", "Structural sealing of cracks in poured and block foundations to stop movement and water intrusion."),
            ("Wall Anchors & Bracing", "Steel anchors and carbon-fiber straps that stabilize bowing or leaning basement walls."),
            ("Push & Helical Piers", "Deep-driven piers that lift and permanently support settling foundations."),
            ("Settlement Correction", "Re-leveling of sunken footings and slabs to restore doors, windows, and floors."),
            ("Structural Inspections", "On-site assessment of cracking, settling, and moisture issues with a written repair plan."),
        ],
    },
    {
        "slug": "sump-pump-installation",
        "name": "Sump Pump Installation",
        "short": "sump pump installation",
        "blurb": "Protect your basement from flooding with a properly sized sump pump and battery backup system installed by licensed Virginia contractors.",
        "offerings": [
            ("Primary Sump Pumps", "High-capacity submersible and pedestal pumps sized to your home's water load."),
            ("Battery Backup Systems", "Secondary pumps that keep working through power outages and pump failures."),
            ("Sump Pit Installation", "New basins and liners installed with proper drainage to the pump."),
            ("Discharge Line Routing", "Freeze-resistant discharge lines that move water safely away from the foundation."),
            ("Pump Replacement & Service", "Fast replacement of failed or undersized pumps, plus routine maintenance."),
        ],
    },
    {
        "slug": "french-drain-installation",
        "name": "French Drain Installation",
        "short": "French drain installation",
        "blurb": "Redirect groundwater away from your foundation with professionally designed interior and exterior French drain systems.",
        "offerings": [
            ("Interior French Drains", "Perimeter drains installed beneath the basement slab to capture and remove seepage."),
            ("Exterior French Drains", "Gravel-bedded perforated pipe that intercepts water before it reaches your foundation."),
            ("Yard & Surface Drainage", "Surface drains and grading that move stormwater away from the home."),
            ("Downspout & Gutter Tie-Ins", "Connecting roof runoff to buried drains that discharge well away from the foundation."),
            ("Curtain Drains", "Shallow intercept drains for sloped lots and high-water-table properties."),
        ],
    },
    {
        "slug": "basement-crack-repair",
        "name": "Basement Crack Repair",
        "short": "basement crack repair",
        "blurb": "Permanently seal leaking and structural cracks in basement walls and floors with professional injection and reinforcement systems.",
        "offerings": [
            ("Polyurethane Crack Injection", "Flexible sealant that fills and waterproofs actively leaking cracks."),
            ("Epoxy Crack Injection", "High-strength structural bonding that restores the integrity of cracked concrete."),
            ("Carbon Fiber Reinforcement", "Bonded straps that stop cracks from widening and reinforce bowing walls."),
            ("Floor & Slab Crack Sealing", "Sealing of basement floor cracks that allow water and radon to enter."),
            ("Leaking Pipe Penetration Repair", "Sealing of gaps around pipes and utility penetrations through foundation walls."),
        ],
    },    {
        "slug": "basement-water-damage-restoration",
        "name": "Basement Water Damage Restoration",
        "label": "Water Damage Restoration",
        "short": "basement water damage restoration",
        "blurb": "Fast, professional water damage restoration for Virginia basements — emergency extraction, structural drying, mold prevention, and full rebuild services.",
        "offerings": [
            ("Emergency Water Extraction", "Truck-mounted and submersible extraction equipment removes standing water from flooded basements within hours of your call — 24/7 response."),
            ("Structural Drying & Dehumidification", "Industrial air movers and commercial dehumidifiers dry framing, subfloor, drywall, and concrete to measured moisture targets, stopping secondary damage."),
            ("Mold Prevention & Remediation", "Antimicrobial treatment applied during the drying process prevents mold colonies from establishing. Active mold growth is safely remediated and removed."),
            ("Damaged Material Removal & Rebuild", "Saturated drywall, insulation, flooring, and framing that cannot be dried in place are removed and replaced with code-compliant materials."),
            ("Contents Cleaning & Pack-Out", "Furniture, stored items, and personal belongings are inventoried, cleaned on-site or packed out for off-site drying and restoration."),
        ],
    },
    {
        "slug": "basement-remodeling",
        "name": "Basement Remodeling",
        "label": "Basement Remodeling",
        "short": "basement remodeling",
        "blurb": "Transform your unfinished or dated Virginia basement into livable, functional space — home offices, family rooms, guest suites, and more — with licensed local remodeling contractors.",
        "offerings": [
            ("Basement Finishing & Framing", "Full framing, insulation, drywall, and finishing that converts raw basement space into a conditioned, livable room ready for flooring and paint."),
            ("Flooring Installation", "Moisture-resistant flooring options — luxury vinyl plank, engineered hardwood, tile, and carpet — selected and installed for below-grade conditions."),
            ("Egress Windows & Permits", "Code-compliant egress window installation that makes basement bedrooms legal, improves natural light, and provides emergency exit access."),
            ("Bathroom & Wet Bar Rough-In", "Plumbing rough-in and finish work for basement half-baths, full bathrooms, and wet bar areas including drain tie-in and fixture installation."),
            ("Lighting, Electrical & HVAC", "Recessed lighting, outlet rough-in, panel upgrades, and HVAC extensions that make the finished basement comfortable year-round."),
        ],
    },
    {
        "slug": "black-mold-treatment",
        "name": "Black Mold Treatment",
        "label": "Black Mold Treatment",
        "short": "black mold treatment",
        "blurb": "Safe, thorough black mold testing, removal, and remediation for Virginia basements and crawl spaces — performed by licensed contractors following EPA and IICRC protocols.",
        "offerings": [
            ("Mold Testing & Air Sampling", "Certified inspectors take surface swab and air samples to confirm mold species, measure spore counts, and define the scope of contamination before any work begins."),
            ("Containment & Safe Removal", "Negative-pressure containment barriers isolate the work area. Contaminated drywall, insulation, and wood materials are removed following IICRC S520 remediation standards."),
            ("Structural Surface Treatment", "Exposed framing, joists, concrete, and block are HEPA-vacuumed, scrubbed, and treated with EPA-registered antimicrobial and encapsulant products."),
            ("Moisture Source Correction", "Remediation without fixing the moisture source always fails. Our contractors identify and correct the water intrusion — drainage, vapor barrier, waterproofing, or HVAC — that fed the mold."),
            ("Post-Remediation Clearance Testing", "Independent air and surface testing after work is complete confirms that spore counts have returned to normal levels and the space is safe to reoccupy."),
        ],
    },
    {
        "slug": "emergency-water-clean-up",
        "name": "Emergency Water Clean Up",
        "label": "Emergency Water Clean Up",
        "short": "emergency water clean up",
        "blurb": "Fast, 24/7 emergency water cleanup for flooded Virginia basements — rapid water extraction, structural drying, and sanitizing to stop damage before it spreads.",
        "offerings": [
            ("24/7 Emergency Response", "Round-the-clock dispatch gets a crew to your flooded basement fast — because every hour that water sits deepens the structural and mold damage."),
            ("Standing Water Extraction", "High-capacity truck-mounted and submersible pumps remove standing water quickly to halt damage to framing, flooring, and stored belongings."),
            ("Rapid Drying & Dehumidification", "Industrial air movers and commercial dehumidifiers pull moisture out of subfloor, walls, and concrete to measured dryness targets."),
            ("Sanitizing & Disinfection", "Antimicrobial cleaning of affected surfaces eliminates bacteria and contaminants left behind by sewage backups, storm water, and flooding."),
            ("Damaged Material Removal", "Saturated drywall, insulation, carpet, and flooring that cannot be salvaged are removed and hauled away so drying and rebuilding can begin."),
        ],
    },
    {
        "slug": "mobile-home-vapor-barrier",
        "name": "Mobile Home Vapor Barrier",
        "label": "Mobile Home Vapor Barrier",
        "short": "mobile home vapor barrier",
        "blurb": "Professional vapor barrier installation and underbelly repair for Virginia mobile and manufactured homes — sealing out ground moisture, mold, cold drafts, and pests.",
        "offerings": [
            ("Underbelly Vapor Barrier Installation", "Heavy-duty polyethylene liners installed across the underbelly to block ground moisture from rising into the floor and insulation."),
            ("Belly Wrap Repair & Replacement", "Torn or sagging factory belly wrap is patched or fully replaced to reseal the underside of your manufactured home."),
            ("Under-Home Moisture Control", "Sealing and grading beneath skirted mobile homes to stop standing water and humidity from rotting the structure."),
            ("Underfloor Insulation Replacement", "Wet, fallen, or rodent-damaged underfloor insulation is removed and replaced to restore comfort and lower energy bills."),
            ("Skirting & Vent Sealing", "Proper skirting and vent management keeps animals, moisture, and cold air out of the crawl area beneath the home."),
        ],
    },
    {
        "slug": "thermal-dry-floor-installation",
        "name": "Thermal Dry Floor Installation",
        "label": "Thermal Dry Floor Installation",
        "short": "thermal dry floor installation",
        "blurb": "Insulated, moisture-proof basement floor systems for Virginia homes — a warm, dry, mold-resistant barrier installed between your finished floor and the cold concrete slab.",
        "offerings": [
            ("Insulated Subfloor Matting", "Dimpled thermal floor panels create an air gap and moisture break between the cold concrete slab and your finished floor surface."),
            ("Built-In Vapor Barrier Layer", "An integrated vapor barrier blocks slab moisture and efflorescence from reaching carpet, vinyl, or laminate installed above."),
            ("Warmer, Energy-Efficient Floors", "The thermal layer keeps basement floors noticeably warmer underfoot and helps reduce heating costs in finished living space."),
            ("Mold-Resistant Inorganic Materials", "Inorganic panels won't feed mold or rot the way wood subfloors and padding do in damp, below-grade conditions."),
            ("Finished-Floor-Ready Panels", "Rigid, level panels install directly over concrete and accept carpet, laminate, luxury vinyl plank, or engineered flooring."),
        ],
    },
]

# ── helpers ───────────────────────────────────────────────────────────────────
def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return re.sub(r'-+', '-', s) or 'x'

def esc(x): return html_mod.escape(str(x), quote=True) if x is not None else ''

# generic VA ZIP fallback by region (used only when a city has no dataset ZIPs)
REGION_FALLBACK_ZIPS = {
    "hampton-roads":    ["23320","23451","23502","23601","23701"],
    "northern-virginia":["22030","22101","22201","22314","20176"],
    "richmond":         ["23220","23223","23228","23230","23060"],
    "shenandoah-valley":["22601","22801","24401","22630","22980"],
    "western-virginia": ["24011","24016","24501","24060","24153"],
    "central-virginia": ["22901","22401","22554","24541","22701"],
}

REASONS = [
    ("Licensed &amp; Insured Local Pros",
     "Every contractor in our {city} network is licensed in Virginia and carries liability insurance, so your home and your investment are protected from the first inspection through the final walkthrough."),
    ("Free, No-Obligation Estimates",
     "Homeowners in {city} get a free on-site evaluation and a written estimate before any work begins. There is never pressure to commit and never a hidden fee."),
    ("Built for Virginia's Soils &amp; Climate",
     "Our {city} contractors understand the local clay soils, high water tables, and freeze-thaw cycles that drive moisture problems here, and they engineer solutions that hold up to {region} conditions."),
    ("Workmanship You Can Trust",
     "From {service_lc} to full system installs, {city} crews show up on time, protect your property, and back their work with transferable warranties."),
    ("One Call Connects You Locally",
     "Call {phone} and we match you with a vetted {city}-area contractor who knows your neighborhood — no national call center, no runaround."),
]

# ── shared components ─────────────────────────────────────────────────────────
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
          <div class="mega-menu__grid">
            <a href="/services/basement-waterproofing/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#128167;</span><span class="mega-menu__text"><strong>Basement Waterproofing</strong><span>Interior drains, exterior membranes &amp; sump systems</span></span></a>
            <a href="/services/crawl-space-encapsulation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#127968;</span><span class="mega-menu__text"><strong>Crawl Space Encapsulation</strong><span>Vapor barriers, vent sealing &amp; dehumidifiers</span></span></a>
            <a href="/services/foundation-repair/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#127959;</span><span class="mega-menu__text"><strong>Foundation Repair</strong><span>Piers, wall anchors &amp; carbon-fiber straps</span></span></a>
            <a href="/services/sump-pump-installation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#9889;</span><span class="mega-menu__text"><strong>Sump Pump Installation</strong><span>Primary &amp; battery-backup pumps</span></span></a>
            <a href="/services/french-drain-installation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#127794;</span><span class="mega-menu__text"><strong>French Drain Installation</strong><span>Interior, exterior &amp; curtain drains</span></span></a>
            <a href="/services/basement-crack-repair/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#128295;</span><span class="mega-menu__text"><strong>Basement Crack Repair</strong><span>Polyurethane &amp; epoxy injection</span></span></a>
            <a href="/services/basement-water-damage-restoration/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#128680;</span><span class="mega-menu__text"><strong>Water Damage Restoration</strong><span>Emergency extraction &amp; structural drying</span></span></a>
            <a href="/services/emergency-water-clean-up/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#128694;</span><span class="mega-menu__text"><strong>Emergency Water Clean Up</strong><span>24/7 flooding response &amp; sanitizing</span></span></a>
            <a href="/services/basement-remodeling/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#128205;</span><span class="mega-menu__text"><strong>Basement Remodeling</strong><span>Finishing, flooring &amp; egress windows</span></span></a>
            <a href="/services/black-mold-treatment/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#129532;</span><span class="mega-menu__text"><strong>Black Mold Treatment</strong><span>Testing, containment &amp; remediation</span></span></a>
            <a href="/services/mobile-home-vapor-barrier/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#127978;</span><span class="mega-menu__text"><strong>Mobile Home Vapor Barrier</strong><span>Underbelly sealing &amp; belly-wrap repair</span></span></a>
            <a href="/services/thermal-dry-floor-installation/" class="mega-menu__item" role="menuitem"><span class="mega-menu__icon">&#9632;</span><span class="mega-menu__text"><strong>Thermal Dry Floor Installation</strong><span>Insulated, moisture-proof subfloor panels</span></span></a>
          </div>
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
      <div><h4>Services</h4><ul><li><a href="/services/basement-waterproofing/">Basement Waterproofing</a></li><li><a href="/services/crawl-space-encapsulation/">Crawl Space Encapsulation</a></li><li><a href="/services/foundation-repair/">Foundation Repair</a></li><li><a href="/services/sump-pump-installation/">Sump Pump Installation</a></li><li><a href="/services/french-drain-installation/">French Drain Installation</a></li><li><a href="/services/basement-crack-repair/">Basement Crack Repair</a></li><li><a href="/services/basement-water-damage-restoration/">Water Damage Restoration</a></li><li><a href="/services/basement-remodeling/">Basement Remodeling</a></li><li><a href="/services/black-mold-treatment/">Black Mold Treatment</a></li><li><a href="/services/emergency-water-clean-up/">Emergency Water Clean Up</a></li><li><a href="/services/mobile-home-vapor-barrier/">Mobile Home Vapor Barrier</a></li><li><a href="/services/thermal-dry-floor-installation/">Thermal Dry Floor Installation</a></li></ul></div>
      <div><h4>Company</h4><ul><li><a href="/about/">About Us</a></li><li><a href="/get-a-quote/">Contact</a></li><li><a href="/sitemap.xml">Sitemap</a></li></ul></div>
      <div><h4>Legal</h4><ul><li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/terms-of-service/">Terms of Service</a></li><li><a href="/disclaimer/">Disclaimer</a></li></ul></div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year>2026</span> VirginiaBasementWaterproofing.org &mdash; All rights reserved.</span>
      <span>Call us: <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></span>
    </div>
    <p class="disclaimer-note">VirginiaBasementWaterproofing.org is a free directory and lead-referral service. We are not a licensed contractor and do not perform waterproofing work ourselves. Listed companies are independent businesses; we make no warranty regarding any contractor\'s work. Always verify licensing and insurance before hiring.</p>
  </div>
</footer>
<script src="/js/main.js"></script>
</body>
</html>'''

def zip_banner(zips):
    # Dynamic banner — JS in main.js detects location and renders contractor name
    return f'''<div class="service-banner" id="dealer-card" aria-live="polite">
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

def page_head(title, description, canonical, schema_json, zips=None):
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
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<link rel="stylesheet" href="/css/styles.css">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
<script type="application/ld+json">{schema_json}</script>
</head>
<body>
{SITE_HEADER}
{zip_banner(zips)}'''

# ── generate ──────────────────────────────────────────────────────────────────
count = 0
index_links = defaultdict(list)   # region_slug -> list of (city, service) link rows

for city, (region_slug, region_label) in CITY_REGION.items():
    city_slug = slugify(city)
    zips = sorted(city_zips.get(city, []))
    if not zips:
        zips = REGION_FALLBACK_ZIPS.get(region_slug, ["23000"])

    # ZIP list HTML (chips)
    zip_chips = ''.join(f'<span class="zip-chip">{z}</span>' for z in zips)

    for svc in SERVICES:
        sname  = svc["name"]
        sslug  = svc["slug"]
        slc    = svc["short"]
        url    = f"/{city_slug}/{sslug}/"
        canonical = f"https://www.virginiabasementwaterproofing.org{url}"
        title  = f"{sname} in {city}, VA"

        description = (f"{sname} in {city}, Virginia. {svc['blurb']} "
                       f"Licensed local contractors, free estimates. Call {PHONE_DISP}.")

        # offerings list
        off_html = ''.join(
            f'''<div class="offering">
            <h3>{esc(oname)}</h3>
            <p>{esc(odesc)}</p>
          </div>''' for oname, odesc in svc["offerings"])

        # reasons list
        reason_html = ''.join(
            f'''<li><strong>{rtitle}</strong><span>{rbody.format(city=esc(city), region=esc(region_label), service_lc=esc(slc), phone=PHONE_DISP)}</span></li>'''
            for rtitle, rbody in REASONS)

        schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "Service",
            "serviceType": sname,
            "name": title,
            "description": svc["blurb"],
            "areaServed": {"@type": "City", "name": city, "addressRegion": "VA"},
            "provider": {
                "@type": "Organization",
                "name": "Virginia Basement Waterproofing",
                "telephone": PHONE_TEL,
                "url": "https://www.virginiabasementwaterproofing.org/",
            },
            "telephone": PHONE_TEL,
            "url": canonical,
        })

        page = page_head(title + " | Free Estimates", description, canonical, schema, zips)
        page += f'''
<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / <a href="/virginia/{region_slug}/{city_slug}/">{esc(city)}</a> / {esc(sname)}</div>
    <h1>{esc(sname)} in {esc(city)}, VA</h1>
    <p>Connect with licensed, insured {esc(slc)} contractors serving {esc(city)} and the surrounding {esc(region_label)} area. Free estimates, no obligation, and one local call away.</p>
    <div style="margin-top:18px; display:flex; gap:12px; flex-wrap:wrap;">
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Submit Job Request</a>
      <a href="tel:{PHONE_TEL}" class="btn btn--ghost btn--lg">Call {PHONE_DISP}</a>
    </div>
  </div>
</div>

<main>
<section class="section">
  <div class="container">
    <p class="lead">{esc(svc["blurb"])} Whether you own an older home with a damp, musty basement or a newer property dealing with seasonal seepage, our {esc(city)} contractors deliver lasting {esc(slc)} solutions backed by warranties.</p>

    <h2>{esc(sname)} Offered in {esc(city)}:</h2>
    <div class="offerings-grid">
      {off_html}
    </div>

    <h2>Why More {esc(city)} Homeowners Choose Us:</h2>
    <ul class="reasons-list">
      {reason_html}
    </ul>

    <h2>Service Area ZIP Codes</h2>
    <p>Our {esc(city)} {esc(slc)} contractors serve homeowners across {esc(city)} and nearby {esc(region_label)} communities, including these ZIP codes:</p>
    <div class="zip-chip-row">
      {zip_chips}
    </div>
    <p class="text-muted" style="margin-top:14px;">Don't see your ZIP code? Call <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a> &mdash; we serve the entire {esc(city)} area.</p>

    <div class="cta-band" id="job-request" style="margin-top:48px;">
      <h2>Submit a Job Request for {esc(sname)} in {esc(city)}, VA</h2>
      <p>Once you submit a job request, we'll connect you with the ideal licensed contractor for your situation. They'll reach out within 1–3 business days.</p>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <a href="/get-a-quote/" class="btn btn--primary btn--lg">Submit Job Request</a>
        <a href="tel:{PHONE_TEL}" class="btn btn--ghost btn--lg">Call {PHONE_DISP}</a>
      </div>
    </div>

    <div style="margin-top:40px;">
      <h2>Other Services in {esc(city)}</h2>
      <div class="related-services">
        {''.join(f'<a href="/{city_slug}/{s["slug"]}/" class="related-chip">{esc(s.get("label", s["name"]))}</a>' for s in SERVICES if s["slug"] != sslug)}
      </div>
    </div>
  </div>
</section>
</main>
'''
        page += FOOTER

        out_dir = os.path.join(ROOT, city_slug, sslug)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'index.html'), 'w') as f:
            f.write(page)
        count += 1
        index_links[region_slug].append((city, city_slug, sname, sslug))

print(f"Generated {count} money pages ({len(CITY_REGION)} cities x {len(SERVICES)} services)")

# write a manifest for sitemap generation
manifest = []
for city, (region_slug, _) in CITY_REGION.items():
    cs = slugify(city)
    for svc in SERVICES:
        manifest.append(f"/{cs}/{svc['slug']}/")
with open(os.path.join(ROOT, 'scripts', 'money_page_urls.json'), 'w') as f:
    json.dump(manifest, f, indent=2)
print(f"Wrote money_page_urls.json ({len(manifest)} urls)")
