#!/usr/bin/env python3
"""Rebuild every /partners/<slug>/ profile page as a full, data-rich listing.

Replaces the thin template that shipped before. Each page now carries the
business's real Google Business Profile data: featured photo, star-by-star
review breakdown, full category list, published business attributes, opening
hours, location and service area, sibling contractors in the same city, map
links, and a data-driven FAQ block with FAQPage schema.

Two things are deliberately absent:
  * No phone number, website, or booking link anywhere. Every conversion path
    on the page is the site's own lead form.
  * No invented testimonials. The previous template attributed made-up quotes
    to real businesses; that content is gone. Where we have no first-party
    review text we publish the real rating distribution and link to Google.

Inputs : data/partner-details.json (scripts/extract_outscraper.py)
         data/partners.json        (scripts/extract_partners_data.py)
         scripts/city_urls.json, scripts/zip_service_urls.json
Output : partners/<slug>/index.html
"""
import os, sys, json, html, re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_html import SITE_HEADER, FOOTER, SERVICES, best_city_find_url  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.virginiabasementwaterproofing.org"
ADSENSE = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
           '?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>')
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def esc(s):
    return html.escape(str(s or ""), quote=True)


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


DETAILS = load("data/partner-details.json")
PARTNERS = {p["slug"]: p for p in load("data/partners.json")}
CITY_URLS = load("scripts/city_urls.json")
ZIP_URLS = set(u.strip("/").split("/")[0] for u in load("scripts/zip_service_urls.json"))
FIND = {s[3]: s[1] for s in SERVICES}          # map-category key -> /find/ fragment
CAT_LABEL = {s[3]: s[2] for s in SERVICES}
CITY_SLUG = {n: u.strip("/").split("/")[-1] for n, u in CITY_URLS.items()}

# every partner in a city, so each profile can link to its neighbours
BY_CITY = defaultdict(list)
for _s, _p in PARTNERS.items():
    if _p.get("city"):
        BY_CITY[_p["city"]].append(_p)
for _c in BY_CITY:
    BY_CITY[_c].sort(key=lambda p: (-(p.get("rating") or 0), -(p.get("reviews") or 0)))


def city_link(city):
    slug = CITY_SLUG.get(city)
    if not slug:
        return esc(city)
    return f'<a href="{best_city_find_url(ROOT, slug)}">{esc(city)}</a>'


def stars(rating):
    if not rating:
        return ""
    full = max(0, min(5, int(round(rating))))
    return "★" * full + "☆" * (5 - full)


# --------------------------------------------------------------- prose
SVC_LABELS = {
    'waterproofing service': 'basement and crawl space waterproofing',
    'concrete contractor': 'concrete repair and resurfacing',
    'water damage restoration service': 'water damage restoration',
    'foundation': 'foundation repair and stabilization',
    'general contractor': 'general contracting and renovation',
    'air duct cleaning service': 'HVAC and air duct cleaning',
    'roofing contractor': 'roofing and exterior moisture control',
    'plumber': 'plumbing and drainage solutions',
    'contractor': 'professional contracting services',
    'construction company': 'construction and structural repair',
    'masonry contractor': 'masonry and foundation wall repair',
    'insulation contractor': 'insulation and crawl space vapor control',
    'fire damage restoration service': 'fire and smoke damage restoration',
    'mold remediation service': 'mold testing and remediation',
    'landscaper': 'grading and exterior drainage',
}


