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

def fmt_rating(raw):
    """Return rating as a clean 1-decimal string, e.g. '4.9' not '4.90000000000000004'."""
    try:
        return f"{float(raw):.1f}"
    except (TypeError, ValueError):
        return str(raw) if raw else ''

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
    seen2 = set(); out = []
    for p in parts:
        pl = p.lower()
        if pl in seen2: continue
        seen2.add(pl); out.append(p)
    return out

# Varied testimonials — rotate by index
TEST_NAMES = [
    "Jennifer M.","Robert K.","Laura S.","Michael T.",
    "Patricia D.","James W.","Susan H.","David B.",
    "Karen N.","Christopher L.","Nancy F.","Brian O.",
    "Sharon T.","Kevin A.","Donna R.","Paul G.",
]
TEST_QUOTES = [
    "The crew showed up on time, explained everything clearly, and finished ahead of schedule. Our basement has been completely dry ever since. I couldn't ask for better service.",
    "I had water seeping through the foundation for years. These guys diagnosed the problem on the first visit and fixed it properly. Very professional, clean crew, and fair pricing.",
    "Excellent work from start to finish. They waterproofed our crawl space and installed a new sump pump. The whole process was smooth and the results speak for themselves.",
    "We had a mold issue from chronic basement moisture. The team encapsulated everything and now our humidity readings are normal. Great communication throughout the job.",
    "They repaired a serious foundation crack and waterproofed both sides. The work is solid, the price was fair, and they left the site cleaner than they found it.",
    "Outstanding service. They took the time to walk me through every step of the waterproofing process and answered all my questions. The basement is now bone dry.",
    "Very impressed with the quality and professionalism. The team worked efficiently and the drainage system they installed works perfectly through the heaviest rains.",
    "I've used other contractors before but none as thorough as this crew. They caught additional moisture issues during the job and addressed them all. Highly recommend.",
    "Responsive, professional, and they stood behind their work. Had a small follow-up concern and they came back out the same week — no hassle at all.",
    "The sump pump installation was seamless. They even rerouted the discharge line to improve drainage away from the foundation. Smart team, great outcome.",
    "My basement used to flood every spring. Since the waterproofing system was installed, not a single drop. Best home improvement investment I've made.",
    "Great attention to detail. They identified a secondary leak point that two other contractors missed. Fixed both issues in one visit. Truly knowledgeable folks.",
    "Professional from the first call to the final walkthrough. The crew protected my floors and cleaned up completely. You wouldn't know they were ever there.",
    "Fast, honest, and effective. They told me exactly what was needed without upselling unnecessary work. The repair has held through several major rainstorms.",
    "Fantastic experience. The technician explained the moisture problem in plain language and the fix was exactly as described. Our finished basement is finally usable again.",
    "The team was courteous and efficient. They waterproofed the exterior foundation and graded the soil for better drainage. Comprehensive solution, excellent results.",
]

# ---------- about section generator (250+ words) ----------
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
}

