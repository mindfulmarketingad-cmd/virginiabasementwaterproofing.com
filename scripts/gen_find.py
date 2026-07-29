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
def page(title, desc, canonical, body, find_config=None, extra_head=""):
    cfg = ""
    if find_config is not None:
        cfg = f"\n<script>window.FIND_CONFIG = {json.dumps(find_config)};</script>"
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
{ADSENSE}{cfg}{extra_head}
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
    write(f"find/{find}-va", page(esc(title), esc(desc), url, body, cfg))
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
</main>
'''
    cfg = {"cat": cat, "service": label, "city": city, "scope": "city"}
    if center:
        cfg["center"] = center
        cfg["zoom"] = 11
    write(f"find/{find}-{city_slug}-va", page(esc(title), esc(desc), url, body, cfg))
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
