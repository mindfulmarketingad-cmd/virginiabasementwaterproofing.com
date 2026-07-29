#!/usr/bin/env python3
"""Generate the /find/ searchmap section.

  /find/                              hub -- links to every searchmap page
  /find/<service>-va/                 statewide (replaces /services/<slug>/)
  /find/<service>-<city>-va/          city-level, e.g. /find/waterproofing-hampton-va/

Every page carries the same searchmap component as the homepage; window.FIND_CONFIG
preselects the service filter and recenters the map.
"""
import os, sys, json, html, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_html import (  # noqa: E402
    SERVICES, SITE_HEADER, FOOTER, SEARCHMAP_HEAD, SEARCHMAP_SCRIPTS, searchmap_section)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.virginiabasementwaterproofing.org"
ADSENSE = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
           '?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>')


def esc(s):
    return html.escape(str(s or ""), quote=True)


# ---------- data ----------
with open(os.path.join(ROOT, "scripts", "city_urls.json"), encoding="utf-8") as f:
    CITY_URLS = json.load(f)                       # "Hampton" -> "/virginia/hampton-roads/hampton/"
CITY_BY_SLUG = {u.strip("/").split("/")[-1]: n for n, u in CITY_URLS.items()}
REGION_BY_SLUG = {u.strip("/").split("/")[-1]: u.strip("/").split("/")[1]
                  for u in CITY_URLS.values() if len(u.strip("/").split("/")) > 2}

with open(os.path.join(ROOT, "data", "partners.json"), encoding="utf-8") as f:
    PARTNERS = json.load(f)

# Long-form copy + ZIP link blocks salvaged from the retired /services/<slug>/
# pages, so converting them to searchmaps costs no content or internal links.
with open(os.path.join(ROOT, "scripts", "service_legacy.json"), encoding="utf-8") as f:
    LEGACY = json.load(f)

with open(os.path.join(ROOT, "scripts", "zip_city_map.json"), encoding="utf-8") as f:
    ZIP_CITY = json.load(f)
with open(os.path.join(ROOT, "data", "va-zip-centroids.json"), encoding="utf-8") as f:
    CENTROIDS = json.load(f)

REGION_LABEL = {
    "hampton-roads": "Hampton Roads",
    "northern-virginia": "Northern Virginia",
    "richmond": "Greater Richmond",
    "central-virginia": "Central Virginia",
    "shenandoah-valley": "Shenandoah Valley",
    "western-virginia": "Western Virginia",
    "central-western-valley": "Central & Western Valley",
}

# Region-specific soil/geography blurb -- real variance across the 653 city
# pages instead of one paragraph copy-pasted everywhere.
REGION_CAUSES = {
    "hampton-roads": (
        "a high water table and sandy, low-lying coastal soil. Groundwater sits close to the "
        "surface for much of the year, so basements and crawl spaces here fight hydrostatic "
        "pressure almost constantly, and storm surge or nor'easters can push the table up "
        "further overnight."),
    "northern-virginia": (
        "heavy clay soil that expands when wet and shrinks when dry. That cycle stresses "
        "foundation walls every season, and the region's dense, older housing stock means "
        "many foundations were built before modern drainage codes existed."),
    "richmond": (
        "clay-heavy Piedmont soil combined with mature tree roots common in older "
        "neighborhoods. Roots seeking moisture can crack footings and clog drain tile, while "
        "clay swelling adds constant pressure against basement walls."),
    "central-virginia": (
        "rolling Piedmont clay and a mix of older rural foundations. Grading that was adequate "
        "decades ago often no longer directs water away from the house, and clay expansion "
        "does the rest."),
    "shenandoah-valley": (
        "limestone bedrock and karst terrain, which can create unpredictable underground water "
        "flow and, in some areas, sinkhole risk. Valley clay soils on top of that bedrock still "
        "expand and contract with the seasons."),
    "western-virginia": (
        "steep terrain and rocky, mountainous soil. Water moves fast downhill toward "
        "foundations built into hillsides, and older homes in the region often have minimal "
        "exterior drainage to intercept it."),
    "central-western-valley": (
        "a transitional mix of Piedmont clay and valley limestone geology. Foundations here see "
        "both the clay expansion common further east and the bedrock drainage quirks typical of "
        "the Shenandoah Valley."),
}
REGION_CAUSES_GENERIC = (
    "Virginia's mix of clay-heavy soil and a high water table in many areas. Clay expands when "
    "saturated and contracts when dry, and that seasonal cycle puts steady pressure on "
    "foundation walls and footings statewide.")

