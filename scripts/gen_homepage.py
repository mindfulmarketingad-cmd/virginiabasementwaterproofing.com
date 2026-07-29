#!/usr/bin/env python3
"""Rebuild index.html as a full landing page.

Structure follows the pattern that works for this vertical: searchmap hero ->
ZIP capture -> proof -> symptoms -> causes -> solutions -> services -> coverage
-> FAQ -> why us -> CTA.

Everything quantitative is computed from data/partners.json at build time, so
the stat strip and the featured-contractor grid can never drift from reality.

Two deliberate omissions:
  * No phone number anywhere -- every CTA is the site's own lead form.
  * No invented homeowner testimonials. The previous homepage carried three
    fabricated quotes with fake names and cities; they are gone. The proof
    block now uses the real aggregate Google rating data instead.
"""
import os, sys, json, html
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_html import (  # noqa: E402
    SITE_HEADER, FOOTER, SERVICES, SEARCHMAP_HEAD, SEARCHMAP_SCRIPTS)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.virginiabasementwaterproofing.org"
ADSENSE = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
           '?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>')


def esc(s):
    return html.escape(str(s or ""), quote=True)


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


PARTNERS = load("data/partners.json")
CITY_URLS = load("scripts/city_urls.json")
CITY_SLUG = {n: u.strip("/").split("/")[-1] for n, u in CITY_URLS.items()}

# ---------------------------------------------------------------- real numbers
RATED = [p for p in PARTNERS if p.get("rating")]
TOTAL_REVIEWS = sum(p.get("reviews") or 0 for p in PARTNERS)
AVG = sum(p["rating"] for p in RATED) / len(RATED) if RATED else 0
CITIES = sorted({p["city"] for p in PARTNERS if p.get("city")})
TOP_RATED = sorted(
    [p for p in RATED if (p.get("reviews") or 0) >= 25],
    key=lambda p: (-(p["rating"]), -(p.get("reviews") or 0)))
FOUR_EIGHT = sum(1 for p in RATED if p["rating"] >= 4.8)
CITY_COUNT = Counter(p["city"] for p in PARTNERS if p.get("city"))


def stars(rating):
    full = max(0, min(5, int(round(rating or 0))))
    return "★" * full + "☆" * (5 - full)


# ---------------------------------------------------------------- content data
SYMPTOMS = [
    ("Musty Smells", "M4 20h16M6 20V9l6-5 6 5v11M9 20v-5h6v5",
     "That damp-earth odour is airborne mould spores and decaying organic matter. "
     "You smell a moisture problem long before you can see one."),
    ("Moldy Walls", "M5 19h14M7 19V8m10 11V8M4 8h16L12 3z",
     "Black, green or white growth on block, drywall or joists. Mould needs only "
     "moisture and something organic to eat, and a damp basement supplies both."),
    ("Wet Walls", "M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z",
     "Beads, streaks or dark patches after rain mean water is coming through the "
     "wall itself &mdash; usually at the cove joint, a crack, or a tie rod hole."),
    ("White Chalky Residue", "M4 18h16M4 14h16M4 10h16M4 6h16",
     "Efflorescence: mineral salt left behind as water evaporates out of concrete. "
     "It is proof water is actively moving through the masonry."),
    ("High Humidity", "M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z M9 13h6",
     "Above 60% relative humidity you get condensation, rust, warped wood and "
     "mould &mdash; without a single visible drop of water."),
    ("Standing Water", "M3 15c3 0 3 2 6 2s3-2 6-2 3 2 6 2M3 10c3 0 3 2 6 2s3-2 6-2 3 2 6 2",
     "Puddles or a flooded floor after heavy rain. At this point the water table "
     "or the drainage around your footing has already been overwhelmed."),
]

