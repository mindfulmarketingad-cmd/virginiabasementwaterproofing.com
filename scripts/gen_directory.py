#!/usr/bin/env python3
"""Generate the two directory hubs and the per-business review pages.

  /partners/            every partner business in one sortable table
  /reviews/             the same roster ranked by rating / review volume
  /reviews/<slug>/      the review detail page for one business

Ratings and review counts come from data/partners.json, which is extracted from
the published profile pages (Google data). No review text is invented here: where
we have no first-party reviews we say so and link out to the Google listing.
"""
import os, sys, json, html
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_html import SITE_HEADER, FOOTER  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.virginiabasementwaterproofing.org"
ADSENSE = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
           '?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>')


def esc(s):
    return html.escape(str(s or ""), quote=True)


with open(os.path.join(ROOT, "data", "partners.json"), encoding="utf-8") as f:
    PARTNERS = json.load(f)

# every partner grouped by city, best-rated first, so each detail page can
# point at its local competition
BY_CITY = defaultdict(list)
for _p in PARTNERS:
    if _p.get("city"):
        BY_CITY[_p["city"]].append(_p)
for _c in BY_CITY:
    BY_CITY[_c].sort(key=lambda r: (-(r.get("rating") or 0), -(r.get("reviews") or 0)))


def stars_html(rating):
    if not rating:
        return '<span class="text-muted">Not rated</span>'
    full = int(round(rating))
    return (f'<span class="stars" aria-hidden="true">{"★" * full}{"☆" * (5 - full)}</span> '
            f'<span class="rating-num">{rating:.1f}</span>')


def availability(p):
    if p.get("open_24h"):
        return "24/7"
    d = p.get("days_open")
    if not d:
        return "&mdash;"
    return "7 days" if d == 7 else f"{d} days/wk"


def services_cell(p):
    labels = p.get("cat_labels") or []
    if not labels:
        labels = p.get("services") or []
    if not labels:
        return '<span class="text-muted">&mdash;</span>'
    shown = labels[:3]
    extra = len(labels) - len(shown)
    out = "".join(f'<span class="svc-tag">{esc(s)}</span>' for s in shown)
    if extra > 0:
        out += f'<span class="svc-tag svc-tag--more" title="{esc(", ".join(labels))}">+{extra}</span>'
    return out


def featured_figure(p):
    """Featured image from the Outscraper export, hotlinked to Google's CDN.

    Removes itself if the URL has rotated, so a dead image never leaves a broken
    frame on the page.
    """
    src = p.get("photo") or p.get("street_view")
    if not src:
        return ""
    logo = p.get("logo")
    logo_html = (f'<img class="biz-featured__logo" src="{esc(logo)}" alt="" width="44" height="44" '
                 f'loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">'
                 if logo else "")
    return f'''<figure class="biz-featured">
          <img src="{esc(src)}" alt="{esc(p["name"])}" loading="lazy" decoding="async"
               referrerpolicy="no-referrer" onerror="this.closest('figure').remove()">
          {logo_html}
          <figcaption>{esc(p["name"])} &mdash; from their Google Business Profile</figcaption>
        </figure>'''


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def score_chart(p):
    """Star-by-star distribution of this business's Google reviews."""
    scores = p.get("scores") or {}
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
    good = round((scores.get("5", 0) + scores.get("4", 0)) / total * 100)
    bad = round((scores.get("1", 0) + scores.get("2", 0)) / total * 100)
    return f'''
        <h3 style="margin-top:1.6em;">Star Breakdown</h3>
        <p>{good}% of {esc(p["name"])}&rsquo;s {total:,} reviewers gave four stars or better,
           and {bad}% gave two stars or below.</p>
        <div class="score-chart">{"".join(rows)}</div>'''