# Per-service facts used in the FAQ. Ranges match the homepage cost table so the
# whole site quotes the same numbers.
SERVICE_INFO = {
    "waterproofing": {
        "cost": "$3,000&ndash;$9,000 for an interior drainage system, or $8,000&ndash;$15,000+ "
                "for exterior waterproofing",
        "duration": "1&ndash;3 days for an interior system; exterior work can take a week or more "
                    "because it involves excavation",
        "urgent": False,
        "warranty": "Reputable installers back interior drainage and sump systems with a "
                    "transferable warranty, often 10&ndash;25 years.",
    },
    "crawl-space-encapsulation": {
        "cost": "$1,500&ndash;$8,000 depending on square footage and whether a dehumidifier is included",
        "duration": "1&ndash;2 days for most residential crawl spaces",
        "urgent": False,
        "warranty": "Vapor barrier and encapsulation warranties commonly run 15&ndash;25 years "
                    "and are usually transferable.",
    },
    "foundation-repair": {
        "cost": "$500&ndash;$1,500 per crack for injection repair, or several thousand dollars for "
                "wall anchors or push piers on a bowing or settling wall",
        "duration": "A single crack injection can be same-day; wall anchor or pier systems "
                    "typically take 1&ndash;3 days",
        "urgent": False,
        "warranty": "Structural repairs like wall anchors and piers are usually backed by a "
                    "lifetime transferable warranty from the manufacturer.",
    },
    "sump-pump-installation": {
        "cost": "$1,000&ndash;$3,500 including a battery-backup pump",
        "duration": "Most installations are completed in a single day",
        "urgent": True,
        "warranty": "Pump manufacturers typically warranty the unit itself for 3&ndash;5 years, "
                    "with the installer separately warrantying the labor.",
    },
    "french-drain-installation": {
        "cost": "$2,000&ndash;$6,500 for an interior system, more for a full exterior French drain",
        "duration": "1&ndash;2 days for interior drain tile; exterior drains can take longer "
                    "depending on the run length",
        "urgent": False,
        "warranty": "Interior drain tile is commonly warrantied for the life of the system when "
                    "paired with a sump pump.",
    },
    "basement-crack-repair": {
        "cost": "$500&ndash;$1,500 per crack for epoxy or polyurethane injection",
        "duration": "Most single-crack repairs are completed in a few hours",
        "urgent": False,
        "warranty": "Crack injection is typically warrantied against re-leaking for as long as "
                    "you own the home.",
    },
    "basement-water-damage-restoration": {
        "cost": "$1,500&ndash;$8,000+ depending on how much water intruded and whether drywall or "
                "flooring needs replacing",
        "duration": "Water extraction starts the same day; full structural drying can take "
                    "3&ndash;5 days",
        "urgent": True,
        "warranty": "Restoration work itself is not usually warrantied the way installed "
                    "systems are, since the goal is repair rather than a new product.",
    },
    "emergency-water-clean-up": {
        "cost": "$500&ndash;$3,000 for emergency extraction, before any repair work",
        "duration": "Response is typically same-day, and extraction itself can be finished in "
                    "hours once a crew is on site",
        "urgent": True,
        "warranty": "Emergency clean-up is a response service, not an installed product, so it "
                    "is not typically warrantied.",
    },
    "basement-remodeling": {
        "cost": "$10,000&ndash;$35,000+ depending on finish level, egress windows, and square footage",
        "duration": "2&ndash;6 weeks depending on scope",
        "urgent": False,
        "warranty": "Workmanship warranties for finishing work are usually 1&ndash;5 years; ask "
                    "what is covered before signing.",
    },
    "black-mold-treatment": {
        "cost": "$500&ndash;$6,000 depending on the affected area and whether testing is included",
        "duration": "Small areas can be treated in a day; larger remediation jobs can take "
                    "several days of containment and drying",
        "urgent": True,
        "warranty": "Mold remediation itself is not usually warrantied, but fixing the moisture "
                    "source that caused it often is.",
    },
    "mobile-home-vapor-barrier": {
        "cost": "$1,000&ndash;$4,000 depending on underbelly size and condition",
        "duration": "Most jobs are completed in a single day",
        "urgent": False,
        "warranty": "Vapor barrier and belly-wrap repairs are commonly warrantied for "
                    "10&ndash;15 years.",
    },
    "thermal-dry-floor-installation": {
        "cost": "$3,000&ndash;$10,000 depending on square footage",
        "duration": "1&ndash;3 days for most residential installations",
        "urgent": False,
        "warranty": "Insulated subfloor panel systems are commonly warrantied for "
                    "10&ndash;25 years.",
    },
}