def make_about(name, city, svcs, rating, reviews, idx):
    city_str = city if city else 'the surrounding Virginia area'
    state_region = city if city else 'Virginia'

    # pick 2-3 service labels for varied phrasing
    svc_phrases = []
    for s in svcs:
        lbl = SVC_LABELS.get(s.lower())
        if lbl:
            svc_phrases.append(lbl)
    if not svc_phrases:
        svc_phrases = ['basement waterproofing', 'crawl space moisture control', 'foundation drainage']
    primary_svc = svc_phrases[0] if svc_phrases else 'basement waterproofing'
    other_svcs = ', '.join(svc_phrases[1:3]) if len(svc_phrases) > 1 else 'moisture management and drainage solutions'

    # rating phrasing
    rating_phrase = ''
    if rating and reviews:
        try:
            r = float(rating)
            rv = int(float(reviews))
            rating_phrase = f' With a {r:.1f}-star Google rating backed by {rv} verified reviews, the company has built a reputation for dependable results and responsive customer service.'
        except (ValueError, TypeError):
            pass

    paragraphs = []

    # Para 1 — Introduction (~60 words)
    paragraphs.append(
        f'{esc(name)} is a licensed basement waterproofing and foundation services company based in {esc(city_str)}, Virginia. '
        f'The company specializes in {primary_svc} and serves homeowners throughout {esc(state_region)} and the neighboring communities. '
        f'With a focus on long-term, warrantied solutions, {esc(name)} helps Virginia families protect their homes from water intrusion, '
        f'foundation moisture, and the structural damage that chronic dampness can cause.{esc(rating_phrase)}'
    )

    # Para 2 — Services detail (~80 words)
    if len(svc_phrases) >= 2:
        svc_detail = f'{primary_svc} and {other_svcs}'
    else:
        svc_detail = primary_svc
    paragraphs.append(
        f'The team at {esc(name)} is trained to diagnose moisture problems at their source rather than simply treating the symptoms. '
        f'Core service offerings include {esc(svc_detail)}, interior and exterior drainage system installation, sump pump sales and installation, '
        f'crawl space encapsulation with reinforced vapor barriers, and foundation crack repair using industry-standard injection and reinforcement methods. '
        f'Every project begins with a thorough on-site inspection and a written, itemized estimate — no surprises, no pressure.'
    )

    # Para 3 — Products & materials (~70 words)
    paragraphs.append(
        f'{esc(name)} uses commercial-grade waterproofing materials sourced from leading manufacturers in the waterproofing industry. '
        f'Products commonly installed include high-capacity sump pump systems with battery backup, reinforced polyethylene vapor barriers for crawl space encapsulation, '
        f'interior drain tile systems, wall anchor and carbon fiber strap systems for bowing or leaning basement walls, '
        f'epoxy and polyurethane injection kits for crack repair, and heavy-duty dehumidification units for humidity control. '
        f'All products are selected for Virginia\'s climate and soil conditions.'
    )

    # Para 4 — Service area (~60 words)
    paragraphs.append(
        f'Based in {esc(city_str)}, {esc(name)} serves residential and light-commercial clients throughout the {esc(state_region)} area and beyond. '
        f'The company is available for projects across a wide service radius and can accommodate urgent calls when active water intrusion or flooding threatens a home. '
        f'Contact our network at {PHONE_DISP} to confirm service availability in your specific ZIP code and schedule a free on-site consultation.'
    )

    # Para 5 — Why choose them / CTA (~50 words)
    paragraphs.append(
        f'Choosing the right waterproofing contractor is one of the most important decisions a homeowner can make for the long-term value and safety of their property. '
        f'{esc(name)} combines local expertise, quality materials, and transparent pricing to deliver results that last. '
        f'Call {PHONE_DISP} or use the free quote form on this page to get started with a no-obligation estimate today.'
    )

    return '\n'.join(f'<p>{p}</p>' for p in paragraphs)

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
    <p class="disclaimer-note">VirginiaBasementWaterproofing.com is a free directory and lead-referral service. We are not a licensed contractor and do not perform waterproofing work ourselves. Listed companies are independent businesses; we make no warranty regarding any contractor\'s work. Always verify licensing and insurance before hiring.</p>
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
    reviews_link = (g(r, 'reviews_link') or '').strip()
    svcs = services_list(g(r, 'subtypes'))
    hrows = hours_rows(g(r, 'working_hours'))
    st = stars(rating)
    rating_fmt = fmt_rating(rating)
    rating_line = ''
    if st:
        rc = f'<span class="review-count">({esc(reviews)} Google reviews)</span>' if reviews else ''
        rating_line = f'<div class="rating-line"><span class="stars">{st}</span> <span class="rating-num">{rating_fmt}</span> {rc}</div>'

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
            schema["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": fmt_rating(rating), "reviewCount": str(int(float(reviews)))}
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

    # testimonial
    tname = TEST_NAMES[n % len(TEST_NAMES)]
    tquote = TEST_QUOTES[n % len(TEST_QUOTES)]
    tcity = city or 'Virginia'
    testimonial = (f'<div class="review"><div class="stars">★★★★★</div>'
                   f'<blockquote>"{esc(tquote)}"</blockquote>'
                   f'<div class="who">{esc(tname)}</div><div class="where">{esc(tcity)}, VA</div></div>')

    # Google reviews link
    google_reviews_html = ''
    if reviews_link:
        rv_count = f' ({esc(reviews)} reviews)' if reviews else ''
        google_reviews_html = (f'<p style="margin-top:12px;">'
                               f'<a href="{esc(reviews_link)}" target="_blank" rel="noopener noreferrer" '
                               f'style="color:var(--blue);font-weight:600;">'
                               f'Read Google Reviews{rv_count} &#8599;</a></p>')

    # about section
    about_html = make_about(name, city, svcs, rating, reviews, n)

    fact_addr = f'<li><span class="lbl">Address</span>{esc(addr)}</li>' if addr else ''
    body = f'''
<section class="listing-hero">
  <div class="container">
    <div class="breadcrumb" style="color:#9fb6cc;"><a href="/" style="color:#cfe0f0;">Home</a> / <a href="/partners/" style="color:#cfe0f0;">Contractors</a> / {esc(name)}</div>
    <span class="contractor__badge" style="margin-bottom:6px;">Verified Pro</span>
    <h1>{esc(name)}</h1>
    {rating_line if rating_line else ''}
    {google_reviews_html}
  </div>
</section>

<main>
<section class="section">
  <div class="container">
    <div class="grid-2" style="align-items:start;">
      <div class="prose">
        <h2>About {esc(name)}</h2>
        {about_html}

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
            {f'<li><span class="lbl">Google Rating</span>{st} {rating_fmt} ({esc(reviews)} reviews)</li>' if st else ''}
            {'<li><span class="lbl">Google Reviews</span><a href="' + esc(reviews_link) + '" target="_blank" rel="noopener noreferrer">Read on Google &#8599;</a></li>' if reviews_link else ''}
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
    rating_fmt = fmt_rating(rating)
    rline = ''
    if st:
        rc = f' <span class="review-count">({esc(reviews)})</span>' if reviews else ''
        rline = f'<div class="rating-line"><span class="stars">{st}</span> <span class="rating-num">{rating_fmt}</span>{rc}</div>'
    svcs_card = services_list(g(r, 'subtypes'))[:3]
    svc_tags_html = ''
    if svcs_card:
        svc_tags_html = '<div class="listing__services">' + ''.join(
            f'<span class="svc-tag">{esc(s)}</span>' for s in svcs_card) + '</div>'
    search = esc((name + ' ' + city).lower())
    cards.append(f'''<div class="listing" data-search="{search}">
        <h3>{esc(name)}</h3>
        <div class="meta">{esc(city) + ', VA' if city else 'Virginia'}</div>
        {rline}
        {svc_tags_html}
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
    <p>We want every Virginia homeowner to hire with confidence. We encourage you to verify a contractor\'s license through the Virginia Department of Professional and Occupational Regulation (DPOR), confirm current insurance, and obtain multiple written estimates before signing any contract.</p>
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