def review_context(p, rank, total):
    """Put the rating in context against the rest of the directory."""
    rating, reviews = p.get("rating"), p.get("reviews")
    if not rating:
        return ""
    pct = round(rank / total * 100)
    volume = ""
    if reviews:
        if reviews >= 500:
            volume = (f"{reviews:,} reviews is a large sample &mdash; the average here is unlikely "
                      "to move much, and it reflects years of work rather than a good month.")
        elif reviews >= 100:
            volume = (f"{reviews:,} reviews is a solid sample size; individual bad experiences "
                      "will not distort the average much.")
        elif reviews >= 20:
            volume = (f"At {reviews:,} reviews the sample is moderate &mdash; read the most recent "
                      "ones rather than trusting the average alone.")
        else:
            volume = (f"With only {reviews:,} reviews, treat this rating as a weak signal. A single "
                      "review moves the average significantly.")
    return f'''
        <h3 style="margin-top:1.6em;">How That Compares</h3>
        <p>{esc(p["name"])} ranks <strong>#{rank}</strong> of the {total} contractors in this
           directory &mdash; the top {pct}% by rating and review volume. {volume}</p>'''


def trust_signals(p):
    """Ownership and service attributes the business publishes itself."""
    attrs = p.get("attributes") or {}
    interesting = {}
    for section in ("From the business", "Service options", "Accessibility", "Payments", "Planning"):
        if attrs.get(section):
            interesting[section] = attrs[section]
    if not interesting:
        return ""
    blocks = "".join(
        f'<div class="attr-group"><h4>{esc(k)}</h4><ul>'
        + "".join(f"<li>{esc(v)}</li>" for v in vals) + "</ul></div>"
        for k, vals in interesting.items())
    return f'''
        <h3 style="margin-top:1.6em;">What They Publish About Themselves</h3>
        <p>Attributes listed on {esc(p["name"])}&rsquo;s own Google Business Profile:</p>
        <div class="attr-grid">{blocks}</div>'''


def availability_note(p):
    hrs = p.get("hours") or {}
    if not hrs:
        return ""
    rows = "".join(f"<tr><td>{d}</td><td>{esc(hrs.get(d, 'Closed'))}</td></tr>" for d in DAYS)
    lead = ("Listed as open 24 hours a day, which matters when water is actively coming in."
            if p.get("open_24h") else
            f"Listed as open {p.get('days_open', 0)} days a week.")
    return f'''
        <h3 style="margin-top:1.6em;">When They&rsquo;re Open</h3>
        <p>{lead} Our job request form runs around the clock either way.</p>
        <table class="hours-table"><tbody>{rows}</tbody></table>'''


def peer_table(p):
    city = p.get("city") or ""
    peers = [x for x in BY_CITY.get(city, []) if x["slug"] != p["slug"]][:6]
    if not peers:
        return ""
    rows = []
    for x in peers:
        r = (f'{stars_html(x["rating"])}'
             + (f' <span class="review-count">({x["reviews"]:,})</span>' if x.get("reviews") else "")
             if x.get("rating") else '<span class="text-muted">Not rated</span>')
        rows.append(f'<tr><td class="dir-name"><a href="/reviews/{esc(x["slug"])}/">'
                    f'{esc(x["name"])}</a></td><td>{r}</td></tr>')
    return f'''
        <h3 style="margin-top:1.6em;">Compare With Other {esc(city)} Contractors</h3>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th scope="col">Business</th><th scope="col">Rating</th></tr></thead>
            <tbody>{"".join(rows)}</tbody>
          </table>
        </div>'''