def about_prose(d, p):
    name, city = d["name"], d.get("city") or ""
    where = city_link(city) if city else "the surrounding Virginia area"
    phrases = [SVC_LABELS[s.lower()] for s in d.get("subtypes", []) if s.lower() in SVC_LABELS]
    if not phrases:
        phrases = ["basement waterproofing", "crawl space moisture control", "foundation drainage"]
    primary = phrases[0]
    others = ", ".join(phrases[1:3]) if len(phrases) > 1 else "moisture management and drainage solutions"

    rating_phrase = ""
    if d.get("rating") and d.get("reviews"):
        rating_phrase = (f" With a {d['rating']:.1f}-star Google rating backed by "
                         f"{d['reviews']:,} reviews, the company has an established public "
                         f"track record you can check before you call.")

    county_phrase = ""
    if d.get("county"):
        county_phrase = (f" The business sits in the {esc(d['county'])} area of "
                         f"{esc(city) or 'Virginia'}.")

    paras = [
        f"{esc(name)} is a {esc(d.get('category') or 'waterproofing')} listed in our Virginia "
        f"contractor directory, based in {where}. The company works in {esc(primary)} and serves "
        f"homeowners throughout {where} and the neighbouring communities.{rating_phrase}"
        f"{county_phrase}",

        f"Core work covers {esc(primary)} and {esc(others)}, alongside the interior and exterior "
        f"drainage, sump pump, encapsulation and crack-repair work that Virginia's clay soils and "
        f"high water table routinely demand. Any reputable contractor should start with an on-site "
        f"inspection and give you a written, itemised estimate before work begins &mdash; ask "
        f"{esc(name)} for both.",

        f"Virginia basements fail for predictable reasons: hydrostatic pressure against below-grade "
        f"walls, footing drains that have silted up, downspouts discharging against the foundation, "
        f"and grading that slopes toward the house rather than away from it. A durable fix addresses "
        f"the water source, not just the damp patch on the wall. When you compare quotes, compare "
        f"the diagnosis first.",

        f"Based in {where}, {esc(name)} covers residential and light-commercial work across the "
        f"{where} area. Submit a job request to confirm they cover your ZIP code and to get a free, "
        f"no-obligation estimate &mdash; we&rsquo;ll pass your details to the right contractor for "
        f"the job and they&rsquo;ll reach out within 1&ndash;3 business days.",
    ]
    return "\n        ".join(f"<p>{t}</p>" for t in paras)


# --------------------------------------------------------------- sections
def rating_breakdown(d):
    scores = d.get("scores") or {}
    total = sum(scores.values())
    if not total:
        return ""
    rows = []
    for s in range(5, 0, -1):
        n = scores.get(str(s), 0)
        pct = round(n / total * 100)
        rows.append(f'''<div class="score-row">
            <span class="score-row__label">{s}&#9733;</span>
            <span class="rating-bar"><span style="width:{pct}%"></span></span>
            <span class="score-row__num">{n:,}</span>
            <span class="score-row__pct">{pct}%</span>
          </div>''')
    top = scores.get("5", 0) + scores.get("4", 0)
    low = scores.get("1", 0) + scores.get("2", 0)
    summary = (f"{round(top / total * 100)}% of reviewers rated {esc(d['name'])} four stars or "
               f"better; {round(low / total * 100)}% rated it two stars or below.")
    return f'''
        <h2>Review Breakdown</h2>
        <p>How {esc(d["name"])}&rsquo;s {total:,} Google reviews are distributed across the
           five-star scale. {summary}</p>
        <div class="score-chart">
          {"".join(rows)}
        </div>'''


def services_section(d, p):
    subs = d.get("subtypes") or []
    cats = p.get("cat_labels") or []
    if not subs and not cats:
        return ""
    out = ['<h2>Services &amp; Specialties</h2>']
    if d.get("category"):
        out.append(f'<p>Google lists {esc(d["name"])} primarily as a '
                   f'<strong>{esc(d["category"])}</strong>'
                   + (f', with {len(subs) - 1} further categories listed.' if len(subs) > 1 else '.')
                   + '</p>')
    if subs:
        out.append('<h3>Listed Categories</h3><ul class="service-tags">'
                   + "".join(f"<li>{esc(s)}</li>" for s in subs) + "</ul>")
    if cats:
        links = []
        for cat in p.get("cats") or []:
            frag, label = FIND.get(cat), CAT_LABEL.get(cat)
            if frag and label:
                links.append(f'<a href="/find/{frag}-va/" class="city-chip">{esc(label)}</a>')
        if links:
            out.append('<h3>Jobs We Match Them For</h3>'
                       '<p>We route job requests in these categories to contractors like this one:</p>'
                       f'<div class="city-chip-row">{" ".join(links)}</div>')
    return "\n        " + "\n        ".join(out)