# Natural-language noun for "what causes X" / "X emergency" questions -- avoids
# awkward phrasing like "what causes foundation repair problems".
PROBLEM_NOUN = {
    "waterproofing": "wet basement problems",
    "crawl-space-encapsulation": "crawl space moisture problems",
    "foundation-repair": "foundation problems",
    "sump-pump-installation": "basement flooding",
    "french-drain-installation": "poor yard and foundation drainage",
    "basement-crack-repair": "foundation cracks",
    "basement-water-damage-restoration": "water damage",
    "emergency-water-clean-up": "flooding emergencies",
    "basement-remodeling": "the basement moisture issues that block finishing a space",
    "black-mold-treatment": "mold growth",
    "mobile-home-vapor-barrier": "moisture under mobile and manufactured homes",
    "thermal-dry-floor-installation": "cold, damp subfloors",
}

with open(os.path.join(ROOT, "scripts", "zip_city_map.json"), encoding="utf-8") as f:
    _ZIP_CITY_RAW = json.load(f)
CITY_ZIPS = {}
for _z, _c in _ZIP_CITY_RAW.items():
    CITY_ZIPS.setdefault(_c, []).append(_z)
for _c in CITY_ZIPS:
    CITY_ZIPS[_c].sort()


def faq_schema(qa_pairs):
    plain = re.compile(r"&\w+;|<[^>]+>")
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": plain.sub(" ", q).strip(),
             "acceptedAnswer": {"@type": "Answer", "text": plain.sub(" ", a).strip()}}
            for q, a in qa_pairs],
    })


def faq_html(qa_pairs):
    items = "".join(f'<div class="faq-item"><h2>{q}</h2><p>{a}</p></div>' for q, a in qa_pairs)
    return f'''
    <span class="eyebrow">Common Questions</span>
    <div class="faq-list">{items}</div>'''