def page(title, desc, canonical, body, ld_json="", scripts="", og_image=""):
    ld = f"\n<script type=\"application/ld+json\">{ld_json}</script>" if ld_json else ""
    og = f'\n<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
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
<meta property="og:url" content="{BASE}{canonical}">{og}
<link rel="stylesheet" href="/css/styles.css">
{ADSENSE}{ld}
</head>
<body>
{SITE_HEADER}
{body}
{scripts}
{FOOTER}
'''


def write(rel_dir, content):
    out = os.path.join(ROOT, rel_dir)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(content)


def search_bar(placeholder):
    return f'''<div class="dir-toolbar">
      <form class="dir-search" role="search">
        <input type="search" id="dirSearch" placeholder="{placeholder}" aria-label="{placeholder}" autocomplete="off">
      </form>
      <div class="dir-count" id="dirCount" aria-live="polite"></div>
    </div>'''


# ---------------------------------------------------------------- /partners/
def build_partners():
    rows = sorted(PARTNERS, key=lambda p: p["name"].lower())
    trs = []
    for p in rows:
        slug = p["slug"]
        city = p.get("city") or ""
        loc = f"{esc(city)}, VA" if city else "Virginia"
        rating = p.get("rating")
        reviews = p.get("reviews")
        area = p.get("county") or city or "Virginia"
        search = esc(" ".join(filter(None, [
            p["name"], city, p.get("zip", ""), p.get("county", ""),
            " ".join(p.get("cat_labels") or []), " ".join(p.get("services") or []),
        ])).lower())

        trs.append(f'''<tr data-search="{search}">
          <td class="dir-name"><a href="/partners/{esc(slug)}/">{esc(p["name"])}</a></td>
          <td data-sort="{esc(city)}">{loc}</td>
          <td data-sort="{rating or 0}">{stars_html(rating)}</td>
          <td class="num" data-sort="{reviews or 0}">{reviews if reviews else "&mdash;"}</td>
          <td class="dir-svcs">{services_cell(p)}</td>
          <td>{esc(area)}</td>
          <td data-sort="{p.get("days_open") or 0}">{availability(p)}</td>
          <td class="dir-cta">
            <a href="/get-a-quote/?provider={esc(slug)}" class="btn btn--blue btn--sm">Free Quote</a>
            <a href="/claim-listing/?provider={esc(slug)}" class="dir-claim">Claim</a>
          </td>
        </tr>''')

    rated = [p for p in rows if p.get("rating")]
    avg = sum(p["rating"] for p in rated) / len(rated) if rated else 0
    total_reviews = sum(p.get("reviews") or 0 for p in rows if p.get("reviews"))
    cities = len({p.get("city") for p in rows if p.get("city")})

    body = f'''<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / Partners</div>
    <h1>Virginia Waterproofing Partner Directory</h1>
    <p>All {len(rows)} basement waterproofing, foundation, crawl space and restoration
       businesses listed on this site &mdash; across {cities} Virginia cities, with
       {total_reviews:,} Google reviews between them and an average rating of {avg:.1f}&#9733;.
       Sort any column, or search by business, city, ZIP or service.</p>
    <div style="margin-top:18px;display:flex;gap:12px;flex-wrap:wrap;">
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Call or Text for Quote</a>
      <a href="/claim-listing/" class="btn btn--ghost btn--lg">Claim Your Listing</a>
    </div>
  </div>
</div>

<main>
<section class="section">
  <div class="container">
    {search_bar("Search business, city, ZIP or service&hellip;")}
    <div class="table-wrap">
      <table class="data-table" data-directory-table>
        <thead>
          <tr>
            <th data-sortable="text" scope="col">Business</th>
            <th data-sortable="text" scope="col">City / State</th>
            <th data-sortable="number" scope="col">Rating</th>
            <th data-sortable="number" scope="col">Reviews</th>
            <th scope="col">Jobs They Handle</th>
            <th data-sortable="text" scope="col">Service Area</th>
            <th data-sortable="number" scope="col">Availability</th>
            <th scope="col">Get Started</th>
          </tr>
        </thead>
        <tbody>
        {"".join(trs)}
        </tbody>
      </table>
    </div>
    <p class="dir-empty-note">No businesses match that search. Try a city name or a service.</p>

    <h2 style="margin-top:2.4em;">Is One of These Your Business?</h2>
    <p>Listings are compiled from public sources. If you own or manage a business on this
       page you can claim it free &mdash; correct the details, add your services, and start
       receiving matched job requests from Virginia homeowners.</p>
    <p><a href="/claim-listing/" class="btn btn--primary">Claim Your Listing</a></p>

    <h2 style="margin-top:2.4em;">Browse Another Way</h2>
    <ul>
      <li><a href="/reviews/">Contractor reviews</a> &mdash; the same roster ranked by rating</li>
      <li><a href="/find/">Find a pro on the map</a> &mdash; searchmaps by service and city</li>
      <li><a href="/virginia/">Browse by city</a> &mdash; local pages with area detail</li>
    </ul>
  </div>