SOLUTIONS = [
    ("Control Wall Moisture",
     "Stop water and vapour moving through the foundation wall itself.",
     ["Inspect the full wall perimeter for cracks, cove-joint seepage and tie-rod holes",
      "Take moisture and relative-humidity readings rather than guessing",
      "Seal active cracks from the inside, or excavate and membrane from the outside",
      "Fit a wall vapour barrier that drains to the perimeter system"],
     ["Vapour barrier", "Polyurethane injection", "Epoxy injection", "Exterior membrane",
      "Dimple board / drainage mat"]),
    ("Control Groundwater Seepage",
     "Give the water somewhere to go before it reaches the slab.",
     ["Trace where the water actually enters &mdash; source first, symptom second",
      "Check footing drains, downspout discharge and grading around the house",
      "Install interior drain tile or an exterior French drain to intercept it",
      "Add a pump with a battery backup so a storm outage is not a flood"],
     ["Interior drain tile", "French drain", "Sump pump", "Battery backup pump",
      "Discharge line extension"]),
    ("Control the Environment",
     "Keep the space dry once the water is handled, so mould never restarts.",
     ["Measure relative humidity across seasons, not on one dry afternoon",
      "Encapsulate the crawl space and seal vents where appropriate",
      "Dehumidify to hold humidity below the mould threshold",
      "Insulate rim joists and ducting to stop condensation forming"],
     ["Crawl space encapsulation", "Commercial dehumidifier", "Rim joist insulation",
      "Thermal dry flooring", "Sealed vent covers"]),
]

WHY = [
    ("One form, not ten phone calls",
     "Describe the job once. We identify the contractor best matched to your service "
     "type, location and project scope, and they contact you &mdash; you are not "
     "chasing quotes across a dozen websites."),
    ("Ratings you can check yourself",
     f"Every listing shows the real Google rating and review count, and links "
     f"straight to the reviews. We publish {TOTAL_REVIEWS:,} reviews' worth of data "
     "across the directory and we do not write any of it ourselves."),
    ("Statewide, not one branch",
     f"{len(PARTNERS)} contractors across {len(CITIES)} Virginia cities, from Hampton "
     "Roads to the Shenandoah Valley and Southwest Virginia. If someone works in your "
     "ZIP code, they are on the map."),
    ("Free, with no obligation",
     "The matching service costs homeowners nothing and you are never committed to "
     "hiring anyone. Take the estimate, compare it, walk away if it is wrong."),
]

FAQS = [
    ("How much does basement waterproofing cost in Virginia?",
     "Interior drainage systems typically run $3,000&ndash;$9,000. Exterior waterproofing "
     "runs $8,000&ndash;$15,000 or more because it involves excavation. Sump pump "
     "installation is usually $1,000&ndash;$3,500, and crack injection $500&ndash;$1,500 "
     "per crack. These are informational ranges, not quotes &mdash; the only accurate "
     "number comes from an on-site inspection."),
    ("Is this service really free?",
     "Yes. Homeowners pay nothing to use the directory or to be matched with a contractor, "
     "and there is no obligation to hire whoever contacts you."),
    ("How quickly will a contractor get in touch?",
     "Most matched contractors reach out within 1&ndash;3 business days to arrange a free "
     "on-site estimate. If your basement is actively flooding, say so in the job request "
     "&mdash; a good number of the companies listed here run 24/7 emergency response."),
    ("Do you do the waterproofing work yourselves?",
     "No. We are a directory and lead-referral service, not a licensed contractor. Every "
     "company listed is an independent business, and we make no warranty about anyone's "
     "workmanship. Always verify licensing and insurance before hiring."),
    ("Why is my basement wet only after heavy rain?",
     "That pattern usually points to surface water rather than a high water table: "
     "downspouts discharging next to the foundation, grading that slopes toward the house, "
     "or a footing drain that has silted up. It is often the cheapest category of problem "
     "to fix, which is why the diagnosis matters more than the product."),
    ("Does a dehumidifier fix a wet basement?",
     "It manages humidity; it does not stop water entering. If you have active seepage, a "
     "dehumidifier treats the symptom while the wall keeps getting wet. Fix the water path "
     "first, then dehumidify to hold the space below the mould threshold."),
    ("How do I know which contractor to pick?",
     "Get at least two itemised written quotes for the same scope, check the licence with "
     "the Virginia DPOR, ask for a current certificate of insurance, and read the most "
     "recent reviews rather than the lifetime average. Ask what the warranty covers and "
     "whether it transfers when you sell."),
    ("What areas of Virginia do you cover?",
     f"All of it. The directory currently lists {len(PARTNERS)} contractors across "
     f"{len(CITIES)} cities and towns, covering Hampton Roads, Northern Virginia, Greater "
     "Richmond, Central Virginia, the Shenandoah Valley and Western Virginia."),
]


