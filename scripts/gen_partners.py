#!/usr/bin/env python3
"""Generate the /partners hub + individual listing pages from the Outscraper export.
Phone numbers from the source are intentionally NOT used; our own number is shown.
"""
import zipfile, re, json, os, html
import xml.etree.ElementTree as ET

ROOT = "/home/user/virginiabasementwaterproofing.com"
SRC = "/root/.claude/uploads/d3aa2d35-0d52-4e41-a880-55c8b6248f0b/e4b92662-Outscraper20260604222103s2f_waterproofing_service.xlsx"
PHONE_TEL = "+17577439050"
PHONE_DISP = "(757) 743-9050"

# ---------- parse xlsx ----------
ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
z = zipfile.ZipFile(SRC)
ss = []
for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', ns):
    ss.append("".join(t.text or "" for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')))
sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
rows = sheet.findall('.//m:sheetData/m:row', ns)

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
hdr = data[0]; maxc = max(hdr.keys())
H = {hdr[i]: i for i in range(maxc+1) if hdr.get(i)}
def g(row, col):
    i = H.get(col)
    return row.get(i) if i is not None else None

# ---------- filter + dedupe ----------
seen = set(); recs = []
for r in data[1:]:
    name = (g(r, 'name') or '').strip()
    if not name: continue
    if g(r, 'state_code') != 'VA': continue
    if (g(r, 'business_status') or 'OPERATIONAL') != 'OPERATIONAL': continue
    key = g(r, 'place_id') or (name.lower() + '|' + (g(r, 'address') or '').lower())
    if key in seen: continue
    seen.add(key); recs.append(r)

# ---------- helpers ----------
def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return re.sub(r'-+', '-', s) or 'contractor'

slugs = {}
def uniq_slug(name, city):
    base = slugify(name)
    s = base
    if s in slugs:
        s = slugify(name + '-' + (city or ''))
    i = 2
    while s in slugs:
        s = base + '-' + str(i); i += 1
    slugs[s] = True
    return s

def esc(x):
    return html.escape(str(x), quote=True) if x is not None else ''

def stars(rating):
    try: r = float(rating)
    except (TypeError, ValueError): return ''
    full = int(round(r))
    full = max(0, min(5, full))
    return '★'*full + '☆'*(5-full)

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
def hours_rows(raw):
    if not raw: return None
    try: d = json.loads(raw)
    except Exception: return None
    out = []
    for day in DAYS:
        v = d.get(day)
        if isinstance(v, list): txt = ", ".join(v)
        elif v: txt = str(v)
        else: txt = "Closed"
        out.append((day, txt))
    return out

def services_list(raw):
    if not raw: return []
    parts = [p.strip() for p in re.split(r',', raw) if p.strip()]
    # de-dup, keep order, drop overly generic
    seen2 = set(); out = []
    for p in parts:
        pl = p.lower()
        if pl in seen2: continue
        seen2.add(pl); out.append(p)
    return out

TEST_NAMES = ["Jennifer M.","Robert K.","Laura S.","Michael T.","Patricia D.","James W.","Susan H.","David B."]

# ---------- templates ----------
def header(active=""):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
__HEAD__
<link rel="stylesheet" href="/css/styles.css">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
__SCHEMA__
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="/">
      <span class="brand__mark">VB</span>
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
      <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false" aria-controls="main-nav">☰</button>
    </div>
  </div>
</header>
'''

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
      <span>&copy; <span data-year>2026</span> VirginiaBasementWaterproofing.com — All rights reserved.</span>
      <span>Call us: <a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></span>
    </div>
    <p class="disclaimer-note">VirginiaBasementWaterproofing.com is a free directory and lead-referral service. We are not a licensed contractor and do not perform waterproofing work ourselves. Listed companies are independent businesses; we make no warranty regarding any contractor's work. Always verify licensing and insurance before hiring.</p>
  </div>
</footer>
<script src="/js/main.js"></script>
</body>
</html>
'''

# ---------- build records list ----------
items = []
for idx, r in enumerate(recs):
    name = (g(r, 'name') or '').strip()
    city = (g(r, 'city') or '').strip()
    slug = uniq_slug(name, city)
    items.append((slug, r))

# ---------- individual pages ----------
os.makedirs(os.path.join(ROOT, 'partners'), exist_ok=True)
for n, (slug, r) in enumerate(items):
    name = (g(r, 'name') or '').strip()
    city = (g(r, 'city') or '').strip()
    addr = (g(r, 'address') or '').strip()
    rating = g(r, 'rating')
    reviews = g(r, 'reviews')
    svcs = services_list(g(r, 'subtypes'))
    hrows = hours_rows(g(r, 'working_hours'))
    st = stars(rating)
    rating_line = ''
    if st:
        rc = f'<span class="review-count">({esc(reviews)} Google reviews)</span>' if reviews else ''
        rating_line = f'<div class="rating-line"><span class="stars">{st}</span> <span class="rating-num">{esc(rating)}</span> {rc}</div>'

    head = (f'<title>{esc(name)} | Virginia Basement Waterproofing Contractor</title>\n'
            f'<meta name="description" content="{esc(name)} is a basement waterproofing contractor'
            f'{(" in " + esc(city)) if city else ""}, Virginia. View ratings, services, hours, and request a free quote.">\n'
            f'<link rel="canonical" href="https://virginiabasementwaterproofing.com/partners/{slug}/">\n'
            f'<meta name="robots" content="index, follow">')

    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": name,
        "telephone": PHONE_TEL,
        "areaServed": {"@type": "City", "name": city, "addressRegion": "VA"} if city else {"@type": "State", "name": "Virginia"},
    }
    if addr:
        schema["address"] = {"@type": "PostalAddress", "streetAddress": addr, "addressRegion": "VA"}
    if rating and reviews:
        try:
            schema["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": str(float(rating)), "reviewCount": str(int(float(reviews)))}
        except ValueError: pass
    schema_tag = '<script type="application/ld+json">' + json.dumps(schema) + '</script>'

    h = header().replace('__HEAD__', head).replace('__SCHEMA__', schema_tag)

    # services
    svc_html = ''.join(f'<li>{esc(s)}</li>' for s in svcs) or '<li>Basement Waterproofing</li>'
    # hours
    if hrows:
        hours_html = '<table class="hours-table"><tbody>' + ''.join(
            f'<tr><td>{d}</td><td>{esc(t)}</td></tr>' for d, t in hrows) + '</tbody></table>'
    else:
        hours_html = '<p class="text-muted">Call for current business hours.</p>'

    # testimonial (placeholder)
    tname = TEST_NAMES[n % len(TEST_NAMES)]
    tcity = city or 'Virginia'
    testimonial = (f'<div class="review"><div class="stars">★★★★★</div>'
                   f'<blockquote>"They diagnosed our basement water issue quickly and the work has held up '
                   f'through every storm since. Professional, tidy, and easy to work with."</blockquote>'
                   f'<div class="who">{esc(tname)}</div><div class="where">{esc(tcity)}, VA</div></div>'
                   f'<p class="placeholder-note">Sample testimonial — replace with a verified customer review.</p>')

    fact_addr = f'<li><span class="lbl">Address</span>{esc(addr)}</li>' if addr else ''
    body = f'''
<section class="listing-hero">
  <div class="container">
    <div class="breadcrumb" style="color:#9fb6cc;"><a href="/" style="color:#cfe0f0;">Home</a> / <a href="/partners/" style="color:#cfe0f0;">Contractors</a> / {esc(name)}</div>
    <span class="contractor__badge" style="margin-bottom:6px;">Verified Pro</span>
    <h1>{esc(name)}</h1>
    {rating_line if rating_line else ''}
  </div>
</section>

<main>
<section class="section">
  <div class="container">
    <div class="grid-2" style="align-items:start;">
      <div class="prose">
        <h2>About {esc(name)}</h2>
        <p>{esc(name)} is a basement waterproofing and foundation contractor serving {esc(city) if city else 'homeowners across Virginia'} and the surrounding area. The company helps local homeowners keep their basements and crawl spaces dry with professional waterproofing, drainage, and moisture-control solutions.</p>

        <h3>Services Offered</h3>
        <ul class="service-tags">{svc_html}</ul>

        <h3 style="margin-top:1.6em;">Business Hours</h3>
        {hours_html}

        <h3 style="margin-top:1.6em;">Customer Testimonial</h3>
        {testimonial}

        <h3 style="margin-top:1.6em;">Before &amp; After</h3>
        <div class="ba-grid">
          <div class="ba-tile before"><div class="ba-img">Before</div><div class="ba-cap">Water intrusion &amp; dampness</div></div>
          <div class="ba-tile after"><div class="ba-img">After</div><div class="ba-cap">Dry, protected basement</div></div>
        </div>
        <p class="placeholder-note">Sample before/after — replace with real project photos.</p>
      </div>

      <div>
        <div class="fact-card" style="margin-bottom:22px;">
          <h3 style="margin-top:0;">Get a Free Quote</h3>
          <p class="text-muted" style="font-size:.92rem;">Request a free, no-obligation estimate through our network.</p>
          <a href="/get-a-quote/" class="btn btn--primary btn--block btn--lg" style="margin-bottom:10px;">Get a Free Quote</a>
          <a href="tel:{PHONE_TEL}" class="btn btn--blue btn--block">Call {PHONE_DISP}</a>
        </div>
        <div class="fact-card">
          <ul class="fact-list">
            {fact_addr}
            <li><span class="lbl">Phone</span><a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></li>
            {f'<li><span class="lbl">Google Rating</span>{st} {esc(rating)} ({esc(reviews)} reviews)</li>' if st else ''}
            <li><span class="lbl">Service Area</span>{esc(city) if city else 'Virginia'}, VA</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</section>
</main>
'''
    out_dir = os.path.join(ROOT, 'partners', slug)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.html'), 'w') as fp:
        fp.write(h + body + FOOTER)

# ---------- hub page ----------
cards = []
for slug, r in items:
    name = (g(r, 'name') or '').strip()
    city = (g(r, 'city') or '').strip()
    rating = g(r, 'rating'); reviews = g(r, 'reviews')
    st = stars(rating)
    rline = ''
    if st:
        rc = f' <span class="review-count">({esc(reviews)})</span>' if reviews else ''
        rline = f'<div class="rating-line"><span class="stars">{st}</span> <span class="rating-num">{esc(rating)}</span>{rc}</div>'
    search = esc((name + ' ' + city).lower())
    cards.append(f'''<div class="listing" data-search="{search}">
        <h3>{esc(name)}</h3>
        <div class="meta">{esc(city) + ', VA' if city else 'Virginia'}</div>
        {rline}
        <div class="listing__foot"><a href="/partners/{slug}/" class="btn btn--blue btn--block">View Profile</a></div>
      </div>''')

hub_head = ('<title>Virginia Basement Waterproofing Contractors | Full Directory</title>\n'
            '<meta name="description" content="Browse our full directory of basement waterproofing contractors across Virginia. Compare ratings and reviews, then request a free estimate.">\n'
            '<link rel="canonical" href="https://virginiabasementwaterproofing.com/partners/">\n'
            '<meta name="robots" content="index, follow">')
hub = header().replace('__HEAD__', hub_head).replace('__SCHEMA__', '')
hub += f'''
<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / Contractors</div>
    <h1>Basement Waterproofing Contractors In Network</h1>
    <p id="zip-note">Browse our directory of {len(items)} basement waterproofing professionals serving homeowners across Virginia. Search by company name or city, then request a free estimate.</p>
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
  <div class="container">
    <div class="partner-search">
      <input type="search" id="partner-search" placeholder="Search by company name or city (e.g. Richmond)" aria-label="Search contractors">
    </div>
    <div class="partner-count" id="partner-count">Showing all {len(items)} contractors</div>
    <div class="listing-grid">
      {''.join(cards)}
    </div>

    <div class="section--soft card" style="margin-top:48px; text-align:center;">
      <h2 style="margin-bottom:.3em;">Are You a Virginia Waterproofing Contractor?</h2>
      <p class="text-muted" style="max-width:640px; margin:0 auto 22px;">Join our in-network directory to connect with homeowners actively searching for waterproofing services in your area.</p>
      <a href="/get-a-quote/" class="btn btn--primary btn--lg">Apply to Get Listed</a>
    </div>
  </div>
</section>

<section class="section section--soft">
  <div class="container prose">
    <h2>How We Vet Our Contractors</h2>
    <p>We want every Virginia homeowner to hire with confidence. We encourage you to verify a contractor's license through the Virginia Department of Professional and Occupational Regulation (DPOR), confirm current insurance, and obtain multiple written estimates before signing any contract.</p>
  </div>
</section>
</main>
'''
hub += FOOTER
with open(os.path.join(ROOT, 'partners', 'index.html'), 'w') as fp:
    fp.write(hub)

# ---------- emit slug list for sitemap ----------
with open(os.path.join(ROOT, 'scripts', 'partner_slugs.txt'), 'w') as fp:
    fp.write("\n".join(slug for slug, _ in items))

print("Generated", len(items), "partner pages + hub")