</section>
</main>
'''
    write("partners", page(
        "Virginia Basement Waterproofing Partner Directory | All Contractors",
        f"Directory of all {len(rows)} basement waterproofing, foundation repair and crawl "
        "space contractors listed across Virginia. Compare ratings, services and service "
        "areas, or claim your listing.",
        "/partners/", body,
        scripts='<script src="/js/directory-table.js" defer></script>'))
    return len(rows)


# ---------------------------------------------------------------- /reviews/
def build_reviews_hub():
    rows = sorted(PARTNERS,
                  key=lambda p: (-(p.get("rating") or 0), -(p.get("reviews") or 0), p["name"].lower()))
    trs = []
    for i, p in enumerate(rows, 1):
        slug = p["slug"]
        city = p.get("city") or ""
        rating = p.get("rating")
        reviews = p.get("reviews") or 0
        pct = int(round((rating or 0) / 5 * 100))
        search = esc(f'{p["name"]} {city} {p.get("county","")}'.lower())
        bar = (f'<div class="rating-bar" title="{rating}/5"><span style="width:{pct}%"></span></div>'
               if rating else '<span class="text-muted">&mdash;</span>')
        trs.append(f'''<tr data-search="{search}">
          <td class="num" data-sort="{i}">{i}</td>
          <td class="dir-name"><a href="/reviews/{esc(slug)}/">{esc(p["name"])}</a></td>
          <td data-sort="{esc(city)}">{esc(city) + ", VA" if city else "Virginia"}</td>
          <td data-sort="{rating or 0}">{stars_html(rating)}</td>
          <td class="num" data-sort="{reviews}">{reviews if reviews else "&mdash;"}</td>
          <td data-sort="{rating or 0}">{bar}</td>
          <td class="dir-cta"><a href="/reviews/{esc(slug)}/" class="btn btn--blue btn--sm">Read Reviews</a></td>
        </tr>''')

    rated = [p for p in rows if p.get("rating")]
    avg = sum(p["rating"] for p in rated) / len(rated) if rated else 0
    total_reviews = sum(p.get("reviews") or 0 for p in rows if p.get("reviews"))
    five = sum(1 for p in rated if p["rating"] >= 4.8)

    body = f'''<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / Reviews</div>
    <h1>Virginia Waterproofing Contractor Reviews</h1>
    <p>Ratings for all {len(rows)} contractors in our directory, ranked highest first.
       {len(rated)} have a public rating, backed by {total_reviews:,} Google reviews in total &mdash;
       {five} of them sit at 4.8&#9733; or better. Click any business for its full review profile.</p>
    <div style="margin-top:18px;">
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Call or Text for Quote</a>
    </div>
  </div>
</div>

<main>
<section class="section">
  <div class="container">
    <div class="stats" style="margin-bottom:28px;">
      <div><div class="num">{len(rows)}</div><div class="lbl">Businesses Reviewed</div></div>
      <div><div class="num">{total_reviews:,}</div><div class="lbl">Total Google Reviews</div></div>
      <div><div class="num">{avg:.1f}&#9733;</div><div class="lbl">Average Rating</div></div>
      <div><div class="num">{five}</div><div class="lbl">Rated 4.8&#9733; or Higher</div></div>
    </div>

    {search_bar("Search a business or city&hellip;")}
    <div class="table-wrap">
      <table class="data-table" data-directory-table>
        <thead>
          <tr>
            <th data-sortable="number" scope="col">#</th>
            <th data-sortable="text" scope="col">Business</th>
            <th data-sortable="text" scope="col">City / State</th>
            <th data-sortable="number" scope="col">Rating</th>
            <th data-sortable="number" scope="col">Reviews</th>
            <th data-sortable="number" scope="col">Score</th>
            <th scope="col">Detail</th>
          </tr>
        </thead>
        <tbody>
        {"".join(trs)}
        </tbody>
      </table>
    </div>
    <p class="dir-empty-note">No businesses match that search. Try a city name.</p>

    <h2 style="margin-top:2.4em;">Where These Ratings Come From</h2>
    <p>Star ratings and review counts are the public Google Business Profile figures for each
       company, captured when the listing was added. They are a starting point, not a
       guarantee &mdash; always confirm a contractor&rsquo;s licence and insurance before hiring,
       and read the most recent reviews on Google before you sign anything.</p>

    <h2 style="margin-top:2.4em;">Browse Another Way</h2>
    <ul>
      <li><a href="/partners/">Full partner directory</a> &mdash; services, service areas and availability</li>
      <li><a href="/find/">Find a pro on the map</a> &mdash; searchmaps by service and city</li>
    </ul>
  </div>