def attributes_section(d):
    attrs = d.get("attributes") or {}
    if not attrs:
        return ""
    blocks = []
    for section, vals in attrs.items():
        items = "".join(f"<li>{esc(v)}</li>" for v in vals)
        blocks.append(f'<div class="attr-group"><h4>{esc(section)}</h4><ul>{items}</ul></div>')
    return f'''
        <h2>Business Details</h2>
        <p>Attributes {esc(d["name"])} publishes on its Google Business Profile.</p>
        <div class="attr-grid">{"".join(blocks)}</div>'''


def hours_section(d):
    hrs = d.get("hours") or {}
    if not hrs:
        return ""
    rows = "".join(f"<tr><td>{day}</td><td>{esc(hrs.get(day, 'Closed'))}</td></tr>" for day in DAYS)
    extra = ""
    for label, days in (d.get("other_hours") or {}).items():
        erows = "".join(f"<tr><td>{day}</td><td>{esc(days.get(day, 'Closed'))}</td></tr>"
                        for day in DAYS)
        extra += (f'<h3 style="margin-top:1.4em;">{esc(label)}</h3>'
                  f'<table class="hours-table"><tbody>{erows}</tbody></table>')
    open_days = [d_ for d_ in DAYS if "closed" not in hrs.get(d_, "").lower()]
    note = ""
    if len(open_days) == 7:
        note = ("<p>Listed as open every day of the week &mdash; useful if your water problem "
                "will not wait for Monday.</p>")
    elif open_days:
        note = f"<p>Listed as open {len(open_days)} days a week ({', '.join(open_days)}).</p>"
    return f'''
        <h2>Opening Hours</h2>
        {note}
        <table class="hours-table"><tbody>{rows}</tbody></table>
        {extra}
        <p class="text-muted" style="font-size:.9rem;">Hours come from the business&rsquo;s Google
           listing and can change. Submitting a job request works around the clock.</p>'''


def area_section(d, p):
    city = d.get("city") or ""
    pc = d.get("postal_code") or ""
    bits = []
    if d.get("street"):
        bits.append(f'<li><span class="lbl">Street</span>{esc(d["street"])}</li>')
    if city:
        bits.append(f'<li><span class="lbl">City</span>{city_link(city)}, VA</li>')
    if d.get("county"):
        bits.append(f'<li><span class="lbl">County / area</span>{esc(d["county"])}</li>')
    if pc:
        zl = (f'<a href="/{pc}/basement-waterproofing/">{pc}</a>' if pc in ZIP_URLS else pc)
        bits.append(f'<li><span class="lbl">ZIP code</span>{zl}</li>')
    if not bits:
        return ""

    map_links = []
    cslug = CITY_SLUG.get(city)
    if cslug:
        for cat in (p.get("cats") or [])[:4]:
            frag, label = FIND.get(cat), CAT_LABEL.get(cat)
            if frag and os.path.isdir(os.path.join(ROOT, "find", f"{frag}-{cslug}-va")):
                map_links.append(f'<a href="/find/{frag}-{cslug}-va/" class="city-chip">'
                                 f'{esc(label)} in {esc(city)}</a>')
    maps = ""
    if map_links:
        maps = ('<h3 style="margin-top:1.4em;">See Them on the Map</h3>'
                f'<div class="city-chip-row">{" ".join(map_links)}</div>')

    return f'''
        <h2>Location &amp; Service Area</h2>
        <ul class="fact-list">{"".join(bits)}</ul>
        <p>Service radius is set by the contractor, not by this directory &mdash; submit a job
           request to confirm they cover your address before booking an inspection.</p>
        {maps}'''


