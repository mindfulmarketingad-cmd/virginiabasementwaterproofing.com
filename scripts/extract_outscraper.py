#!/usr/bin/env python3
"""Extract everything usable from the Outscraper export into data/partner-details.json.

Deliberately NOT extracted, so visitors have no route around the lead form:
phone, website, booking_appointment_link, order_links, location_link.

Slugs are derived with exactly the same filter, dedupe and slug rules as
gen_partners.py, so the keys line up with the existing /partners/<slug>/ pages.
"""
import os, re, json, zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get(
    "OUTSCRAPER_XLSX",
    "/root/.claude/uploads/e5d91189-be53-5917-9e4a-2869781cc3d8/"
    "0aea0fa5-Outscraper20260604222103s2f_waterproofing_service.xlsx")

ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
T = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# attribute groups worth publishing, in display order. "Other" is dropped: it
# duplicates "From the business" and "Crowd" in every row we looked at.
ABOUT_SECTIONS = ["From the business", "Service options", "Offerings", "Amenities",
                  "Accessibility", "Parking", "Payments", "Planning", "Crowd"]


def load_rows():
    z = zipfile.ZipFile(SRC)
    ss = ["".join(t.text or "" for t in si.iter(T))
          for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', ns)]

    def colnum(ref):
        s = re.match(r'([A-Z]+)', ref).group(1)
        n = 0
        for ch in s:
            n = n * 26 + (ord(ch) - 64)
        return n - 1

    out = []
    for r in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:sheetData/m:row', ns):
        cells = {}
        for c in r.findall('m:c', ns):
            v = c.find('m:v', ns)
            if v is not None:
                cells[colnum(c.get('r'))] = ss[int(v.text)] if c.get('t') == 's' else v.text
        out.append(cells)
    return out


rows = load_rows()
hdr = rows[0]
H = {hdr[i]: i for i in range(max(hdr.keys()) + 1) if hdr.get(i)}


def g(row, col):
    i = H.get(col)
    return row.get(i) if i is not None else None


# ---------- filter + dedupe (identical to gen_partners.py) ----------
seen, recs = set(), []
for r in rows[1:]:
    name = (g(r, 'name') or '').strip()
    if not name:
        continue
    if g(r, 'state_code') != 'VA':
        continue
    if (g(r, 'business_status') or 'OPERATIONAL') != 'OPERATIONAL':
        continue
    key = g(r, 'place_id') or (name.lower() + '|' + (g(r, 'address') or '').lower())
    if key in seen:
        continue
    seen.add(key)
    recs.append(r)


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
        s = base + '-' + str(i)
        i += 1
    slugs[s] = True
    return s


# ---------- field parsers ----------
def url(v):
    v = (v or "").strip()
    return v if v.startswith("http") else ""


def text(v):
    """Outscraper writes the literal string 'None' for missing values in several
    columns (county, owner_id). Treat it as empty so it never reaches a page."""
    v = (v or "").strip()
    return "" if v.lower() in ("none", "null", "n/a", "-") else v


def num(v, cast=float):
    try:
        return cast(float(v))
    except (TypeError, ValueError):
        return None


def subtypes(raw):
    out, seen2 = [], set()
    for p in re.split(r',', raw or ""):
        p = p.strip()
        if p and p.lower() not in seen2:
            seen2.add(p.lower())
            out.append(p)
    return out


def hours(raw):
    if not raw:
        return {}
    try:
        d = json.loads(raw)
    except ValueError:
        return {}
    out = {}
    for day in DAYS:
        v = d.get(day)
        out[day] = ", ".join(v) if isinstance(v, list) else (str(v) if v else "Closed")
    return out


def online_hours(raw):
    """other_hours is a list of {"<label>": {day: hours}} blocks."""
    if not raw:
        return {}
    try:
        blocks = json.loads(raw)
    except ValueError:
        return {}
    out = {}
    for block in blocks if isinstance(blocks, list) else []:
        for label, days in (block or {}).items():
            if isinstance(days, dict):
                pretty = label.replace("_", " ").strip().capitalize()
                out[pretty] = {d: days.get(d, "Closed") for d in DAYS}
    return out


def attributes(raw):
    """about -> {section: [attribute, ...]} keeping only the true flags."""
    if not raw:
        return {}
    try:
        d = json.loads(raw)
    except ValueError:
        return {}
    out = {}
    for section in ABOUT_SECTIONS:
        kv = d.get(section)
        if not isinstance(kv, dict):
            continue
        vals = [k for k, v in kv.items() if v is True]
        if vals:
            out[section] = sorted(vals)
    return out


def score_breakdown(r):
    out = {}
    for s in range(1, 6):
        n = num(g(r, f'reviews_per_score_{s}'), int)
        if n is not None:
            out[str(s)] = n
    if out:
        return out
    raw = g(r, 'reviews_per_score')
    if raw:
        try:
            return {str(k): int(v) for k, v in json.loads(raw).items()}
        except (ValueError, TypeError):
            pass
    return {}


def main():
    out = {}
    for r in recs:
        name = (g(r, 'name') or '').strip()
        city = (g(r, 'city') or '').strip()
        slug = uniq_slug(name, city)
        out[slug] = {
            "name": name,
            "city": city,
            "street": text(g(r, 'street')),
            "address": text(g(r, 'address')),
            "county": text(g(r, 'county')),
            "postal_code": text(g(r, 'postal_code')),
            "lat": num(g(r, 'latitude')),
            "lng": num(g(r, 'longitude')),
            "category": text(g(r, 'category')),
            "subtypes": subtypes(g(r, 'subtypes')),
            "rating": num(g(r, 'rating')),
            "reviews": num(g(r, 'reviews'), int),
            "reviews_link": url(g(r, 'reviews_link')),
            "scores": score_breakdown(r),
            "photos_count": num(g(r, 'photos_count'), int) or 0,
            "photo": url(g(r, 'photo')),
            "street_view": url(g(r, 'street_view')),
            "logo": url(g(r, 'logo')),
            "hours": hours(g(r, 'working_hours')),
            "other_hours": online_hours(g(r, 'other_hours')),
            "attributes": attributes(g(r, 'about')),
            "area_service": str(g(r, 'area_service') or '0') == '1',
            "time_zone": (g(r, 'time_zone') or '').strip(),
        }

    dest = os.path.join(ROOT, "data", "partner-details.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    live = {d for d in os.listdir(os.path.join(ROOT, "partners"))
            if os.path.isfile(os.path.join(ROOT, "partners", d, "index.html"))}

    def n(pred):
        return sum(1 for v in out.values() if pred(v))

    print(f"Wrote {len(out)} records -> data/partner-details.json")
    print(f"  photo {n(lambda v: v['photo'])}   logo {n(lambda v: v['logo'])}   "
          f"hours {n(lambda v: v['hours'])}   attributes {n(lambda v: v['attributes'])}   "
          f"score breakdown {n(lambda v: v['scores'])}   subtypes>1 {n(lambda v: len(v['subtypes']) > 1)}")
    print(f"  published partner pages: {len(live)}   matched: {len(live & set(out))}   "
          f"unmatched pages: {sorted(live - set(out))}")


if __name__ == "__main__":
    main()