</section>
</main>
'''
    write("reviews", page(
        "Virginia Basement Waterproofing Contractor Reviews & Ratings",
        f"Compare ratings and review counts for {len(rows)} Virginia basement waterproofing, "
        "foundation repair and crawl space contractors. Ranked highest rated first.",
        "/reviews/", body,
        scripts='<script src="/js/directory-table.js" defer></script>'))
    return rows


# ---------------------------------------------------------- /reviews/<slug>/
def build_review_page(p, rank, total):
    slug = p["slug"]
    name = p["name"]
    city = p.get("city") or ""
    rating = p.get("rating")
    reviews = p.get("reviews")
    loc = f"{esc(city)}, VA" if city else "Virginia"
    pct = int(round((rating or 0) / 5 * 100))

    title = f"{esc(name)} Reviews &amp; Rating | {loc}"
    desc = (f"{name} in {city or 'Virginia'} holds a {rating}-star rating from {reviews} Google "
            f"reviews. See the rating, services and service area, or request a free estimate."
            if rating and reviews else
            f"Review profile for {name}, a waterproofing contractor in {city or 'Virginia'}. "
            "See services, service area and request a free estimate.")

    ld = ""
    if rating and reviews:
        ld = json.dumps({
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": name,
            "url": f"{BASE}/partners/{slug}/",
            "address": {"@type": "PostalAddress",
                        "streetAddress": p.get("address", ""), "addressRegion": "VA"},
            "aggregateRating": {"@type": "AggregateRating",
                                "ratingValue": str(rating), "reviewCount": str(reviews)},
        })

    count_line = f"{reviews:,} Google reviews" if reviews else "Google rating"
    if rating:
        summary = f'''<div class="review-hero">
        <div class="review-hero__score">
          <div class="review-hero__num">{rating:.1f}</div>
          <div class="stars" aria-hidden="true">{"★" * int(round(rating))}{"☆" * (5 - int(round(rating)))}</div>
          <div class="review-hero__count">{count_line}</div>
        </div>
        <div class="review-hero__meter">
          <div class="rating-bar rating-bar--lg"><span style="width:{pct}%"></span></div>
          <p class="text-muted">Ranked <strong>#{rank}</strong> of {total} contractors in our Virginia directory
             by rating and review volume.</p>
        </div>
      </div>'''
    else:
        summary = ('<p class="text-muted">This business does not have a public star rating in our '
                   'directory yet.</p>')

    google = ""
    if p.get("google_reviews_url"):
        google = (f'<p><a href="{esc(p["google_reviews_url"])}" target="_blank" '
                  f'rel="noopener noreferrer nofollow" class="btn btn--ghost">'
                  f'Read all {reviews:,} reviews on Google &#8599;</a></p>' if reviews else
                  f'<p><a href="{esc(p["google_reviews_url"])}" target="_blank" '
                  'rel="noopener noreferrer nofollow" class="btn btn--ghost">Read reviews on Google &#8599;</a></p>')

    svc_list = p.get("cat_labels") or p.get("services") or []
    svcs = ("".join(f'<span class="svc-tag">{esc(s)}</span>' for s in svc_list)
            or '<span class="text-muted">Not listed</span>')

    facts = []
    if p.get("address"):
        facts.append(f'<li><span class="lbl">Address</span>{esc(p["address"])}</li>')
    if p.get("county"):
        facts.append(f'<li><span class="lbl">Service Area</span>{esc(p["county"])}</li>')
    if rating:
        facts.append(f'<li><span class="lbl">Google Rating</span>{rating:.1f} of 5</li>')
    if reviews:
        facts.append(f'<li><span class="lbl">Review Count</span>{reviews:,}</li>')
    facts.append(f'<li><span class="lbl">Availability</span>{availability(p)}</li>')

    body = f'''<section class="contractor-hero">
  <div class="container">
    <div class="breadcrumb" style="color:#9fb6cc;"><a href="/" style="color:#cfe0f0;">Home</a> /
      <a href="/reviews/" style="color:#cfe0f0;">Reviews</a> / {esc(name)}</div>
    <h1>{esc(name)} Reviews</h1>
    <p style="margin-top:8px;">{loc}</p>
  </div>