# ---------------------------------------------------------------- sections
def stats_strip():
    return f'''<section class="section section--navy" style="padding:44px 0;">
  <div class="container">
    <div class="stats">
      <div><div class="num">{len(PARTNERS)}</div><div class="lbl">Contractors Listed</div></div>
      <div><div class="num">{len(CITIES)}</div><div class="lbl">Virginia Cities Covered</div></div>
      <div><div class="num">{TOTAL_REVIEWS:,}</div><div class="lbl">Google Reviews Indexed</div></div>
      <div><div class="num">{AVG:.1f}&#9733;</div><div class="lbl">Average Contractor Rating</div></div>
    </div>
  </div>
</section>'''


def zip_bar():
    return '''<section class="zip-bar">
  <div class="container zip-bar__inner">
    <div class="zip-bar__copy">
      <h2>Get started with a free inspection</h2>
      <p>Enter your ZIP code and we&rsquo;ll match you with a licensed pro who covers it.</p>
    </div>
    <form class="zip-bar__form" action="/get-a-quote/" method="get">
      <label class="sr-only" for="heroZip">ZIP code</label>
      <input type="text" id="heroZip" name="zip" inputmode="numeric" maxlength="5"
             pattern="[0-9]{5}" placeholder="Enter ZIP code" required>
      <button type="submit" class="btn btn--primary">Instant Free Quote</button>
    </form>
  </div>
</section>'''


def proof_block():
    cards = []
    for p in TOP_RATED[:6]:
        photo = p.get("photo") or p.get("street_view")
        img = (f'<img class="pro-card__img" src="{esc(photo)}" alt="{esc(p["name"])}" '
               f'loading="lazy" decoding="async" referrerpolicy="no-referrer" '
               f'onerror="this.remove()">' if photo else "")
        svcs = "".join(f'<span class="svc-tag">{esc(s)}</span>'
                       for s in (p.get("cat_labels") or [])[:2])
        cards.append(f'''<article class="pro-card">
        {img}
        <div class="pro-card__body">
          <h3><a href="/partners/{esc(p["slug"])}/">{esc(p["name"])}</a></h3>
          <div class="meta">{esc(p.get("city") or "Virginia")}, VA</div>
          <div class="rating-line"><span class="stars">{stars(p["rating"])}</span>
            <span class="rating-num">{p["rating"]:.1f}</span>
            <span class="review-count">({p.get("reviews", 0):,} reviews)</span></div>
          <div class="listing__services">{svcs}</div>
          <a href="/reviews/{esc(p["slug"])}/" class="pro-card__link">Read the reviews &rarr;</a>
        </div>
      </article>''')

    return f'''<section class="section section--soft">
  <div class="container">
    <div class="center">
      <span class="eyebrow">Rated by real customers</span>
      <h2>Highly Rated Across Virginia</h2>
      <p class="lead">We do not write reviews and we do not sell placement. Every rating on this
         site is the contractor&rsquo;s own public Google score, and every listing links straight
         to the source so you can check it yourself.</p>
    </div>

    <div class="proof-row">
      <div class="proof-stat">
        <div class="proof-stat__num">{AVG:.1f}</div>
        <div class="stars">{stars(AVG)}</div>
        <div class="proof-stat__lbl">Average rating across {len(RATED)} rated contractors</div>
      </div>
      <div class="proof-stat">
        <div class="proof-stat__num">{TOTAL_REVIEWS:,}</div>
        <div class="proof-stat__lbl">Google reviews behind those ratings</div>
      </div>
      <div class="proof-stat">
        <div class="proof-stat__num">{FOUR_EIGHT}</div>
        <div class="proof-stat__lbl">Contractors rated 4.8&#9733; or higher</div>
      </div>
    </div>

    <h3 class="center" style="margin-top:40px;">Top-Rated Pros Right Now</h3>
    <div class="pro-grid">{"".join(cards)}</div>
    <div class="center" style="margin-top:30px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
      <a href="/reviews/" class="btn btn--ghost">Compare All {len(PARTNERS)} Contractors by Rating</a>
      <a href="/partners/" class="btn btn--ghost">Browse the Full Directory</a>
    </div>
  </div>
</section>'''