def city_faq(svc, city, city_slug, rows, center):
    """Per-page FAQ for a /find/<service>-<city>-va/ page.

    Every answer pulls a real, page-specific fact (provider count, ZIP list,
    average local rating, region geology) rather than repeating one paragraph
    across all 653 city pages.
    """
    label, cat = svc["label"], svc["cat"]
    info = SERVICE_INFO.get(svc["find"], {})
    problem = PROBLEM_NOUN.get(svc["find"], f"{label.lower()} problems")
    n = len(rows)
    rated = [p for p in rows if p.get("rating")]
    avg = sum(p["rating"] for p in rated) / len(rated) if rated else 0
    zips = CITY_ZIPS.get(city, [])
    region = REGION_BY_SLUG.get(city_slug)
    region_label = REGION_LABEL.get(region, "Virginia")
    causes = REGION_CAUSES.get(region, REGION_CAUSES_GENERIC)
    open_now = sum(1 for p in rows if p.get("open_24h"))

    qa = []

    qa.append((
        f"How much does {label.lower()} cost in {esc(city)}, VA?",
        f"Typical cost runs {info.get('cost', 'a few thousand dollars depending on scope')}. "
        f"That is a statewide range, not a quote &mdash; the only accurate number comes from an "
        f"on-site inspection, which is free through this site."))

    if n:
        rating_note = (f" The {len(rated)} with a public rating average {avg:.1f}&#9733;."
                       if rated else "")
        qa.append((
            f"How many {label.lower()} contractors serve {esc(city)}?",
            f"We currently track {n} contractor{'s' if n != 1 else ''} within about 25 miles of "
            f"{esc(city)} that list {label.lower()} as a service.{rating_note} The map above "
            f"shows all of them; submit a job request and we&rsquo;ll match you with the "
            f"best-fit pro."))
    else:
        qa.append((
            f"Are there {label.lower()} contractors near {esc(city)}?",
            f"We don&rsquo;t yet have a {label.lower()} contractor listed within 25 miles of "
            f"{esc(city)} in our directory. Submit a job request anyway &mdash; we work with "
            f"contractors outside our standard listings and can often still find a match for "
            f"your ZIP code."))

    if zips:
        shown = ", ".join(zips[:8])
        more = f", and {len(zips) - 8} more" if len(zips) > 8 else ""
        qa.append((
            f"What ZIP codes does this cover near {esc(city)}?",
            f"This map includes ZIP code{'s' if len(zips) != 1 else ''} {shown}{more} in and "
            f"around {esc(city)}. Search any of them above, or type your own ZIP to recenter "
            f"the map."))

    qa.append((
        f"What causes {problem} in {esc(city)}?",
        f"{esc(city)} sits in the {esc(region_label)} region, where the main driver is "
        f"{causes}"))

    if info.get("urgent"):
        emergency_note = (
            f" {open_now} of the {n} contractors listed near {esc(city)} are open 24 hours."
            if n and open_now else
            " Mention that it's urgent in your job request and we'll prioritize the match.")
        qa.append((
            f"How fast can someone respond to {problem} in {esc(city)}?",
            f"Most companies that offer {label.lower()} treat active water intrusion as an "
            f"emergency call and can respond same-day.{emergency_note}"))
    else:
        qa.append((
            f"How long does {label.lower()} take in {esc(city)}?",
            f"{info.get('duration', 'Timing depends on the scope of the job')}. Your matched "
            f"contractor will confirm an exact schedule during the free on-site estimate."))

    qa.append((
        f"Is {label.lower()} covered by a warranty in {esc(city)}?",
        info.get("warranty", "Ask any contractor you're considering exactly what their warranty "
                             "covers and whether it transfers if you sell the home.")))

    qa.append((
        f"How do I get a free {label.lower()} quote in {esc(city)}?",
        f"Use the map above or submit a job request with your ZIP code. We match you with a "
        f"licensed contractor covering {esc(city)}, and they contact you directly &mdash; "
        f"usually within 1&ndash;3 business days. There is no cost and no obligation."))

    return qa


def statewide_faq(svc, n_total, n_cities):
    """Per-page FAQ for a /find/<service>-va/ statewide page."""
    label = svc["label"]
    info = SERVICE_INFO.get(svc["find"], {})
    problem = PROBLEM_NOUN.get(svc["find"], f"{label.lower()} problems")
    rows = [p for p in PARTNERS if svc["cat"] in (p.get("cats") or [])]
    rated = [p for p in rows if p.get("rating")]
    avg = sum(p["rating"] for p in rated) / len(rated) if rated else 0

    qa = [
        (f"How much does {label.lower()} cost in Virginia?",
         f"Typical cost runs {info.get('cost', 'a few thousand dollars depending on scope')} "
         f"statewide. Prices vary by region and by how much excavation or structural work is "
         f"involved &mdash; the only accurate number comes from a free on-site inspection."),

        (f"How many {label.lower()} contractors are listed in Virginia?",
         f"We currently track {n_total} contractors offering {label.lower()} across "
         f"{n_cities} Virginia cities and towns."
         + (f" Of the {len(rated)} with a public Google rating, the average is {avg:.1f}&#9733;."
            if rated else "")),

        (f"What causes {problem} across Virginia?",
         f"Mostly {REGION_CAUSES_GENERIC} The specifics vary by region &mdash; coastal Hampton "
         f"Roads deals with a high water table, while the Shenandoah Valley's limestone bedrock "
         f"creates its own drainage quirks. Open the city-specific map below for detail on your area."),
    ]

    if info.get("urgent"):
        qa.append((
            f"Is {label.lower()} available as an emergency service?",
            "Yes &mdash; most companies offering this service treat active water intrusion as "
            "an emergency call. Note that it's urgent in your job request and we will "
            "prioritize the match."))
    else:
        qa.append((
            f"How long does {label.lower()} take?",
            f"{info.get('duration', 'Timing depends on the scope of the job')}. Your matched "
            f"contractor will confirm an exact schedule during the free on-site estimate."))

    qa.append((
        f"Is {label.lower()} covered by a warranty?",
        info.get("warranty", "Ask any contractor you're considering exactly what their warranty "
                             "covers and whether it transfers if you sell the home.")))

    qa.append((
        "How do I get a free quote?",
        "Search the map above by ZIP code, or submit a job request directly. We match you with "
        "a licensed contractor covering your area, and they contact you within 1&ndash;3 "
        "business days. There is no cost and no obligation."))

    return qa