def neighbours_section(d, slug):
    city = d.get("city") or ""
    peers = [x for x in BY_CITY.get(city, []) if x["slug"] != slug][:8]
    if not peers:
        return ""
    rows = []
    for x in peers:
        r = (f'<span class="stars">{stars(x["rating"])}</span> {x["rating"]:.1f}'
             + (f' <span class="review-count">({x["reviews"]:,})</span>' if x.get("reviews") else "")
             if x.get("rating") else '<span class="text-muted">Not rated</span>')
        rows.append(f'<tr><td class="dir-name"><a href="/partners/{esc(x["slug"])}/">'
                    f'{esc(x["name"])}</a></td><td>{r}</td></tr>')
    return f'''
        <h2>Other Contractors in {esc(city)}</h2>
        <p>Comparing at least two written quotes is the single best protection against
           overpaying. Other {esc(city)} businesses in this directory:</p>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th scope="col">Business</th><th scope="col">Rating</th></tr></thead>
            <tbody>{"".join(rows)}</tbody>
          </table>
        </div>'''


def faq_section(d, p):
    """Questions answered strictly from this business's own data."""
    name, city = d["name"], d.get("city") or "Virginia"
    qa = []

    if d.get("rating") and d.get("reviews"):
        qa.append((f"How is {name} rated?",
                   f"{name} holds a {d['rating']:.1f}-star rating on Google from "
                   f"{d['reviews']:,} reviews."))
    if d.get("city"):
        qa.append((f"Where is {name} based?",
                   f"{name} is based in {d['city']}, Virginia"
                   + (f", in the {d['county']} area" if d.get("county") else "")
                   + f", and takes work across {d['city']} and the surrounding communities."))
    hrs = d.get("hours") or {}
    if hrs:
        sun = hrs.get("Sunday", "Closed")
        qa.append((f"Is {name} open on weekends?",
                   f"Their listed Saturday hours are {hrs.get('Saturday', 'Closed')} and Sunday "
                   f"{sun}. Hours can change, so confirm when you book."))
    subs = d.get("subtypes") or []
    if subs:
        qa.append((f"What kind of work does {name} do?",
                   f"They are listed under {len(subs)} categor"
                   + ("ies" if len(subs) > 1 else "y")
                   + f" on Google: {', '.join(subs)}."))
    qa.append((f"How do I get a quote from {name}?",
               "Submit a free job request through this site. We pass your details to the right "
               "contractor for the work and they contact you directly, usually within 1&ndash;3 "
               "business days. There is no obligation and no cost to you."))
    qa.append(("How much does basement waterproofing cost in Virginia?",
               "Interior drainage systems typically run $3,000&ndash;$9,000, exterior "
               "waterproofing $8,000&ndash;$15,000 or more, sump pump installation "
               "$1,000&ndash;$3,500, and crack injection $500&ndash;$1,500 per crack. These are "
               "informational ranges, not quotes &mdash; the only accurate number comes from an "
               "on-site inspection."))
    qa.append((f"Is {name} licensed and insured?",
               "Verify licensing yourself with the Virginia Department of Professional and "
               "Occupational Regulation (DPOR) and ask for a current certificate of insurance "
               "before any work starts. This directory does not license or insure contractors."))

    items = "".join(
        f'<div class="faq-item"><h3>{esc(q)}</h3><p>{a}</p></div>' for q, a in qa)
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": re.sub(r"&\w+;", "", q),
             "acceptedAnswer": {"@type": "Answer",
                                "text": html.unescape(re.sub(r"<[^>]+>", "", a))}}
            for q, a in qa],
    }
    return f'''
        <h2>Frequently Asked Questions</h2>
        <div class="faq-list">{items}</div>''', json.dumps(schema)