def symptoms_block():
    tiles = []
    for title, path, body in SYMPTOMS:
        tiles.append(f'''<div class="symptom">
        <div class="symptom__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
               stroke-linecap="round" stroke-linejoin="round"><path d="{path}"/></svg>
        </div>
        <h3>{esc(title)}</h3>
        <p>{body}</p>
      </div>''')
    return f'''<section class="section">
  <div class="container">
    <div class="center">
      <span class="eyebrow">Know the signs</span>
      <h2>Types of Basement Damage in Virginia Homes</h2>
      <p class="lead">Six symptoms worth acting on. Every one of them is a moisture problem
         showing itself in a different way &mdash; and every one gets more expensive the longer
         it runs.</p>
    </div>
    <div class="symptom-grid">{"".join(tiles)}</div>
  </div>
</section>'''


def causes_block():
    return '''<section class="section section--soft">
  <div class="container">
    <div class="prose" style="max-width:820px;margin:0 auto;">
      <h2>Common Causes of Basement Problems in Virginia</h2>
      <p>Virginia sits on a lot of clay. Clay expands when it takes on water and contracts as it
         dries, and that cycle pushes against foundation walls and footings year after year. Add
         the Commonwealth&rsquo;s rainfall pattern &mdash; long wet stretches, then tropical
         systems that dump several inches in a day &mdash; and you get soil that is saturated far
         more often than the foundation was designed for.</p>
      <p>Saturated soil creates hydrostatic pressure: the weight of water in the ground pressing
         against everything below grade. Water does not need a large opening. It will find the
         cove joint where the wall meets the slab, a hairline shrinkage crack, a tie-rod hole, or
         a porous block core, and it will move through all of them. This is why patching the
         visible damp patch so rarely holds &mdash; the pressure simply finds the next weakest
         point along the wall.</p>
      <p>Just as often, the cause is above ground and much cheaper to fix. Downspouts that
         discharge a foot from the foundation, grading that slopes back toward the house, a
         footing drain that silted up two decades ago, or a driveway that channels runoff at the
         wall. A contractor who quotes a full interior drainage system without first checking
         your gutters and grading is selling you a product rather than diagnosing a problem.</p>
      <p>The practical consequence: judge quotes on the diagnosis, not the hardware. Ask where
         the water is coming from and how they established it. Two contractors proposing different
         systems for the same basement usually disagree about the source, and that is the
         conversation worth having before you sign anything.</p>
    </div>
  </div>
</section>'''


def solutions_block():
    groups = []
    for title, sub, doing, using in SOLUTIONS:
        bullets = "".join(f"<li>{b}</li>" for b in doing)
        chips = "".join(f'<span class="city-chip">{esc(u)}</span>' for u in using)
        groups.append(f'''<div class="solution">
        <div class="solution__head">
          <h3>{esc(title)}</h3>
          <p>{esc(sub)}</p>
        </div>
        <div class="solution__cols">
          <div>
            <h4>What a good contractor does</h4>
            <ul>{bullets}</ul>
          </div>
          <div>
            <h4>What they typically install</h4>
            <div class="city-chip-row">{chips}</div>
          </div>
        </div>
      </div>''')
    return f'''<section class="section">
  <div class="container">
    <div class="center">
      <span class="eyebrow">How it gets fixed</span>
      <h2>Waterproofing Solutions Virginia Pros Provide</h2>
      <p class="lead">Nearly every basement job falls into one of three buckets. Knowing which one
         you are buying makes it much harder to be oversold.</p>
    </div>
    <div class="solution-list">{"".join(groups)}</div>
  </div>
</section>'''