def city_center(city_name):
    """Average the centroids of every ZIP mapped to this city."""
    pts = [CENTROIDS[z] for z, c in ZIP_CITY.items() if c == city_name and z in CENTROIDS]
    if not pts:
        pts = [[p["lat"], p["lng"]] for p in PARTNERS
               if p.get("city") == city_name and p.get("lat")]
    if not pts:
        return None
    return [round(sum(p[0] for p in pts) / len(pts), 5),
            round(sum(p[1] for p in pts) / len(pts), 5)]


def providers_near(center, cat, km=40):
    """Partners in `cat` within `km` of a point -- rough equirectangular distance."""
    if not center:
        return []
    out = []
    for p in PARTNERS:
        if not p.get("lat") or cat not in (p.get("cats") or []):
            continue
        dx = (p["lat"] - center[0]) * 111.0
        dy = (p["lng"] - center[1]) * 88.0
        if (dx * dx + dy * dy) ** 0.5 <= km:
            out.append(p)
    out.sort(key=lambda p: (-(p.get("rating") or 0), -(p.get("reviews") or 0)))
    return out


# ---------- page shell ----------
def page(title, desc, canonical, body, find_config=None, extra_head="", faq_qa=None):
    cfg = ""
    if find_config is not None:
        cfg = f"\n<script>window.FIND_CONFIG = {json.dumps(find_config)};</script>"
    schema = f"\n<script type=\"application/ld+json\">{faq_schema(faq_qa)}</script>" if faq_qa else ""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE}{canonical}">
<link rel="stylesheet" href="/css/styles.css">
{SEARCHMAP_HEAD}
{ADSENSE}{cfg}{extra_head}{schema}
</head>
<body>
{SITE_HEADER}
{body}
{SEARCHMAP_SCRIPTS}
{FOOTER}
'''


def hub_page(title, desc, canonical, body):
    """A /find/ hub -- no map, so no Leaflet payload."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE}{canonical}">
<link rel="stylesheet" href="/css/styles.css">
{ADSENSE}
</head>
<body>
{SITE_HEADER}
{body}
'''


def write(rel_dir, content):
    out = os.path.join(ROOT, rel_dir)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(content)


def provider_strip(rows, heading, empty_note):
    """Top-rated providers under the map -- real crawlable text on every page."""
    if not rows:
        return f'<p class="text-muted">{empty_note}</p>'
    cards = []
    for p in rows[:12]:
        stars = ""
        if p.get("rating"):
            full = int(round(p["rating"]))
            stars = ('<span class="stars">' + "★" * full + "☆" * (5 - full) + "</span> "
                     f'<span class="rating-num">{p["rating"]}</span>'
                     + (f' <span class="review-count">({p["reviews"]})</span>' if p.get("reviews") else ""))
        cards.append(
            f'''<div class="listing">
        <h3><a href="/partners/{esc(p["slug"])}/">{esc(p["name"])}</a></h3>
        <div class="meta">{esc(p.get("city") or "Virginia")}, VA</div>
        <div class="rating-line">{stars}</div>
        <div class="listing__foot"><a href="/get-a-quote/?provider={esc(p["slug"])}" class="btn btn--blue btn--block">Instant Free Quote</a></div>
      </div>''')
    return (f'<h2>{heading}</h2>\n<div class="listing-grid">\n      '
            + "\n      ".join(cards) + "\n    </div>")