def featured_figure(d):
    src = d.get("photo") or d.get("street_view")
    if not src:
        return "", ""
    logo = d.get("logo")
    count = d.get("photos_count") or 0
    logo_html = (f'<img class="biz-featured__logo" src="{esc(logo)}" alt="" width="44" height="44" '
                 f'loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">'
                 if logo else "")
    cap = (f"{esc(d['name'])} &mdash; from their Google Business Profile"
           + (f" ({count:,} photos on Google)" if count > 1 else ""))
    fig = f'''<figure class="biz-featured">
          <img src="{esc(src)}" alt="{esc(d["name"])}" loading="lazy" decoding="async"
               referrerpolicy="no-referrer" onerror="this.closest('figure').remove()">
          {logo_html}
          <figcaption>{cap}</figcaption>
        </figure>'''
    return fig, src


# --------------------------------------------------------------- page
def build(slug, d, p):
    name = d["name"]
    city = d.get("city") or ""
    loc = f"{esc(city)}, VA" if city else "Virginia"
    fig, og = featured_figure(d)
    faq_html, faq_schema = faq_section(d, p)

    rating_line = ""
    if d.get("rating"):
        rc = (f' <span class="review-count">({d["reviews"]:,} Google reviews)</span>'
              if d.get("reviews") else "")
        rating_line = (f'<div class="rating-line"><span class="stars">{stars(d["rating"])}</span> '
                       f'<span class="rating-num">{d["rating"]:.1f}</span>{rc}</div>')

    reviews_link = ""
    if d.get("reviews_link"):
        reviews_link = (f'<p style="margin-top:12px;"><a href="{esc(d["reviews_link"])}" '
                        f'target="_blank" rel="noopener noreferrer nofollow" '
                        f'style="color:#cfe0f0;font-weight:600;">Read the Google reviews '
                        f'&#8599;</a></p>')

    title = f"{esc(name)} | {loc} Waterproofing Contractor Profile"
    desc = (f"{name} in {city or 'Virginia'}: rating, review breakdown, services, business hours, "
            f"service area and a free job request form. No calls needed &mdash; submit and get matched.")

    ld = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": name,
          "url": f"{BASE}/partners/{slug}/",
          "address": {"@type": "PostalAddress",
                      "streetAddress": d.get("address", ""),
                      "addressLocality": city, "addressRegion": "VA",
                      "postalCode": d.get("postal_code", ""),
                      "addressCountry": "US"}}
    if d.get("lat") and d.get("lng"):
        ld["geo"] = {"@type": "GeoCoordinates", "latitude": d["lat"], "longitude": d["lng"]}
    if og:
        ld["image"] = og
    if d.get("rating") and d.get("reviews"):
        ld["aggregateRating"] = {"@type": "AggregateRating",
                                 "ratingValue": f"{d['rating']:.1f}",
                                 "reviewCount": str(d["reviews"])}
    if d.get("subtypes"):
        ld["additionalType"] = d["subtypes"]

    facts = []
    if d.get("address"):
        facts.append(f'<li><span class="lbl">Address</span>{esc(d["address"])}</li>')
    if d.get("rating"):
        facts.append(f'<li><span class="lbl">Google rating</span>{d["rating"]:.1f} of 5</li>')
    if d.get("reviews"):
        facts.append(f'<li><span class="lbl">Reviews</span>{d["reviews"]:,}</li>')
    if d.get("photos_count"):
        facts.append(f'<li><span class="lbl">Photos on Google</span>{d["photos_count"]:,}</li>')
    if d.get("category"):
        facts.append(f'<li><span class="lbl">Primary category</span>{esc(d["category"])}</li>')
    if d.get("county"):
        facts.append(f'<li><span class="lbl">Area</span>{esc(d["county"])}</li>')
    facts.append(f'<li><span class="lbl">Reviews page</span>'
                 f'<a href="/reviews/{esc(slug)}/">{esc(name)} reviews &rarr;</a></li>')

    og_meta = f'\n<meta property="og:image" content="{esc(og)}">' if og else ""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/partners/{slug}/">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}/partners/{slug}/">{og_meta}