def services_block():
    tiles = []
    for slug, find, label, cat in SERVICES:
        n = sum(1 for p in PARTNERS if cat in (p.get("cats") or []))
        tiles.append(f'''<a class="svc-tile" href="/find/{find}-va/">
        <strong>{esc(label)}</strong>
        <span>{n} contractor{"s" if n != 1 else ""} on the map</span>
      </a>''')
    return f'''<section class="section section--soft">
  <div class="container">
    <div class="center">
      <span class="eyebrow">Every service</span>
      <h2>Find the Right Kind of Pro</h2>
      <p class="lead">Each link opens a live searchmap filtered to that service, with ZIP search
         and ratings built in.</p>
    </div>
    <div class="svc-tiles">{"".join(tiles)}</div>
  </div>
</section>'''


def coverage_block():
    top = [c for c, _n in CITY_COUNT.most_common(28)]
    chips = []
    for c in sorted(top):
        cslug = CITY_SLUG.get(c)
        href = (f"/find/waterproofing-{cslug}-va/"
                if cslug and os.path.isdir(os.path.join(ROOT, "find", f"waterproofing-{cslug}-va"))
                else CITY_URLS.get(c, "/virginia/"))
        chips.append(f'<a href="{href}" class="city-chip">{esc(c)} '
                     f'<span class="city-chip__n">{CITY_COUNT[c]}</span></a>')
    regions = [("Hampton Roads", "/virginia/hampton-roads/"),
               ("Northern Virginia", "/virginia/northern-virginia/"),
               ("Greater Richmond", "/virginia/richmond/"),
               ("Central Virginia", "/virginia/central-virginia/"),
               ("Shenandoah Valley", "/virginia/shenandoah-valley/"),
               ("Western Virginia", "/virginia/western-virginia/")]
    rlinks = "".join(f'<a href="{u}" class="city-chip">{esc(r)}</a> ' for r, u in regions)
    return f'''<section class="section">
  <div class="container">
    <div class="center">
      <span class="eyebrow">Where we cover</span>
      <h2>Serving Homeowners Across the Commonwealth</h2>
      <p class="lead">{len(PARTNERS)} contractors across {len(CITIES)} Virginia cities and towns.
         The number beside each city is how many are listed there.</p>
    </div>
    <h3 style="margin-top:30px;">By Region</h3>
    <div class="city-chip-row">{rlinks}</div>
    <h3 style="margin-top:26px;">Busiest Cities</h3>
    <div class="city-chip-row">{" ".join(chips)}</div>
    <div class="center" style="margin-top:28px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">
      <a href="/find/" class="btn btn--ghost">All Searchmaps</a>
      <a href="/virginia/" class="btn btn--ghost">All Virginia Cities</a>
    </div>
  </div>
</section>'''


def why_block():
    cards = "".join(f'''<div class="why-card">
        <h3>{esc(t)}</h3>
        <p>{b}</p>
      </div>''' for t, b in WHY)
    return f'''<section class="section section--soft">
  <div class="container">
    <div class="center">
      <span class="eyebrow">Why use this directory</span>
      <h2>Why Virginia Homeowners Start Here</h2>
    </div>
    <div class="why-grid">{cards}</div>
  </div>
</section>'''


def faq_block():
    items = "".join(f'''<details class="faq-acc">
        <summary>{esc(q)}</summary>
        <div class="faq-acc__body"><p>{a}</p></div>
      </details>''' for q, a in FAQS)
    schema = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer",
                                                 "text": html.unescape(a)}}
                             for q, a in FAQS]}
    return f'''<section class="section">
  <div class="container" style="max-width:860px;">
    <div class="center">
      <span class="eyebrow">Questions</span>
      <h2>Basement Waterproofing FAQs</h2>
    </div>
    <div class="faq-accordion">{items}</div>
  </div>
</section>''', json.dumps(schema)