# ---------- statewide service pages ----------
def build_statewide(svc, city_pages):
    label, find, cat = svc["label"], svc["find"], svc["cat"]
    url = f"/find/{find}-va/"
    legacy = LEGACY.get(svc["slug"], {})
    title = f"Find {label} Contractors in Virginia | Map Search"
    desc = legacy.get("description") or (
        f"Search every licensed {label.lower()} contractor in Virginia on an interactive map. "
        "Filter by ZIP code, compare ratings, and request a free estimate.")
    rows = [p for p in PARTNERS if cat in (p.get("cats") or [])]
    rows.sort(key=lambda p: (-(p.get("rating") or 0), -(p.get("reviews") or 0)))

    crumb = f'<div class="breadcrumb"><a href="/">Home</a> / <a href="/find/">Find</a> / {esc(label)}</div>'
    intro = (f"Every {esc(label.lower())} pro we track across the Commonwealth, plotted on one map. "
             "Search a ZIP code, switch to satellite, toggle city or ZIP borders, then send one "
             "free job request to the pros you like.")

    # city links for this service
    links = "".join(
        f'<a href="/find/{find}-{slug}-va/" class="city-chip">{esc(CITY_BY_SLUG[slug])}</a> '
        for slug in city_pages)
    by_city = (f'''
    <h2>Open the {esc(label)} Map for Your City</h2>
    <p>Each link opens this same searchmap already centred on that area:</p>
    <div class="city-chip-row">{links}</div>''' if links else "")

    strip = provider_strip(
        rows, f"Top-Rated {esc(label)} Pros in Virginia",
        "No providers are listed for this service yet &mdash; submit a job request "
        "and we&rsquo;ll match you manually.")

    qa = statewide_faq(svc, len(rows), len(city_pages))

    body = f'''<main>
{searchmap_section(f"Find {esc(label)} in Virginia", intro, crumb)}

<section class="section">
  <div class="container">
    {strip}
{by_city}
    <div style="margin-top:32px;">
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Instant Free Quote</a>
    </div>
  </div>
</section>

{legacy.get("body", "")}

<section class="section section--soft">
  <div class="container">
    {faq_html(qa)}
  </div>
</section>

<section class="section section--navy">
  <div class="container" style="text-align:center;">
    <h2>Instant Free Quote</h2>
    <p>Submit a job request and we&rsquo;ll connect you with the ideal licensed contractor for
       your situation. They&rsquo;ll reach out within 1&ndash;3 business days.</p>
    <a href="/get-a-quote/" class="btn btn--primary btn--lg">Instant Free Quote</a>
  </div>
</section>
</main>
'''
    cfg = {"cat": cat, "service": label, "scope": "va"}
    write(f"find/{find}-va", page(esc(title), esc(desc), url, body, cfg, faq_qa=qa))
    return url


# ---------- city service pages ----------
def build_city(svc, city_slug):
    label, find, cat = svc["label"], svc["find"], svc["cat"]
    city = CITY_BY_SLUG[city_slug]
    url = f"/find/{find}-{city_slug}-va/"
    center = city_center(city)
    rows = providers_near(center, cat)

    title = f"Find {label} in {city}, VA | Map Search"
    desc = (f"Interactive map of {label.lower()} contractors serving {city}, Virginia. "
            "Compare ratings, search nearby ZIP codes, and get a free estimate.")

    crumb = (f'<div class="breadcrumb"><a href="/">Home</a> / <a href="/find/">Find</a> / '
             f'<a href="/find/{find}-va/">{esc(label)}</a> / {esc(city)}</div>')
    intro = (f"{esc(label)} pros serving {esc(city)} and the surrounding ZIP codes, on the map below. "
             "Filter by service, search a neighbouring ZIP, then request a free estimate.")

    detail_url = f"/{city_slug}/{svc['slug']}/"
    has_detail = os.path.isdir(os.path.join(ROOT, city_slug, svc["slug"]))
    deep = (f'''
    <h2>More About {esc(label)} in {esc(city)}</h2>
    <p>Costs, warning signs, local soil and permitting notes, and the full contractor list for
       {esc(city)} are on the detail page:
       <a href="{detail_url}">{esc(label)} in {esc(city)}, VA &rarr;</a></p>''' if has_detail else "")

    others = [s for s in SERVICES
              if s[1] != find and os.path.isdir(os.path.join(ROOT, city_slug, s[0]))]
    other_links = "".join(
        f'<a href="/find/{f}-{city_slug}-va/" class="city-chip">{esc(l)}</a> '
        for _slug, f, l, _c in others)
    also = (f'''
    <h2>Other Services in {esc(city)}</h2>
    <div class="city-chip-row">{other_links}</div>''' if other_links else "")

    empty_note = (
        f"No {esc(label.lower())} pros are listed within 40&nbsp;km of {esc(city)} yet. "
        'Use the map to widen your search, or <a href="/get-a-quote/">submit a job request</a> '
        "and we&rsquo;ll match you manually.")
    strip = provider_strip(rows, f"Top-Rated {esc(label)} Pros Near {esc(city)}", empty_note)

    qa = city_faq(svc, city, city_slug, rows, center)

    body = f'''<main>
{searchmap_section(f"Find {esc(label)} in {esc(city)}, VA", intro, crumb)}

<section class="section">
  <div class="container">
    {strip}
{deep}
{also}
    <div style="margin-top:32px;">
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Instant Free Quote</a>
    </div>
  </div>
</section>

<section class="section section--soft">
  <div class="container">
    {faq_html(qa)}
  </div>
</section>
</main>
'''
    cfg = {"cat": cat, "service": label, "city": city, "scope": "city"}
    if center:
        cfg["center"] = center
        cfg["zoom"] = 11
    write(f"find/{find}-{city_slug}-va", page(esc(title), esc(desc), url, body, cfg, faq_qa=qa))
    return url, len(rows)