</section>

<main>
<section class="section">
  <div class="container">
    <div class="grid-2" style="align-items:start;">
      <div class="prose">
        {featured_figure(p)}
        <h2>Rating Summary</h2>
        {summary}
        {google}

        <h3 style="margin-top:1.6em;">What We Publish &mdash; and What We Don&rsquo;t</h3>
        <p>The score above is {esc(name)}&rsquo;s public Google Business Profile rating, recorded when
           this listing was compiled. We do not host our own written reviews for this business, so
           rather than paraphrase someone else&rsquo;s words we link straight to the source. Read the
           most recent Google reviews before you make a decision &mdash; ratings move, and a company&rsquo;s
           last six months matter more than its lifetime average.</p>
        <p>If you have hired {esc(name)}, the most useful thing you can do for the next homeowner is
           leave an honest review on their Google listing.</p>

{score_chart(p)}
{review_context(p, rank, total)}

        <h3 style="margin-top:1.6em;">Jobs They Handle</h3>
        <div class="listing__services">{svcs}</div>
{trust_signals(p)}
{availability_note(p)}
{peer_table(p)}

        <h3 style="margin-top:1.6em;">Before You Hire</h3>
        <ul>
          <li>Confirm the licence number with the Virginia DPOR and ask for a certificate of insurance.</li>
          <li>Get the diagnosis in writing &mdash; the water source, not just the proposed fix.</li>
          <li>Compare at least two written, itemised quotes for the same scope of work.</li>
          <li>Ask what the warranty covers, how long it lasts, and whether it transfers on sale.</li>
        </ul>
      </div>

      <div>
        <div class="fact-card" style="margin-bottom:22px;">
          <h3 style="margin-top:0;">Instant Free Quote</h3>
          <p class="text-muted" style="font-size:.92rem;">Tell us about the job and we&rsquo;ll connect you
             with the ideal contractor for your situation &mdash; they&rsquo;ll reach out within 1&ndash;3
             business days.</p>
          <a href="/get-a-quote/?provider={esc(slug)}" class="btn btn--primary btn--block btn--lg">Call or Text for Quote</a>
        </div>
        <div class="fact-card" style="margin-bottom:22px;">
          <ul class="fact-list">{"".join(facts)}</ul>
        </div>
        <div class="fact-card">
          <h3 style="margin-top:0;">Own this business?</h3>
          <p class="text-muted" style="font-size:.92rem;">Claim the listing to correct details and
             receive matched job requests.</p>
          <a href="/claim-listing/?provider={esc(slug)}" class="btn btn--ghost btn--block">Claim This Listing</a>
        </div>
        <div class="fact-card">
          <ul class="fact-list">
            <li><span class="lbl">Full profile</span><a href="/partners/{esc(slug)}/">{esc(name)} &rarr;</a></li>
            <li><span class="lbl">All reviews</span><a href="/reviews/">Virginia contractor reviews &rarr;</a></li>
            <li><span class="lbl">Directory</span><a href="/partners/">All partners &rarr;</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</section>
</main>
'''
    write(f"reviews/{slug}", page(title, esc(desc), f"/reviews/{slug}/", body, ld_json=ld,
                                  og_image=p.get("photo") or p.get("street_view") or ""))


def main():
    n = build_partners()
    ranked = build_reviews_hub()
    for i, p in enumerate(ranked, 1):
        build_review_page(p, i, len(ranked))
    print(f"Generated /partners/ hub ({n} rows), /reviews/ hub, "
          f"and {len(ranked)} /reviews/<slug>/ pages")


if __name__ == "__main__":
    main()
