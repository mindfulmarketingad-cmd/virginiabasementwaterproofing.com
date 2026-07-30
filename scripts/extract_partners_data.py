#!/usr/bin/env python3
"""Build data/partners.json -- the flat roster the /partners/ and /reviews/ hubs render.

Sources, in order of authority:
  data/partner-details.json  (scripts/extract_outscraper.py) -- the Outscraper export
  data/va-providers.json                                     -- map categories, county, lat/lng
  partners/<slug>/                                           -- which slugs are actually published

Nothing is scraped back out of the generated HTML: the pages are downstream of
this file, so parsing them would be circular.
"""
import os, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_html import best_city_find_url  # noqa: E402

CAT_LABEL = {
    "waterproofing": "Basement Waterproofing",
    "crawl-space":   "Crawl Space Encapsulation",
    "foundation":    "Foundation Repair",
    "plumbing":      "Sump Pump Installation",
    "drainage":      "French Drains & Drainage",
    "water-damage":  "Water Damage Restoration",
    "restoration":   "Fire & Building Restoration",
    "concrete":      "Concrete & Masonry",
    "mold":          "Mold & Air Quality",
    "general":       "General Contracting",
}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def city_url(city, city_urls):
    """Best /find/ page for this city -- the old /virginia/<region>/<city>/ pages
    (what city_urls.json's raw values still encode) have been retired."""
    url = city_urls.get(city, "")
    if not url:
        return ""
    slug = url.strip("/").split("/")[-1]
    return best_city_find_url(ROOT, slug, preferred="waterproofing")


def text(v):
    """va-providers.json carries the literal string 'None' for missing counties."""
    v = (v or "").strip()
    return "" if v.lower() in ("none", "null", "n/a", "-") else v


def main():
    details = load("data/partner-details.json")
    providers = {r["slug"]: r for r in load("data/va-providers.json")}
    city_urls = load("scripts/city_urls.json")

    published = {d for d in os.listdir(os.path.join(ROOT, "partners"))
                 if os.path.isfile(os.path.join(ROOT, "partners", d, "index.html"))}

    out = []
    for slug in sorted(published):
        d = details.get(slug)
        if not d:
            continue
        p = providers.get(slug, {})
        hours = d.get("hours") or {}
        cats = p.get("cats") or []
        out.append({
            "slug": slug,
            "name": d["name"],
            "rating": d.get("rating"),
            "reviews": d.get("reviews"),
            "google_reviews_url": d.get("reviews_link") or "",
            "address": text(d.get("address")),
            "zip": d.get("postal_code") or p.get("zip", ""),
            "city": d.get("city") or p.get("city", ""),
            "city_url": city_url(d.get("city") or p.get("city", ""), city_urls),
            "county": text(d.get("county")) or text(p.get("county")),
            "lat": d.get("lat") if d.get("lat") is not None else p.get("lat"),
            "lng": d.get("lng") if d.get("lng") is not None else p.get("lng"),
            "category": text(d.get("category")),
            "services": d.get("subtypes") or [],
            "cats": cats,
            "cat_labels": [CAT_LABEL.get(c, c) for c in cats],
            "scores": d.get("scores") or {},
            "attributes": d.get("attributes") or {},
            "hours": hours,
            "other_hours": d.get("other_hours") or {},
            "open_24h": bool(hours) and all("24 hours" in v for v in hours.values()),
            "days_open": sum(1 for v in hours.values() if "closed" not in v.lower()),
            "photos_count": d.get("photos_count") or 0,
            "photo": d.get("photo", ""),
            "logo": d.get("logo", ""),
            "street_view": d.get("street_view", ""),
        })

    out.sort(key=lambda r: r["name"].lower())
    with open(os.path.join(ROOT, "data", "partners.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    def n(pred):
        return sum(1 for r in out if pred(r))

    print(f"Wrote {len(out)} partners -> data/partners.json")
    print(f"  rating {n(lambda r: r['rating'])}   reviews link {n(lambda r: r['google_reviews_url'])}"
          f"   photo {n(lambda r: r['photo'])}   hours {n(lambda r: r['hours'])}"
          f"   attributes {n(lambda r: r['attributes'])}   score breakdown {n(lambda r: r['scores'])}")
    missing = [r["slug"] for r in out if not r["city"] or not r["services"]]
    if missing:
        print(f"  incomplete records: {missing}")
    orphans = sorted(published - set(details))
    if orphans:
        print(f"  published pages with no Outscraper record: {orphans}")


if __name__ == "__main__":
    main()