# ---------- hub ----------
def build_hub(statewide, city_map):
    rows = []
    for slug, find, label, cat in SERVICES:
        chips = "".join(
            f'<a href="/find/{find}-{cs}-va/" class="city-chip">{esc(CITY_BY_SLUG[cs])}</a> '
            for cs in city_map.get(find, []))
        rows.append(f'''<div class="find-group">
        <h3><a href="/find/{find}-va/">{esc(label)} &mdash; Statewide Map</a></h3>
        <div class="city-chip-row">{chips or '<span class="text-muted">Statewide map only</span>'}</div>
      </div>''')

    total = sum(len(v) for v in city_map.values()) + len(SERVICES)
    body = f'''<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / Find</div>
    <h1>Find a Waterproofing Pro in Virginia</h1>
    <p>{total} interactive searchmaps &mdash; one per service, one per service and city.
       Every map plots the licensed waterproofing, foundation, crawl space and restoration
       contractors we track, with ZIP search, ratings and a free job request built in.</p>
    <div style="margin-top:18px;">
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Instant Free Quote</a>
    </div>
  </div>
</div>

<main>
<section class="section">
  <div class="container">
    <p class="lead">Pick the service you need. Each statewide map covers all of Virginia;
       the city chips below it open a map already centred on that area.</p>
    <div class="find-groups">
      {"".join(rows)}
    </div>

    <h2 style="margin-top:2em;">Browse Another Way</h2>
    <ul>
      <li><a href="/partners/">All partner contractors</a> &mdash; the full directory in one table</li>
      <li><a href="/reviews/">Contractor reviews</a> &mdash; ratings and review counts, ranked</li>
      <li><a href="/virginia/">Browse by city</a> &mdash; city pages with local detail</li>
    </ul>
  </div>
</section>
</main>
'''
    write("find", hub_page(
        "Find Basement Waterproofing Contractors in Virginia | Map Search",
        "Interactive searchmaps for every basement waterproofing, foundation repair, "
        "crawl space and water damage service in Virginia. Search by ZIP, compare ratings, "
        "get a free estimate.",
        "/find/", body) + FOOTER)


def main():
    # which cities already have a page for each service
    city_map = {}
    for slug, find, label, cat in SERVICES:
        cities = sorted(cs for cs in CITY_BY_SLUG
                        if os.path.isdir(os.path.join(ROOT, cs, slug)))
        city_map[find] = cities

    urls = []
    for slug, find, label, cat in SERVICES:
        svc = {"slug": slug, "find": find, "label": label, "cat": cat}
        urls.append(build_statewide(svc, city_map[find]))

    empty = 0
    for slug, find, label, cat in SERVICES:
        svc = {"slug": slug, "find": find, "label": label, "cat": cat}
        for cs in city_map[find]:
            u, n = build_city(svc, cs)
            urls.append(u)
            if n == 0:
                empty += 1

    build_hub(urls, city_map)
    urls.append("/find/")

    with open(os.path.join(ROOT, "scripts", "find_urls.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, indent=1)

    print(f"Generated {len(urls)} /find/ pages "
          f"({len(SERVICES)} statewide, {len(urls) - len(SERVICES) - 1} city, 1 hub)")
    print(f"  {empty} city pages have no provider within 40km (map still works, "
          f"copy points to the job-request form)")


if __name__ == "__main__":
    main()