def final_cta():
    return '''<section class="section">
  <div class="container">
    <div class="cta-band">
      <h2>Ready to Get Matched?</h2>
      <p>Submit your job request and we&rsquo;ll identify the best-fit licensed contractor in your
         area. They&rsquo;ll reach out within 1&ndash;3 business days with a free, no-obligation
         estimate. The matching service is completely free to homeowners.</p>
      <form class="zip-bar__form zip-bar__form--center" action="/get-a-quote/" method="get">
        <label class="sr-only" for="ctaZip">ZIP code</label>
        <input type="text" id="ctaZip" name="zip" inputmode="numeric" maxlength="5"
               pattern="[0-9]{5}" placeholder="Enter ZIP code" required>
        <button type="submit" class="btn btn--primary btn--lg">Instant Free Quote</button>
      </form>
    </div>
  </div>
</section>'''


# ---------------------------------------------------------------- hero
def hero():
    return f'''<section class="map-hero">
  <div class="map-hero__bar">
    <div class="container">
      <h1>Find Basement Waterproofing Contractors in Virginia</h1>
      <p>Every licensed waterproofing, foundation, crawl space and restoration pro we track across
         the Commonwealth &mdash; {len(PARTNERS)} companies in {len(CITIES)} cities, plotted on one
         map with their real Google ratings. Search your ZIP, filter by the service you need, then
         send one free job request and let the right contractor come to you.</p>
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


def main():
    faq_html, faq_schema = faq_block()

    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Virginia Basement Waterproofing",
        "alternateName": "VirginiaBasementWaterproofing.org",
        "description": ("Free statewide directory connecting Virginia homeowners with licensed, "
                        "insured basement waterproofing, foundation repair, crawl space, and "
                        "water damage restoration contractors."),
        "url": f"{BASE}/",
        "logo": f"{BASE}/favicon.svg",
        "areaServed": {"@type": "State", "name": "Virginia"},
    }
    website = {
        "@context": "https://schema.org", "@type": "WebSite", "url": f"{BASE}/",
        "name": "Virginia Basement Waterproofing",
        "potentialAction": {"@type": "SearchAction",
                            "target": f"{BASE}/find/?zip={{search_term_string}}",
                            "query-input": "required name=search_term_string"},
    }

    desc = (f"Compare {len(PARTNERS)} licensed Virginia basement waterproofing, foundation repair "
            f"and crawl space contractors on one map. Real Google ratings, "
            f"{TOTAL_REVIEWS:,} reviews, free no-obligation estimates.")

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Virginia Basement Waterproofing | Compare {len(PARTNERS)} Local Contractors Free</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="Virginia Basement Waterproofing Contractors">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}/">
<meta property="og:site_name" content="Virginia Basement Waterproofing">
<link rel="stylesheet" href="/css/styles.css">
{SEARCHMAP_HEAD}
{ADSENSE}
<script type="application/ld+json">{json.dumps(org)}</script>
<script type="application/ld+json">{json.dumps(website)}</script>
<script type="application/ld+json">{faq_schema}</script>
</head>
<body>
{SITE_HEADER}

<main>

{hero()}

{zip_bar()}

{stats_strip()}

{proof_block()}

{symptoms_block()}

{causes_block()}

{solutions_block()}

{services_block()}

{coverage_block()}

{why_block()}

{faq_html}

{final_cta()}

</main>
{SEARCHMAP_SCRIPTS}
{FOOTER}
'''
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    text = html.unescape(__import__("re").sub(r"<[^>]+>", " ", page))
    print(f"Wrote index.html  ({len(page):,} bytes, ~{len(text.split()):,} words)")
    print(f"  stats from live data: {len(PARTNERS)} contractors, {len(CITIES)} cities, "
          f"{TOTAL_REVIEWS:,} reviews, {AVG:.1f} avg")


if __name__ == "__main__":
    main()