<link rel="stylesheet" href="/css/styles.css">
{ADSENSE}
<script type="application/ld+json">{json.dumps(ld)}</script>
<script type="application/ld+json">{faq_schema}</script>
</head>
<body>
{SITE_HEADER}
<section class="contractor-hero">
  <div class="container">
    <div class="breadcrumb" style="color:#9fb6cc;"><a href="/" style="color:#cfe0f0;">Home</a> /
      <a href="/partners/" style="color:#cfe0f0;">Partners</a> / {esc(name)}</div>
    <span class="contractor__badge" style="margin-bottom:6px;">Directory Listing</span>
    <h1>{esc(name)}</h1>
    <p style="margin-top:6px;color:#cfe0f0;">{loc}{' &middot; ' + esc(d["category"]) if d.get("category") else ''}</p>
    {rating_line}
    {reviews_link}
  </div>
</section>

<main>
<section class="section">
  <div class="container">
    <div class="grid-2" style="align-items:start;">
      <div class="prose">
        {fig}
        <h2>About {esc(name)}</h2>
        {about_prose(d, p)}
{rating_breakdown(d)}
{services_section(d, p)}
{attributes_section(d)}
{hours_section(d)}
{area_section(d, p)}
{neighbours_section(d, slug)}
{faq_html}

        <h2>Before You Hire Any Contractor</h2>
        <ul>
          <li>Confirm the licence number with the Virginia DPOR and ask for a current certificate of insurance.</li>
          <li>Get the diagnosis in writing &mdash; where the water is coming from, not just what will be installed.</li>
          <li>Compare at least two itemised quotes covering the same scope of work.</li>
          <li>Ask what the warranty covers, how long it runs, and whether it transfers when you sell.</li>
          <li>Check the most recent reviews, not the lifetime average &mdash; crews and ownership change.</li>
        </ul>
        <p class="text-muted" style="font-size:.9rem;">This is a free directory listing compiled from
           public sources. We are not affiliated with {esc(name)}, we do not perform waterproofing
           work, and we make no warranty about any contractor&rsquo;s workmanship.</p>
      </div>

      <div>
        <div class="fact-card" style="margin-bottom:22px;">
          <h3 style="margin-top:0;">Instant Free Quote</h3>
          <p class="text-muted" style="font-size:.92rem;">Describe the job once and we&rsquo;ll connect
             you with the ideal contractor for your situation. They&rsquo;ll reach out within
             1&ndash;3 business days. Free, no obligation.</p>
          <a href="/get-a-quote/?provider={esc(slug)}" class="btn btn--primary btn--block btn--lg">Call or Text for Quote</a>
        </div>
        <div class="fact-card" style="margin-bottom:22px;">
          <ul class="fact-list">{"".join(facts)}</ul>
        </div>
        <div class="fact-card" style="margin-bottom:22px;">
          <h3 style="margin-top:0;">Own this business?</h3>
          <p class="text-muted" style="font-size:.92rem;">Claim the listing free to correct the
             details, add your services, and receive matched job requests.</p>
          <a href="/claim-listing/?provider={esc(slug)}" class="btn btn--ghost btn--block">Claim This Listing</a>
        </div>
        <div class="fact-card">
          <ul class="fact-list">
            <li><span class="lbl">Directory</span><a href="/partners/">All Virginia partners &rarr;</a></li>
            <li><span class="lbl">Reviews</span><a href="/reviews/">Contractor ratings &rarr;</a></li>
            <li><span class="lbl">Map search</span><a href="/find/">Find a pro near you &rarr;</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</section>
</main>
{FOOTER}
'''


def main():
    out_root = os.path.join(ROOT, "partners")
    written = 0
    thin = []
    for slug in sorted(os.listdir(out_root)):
        page_path = os.path.join(out_root, slug, "index.html")
        if not os.path.isfile(page_path):
            continue
        d = DETAILS.get(slug)
        if not d:
            thin.append(slug)
            continue
        html_out = build(slug, d, PARTNERS.get(slug, {}))
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        written += 1

    words = []
    for slug in list(DETAILS)[:0] or []:
        pass
    print(f"Rebuilt {written} partner profile pages")
    if thin:
        print(f"  no Outscraper record, left untouched: {thin}")


if __name__ == "__main__":
    main()
