#!/usr/bin/env python3
"""Generate api/analytics/_listings.json -- the slug -> business/city lookup the
serverless tracking function uses to resolve a listing path into a business name
and city, server-side.

Kept as a generated file (rather than reading data/partners.json at request
time) so the serverless function has a single small dependency it can bundle,
and so it stays in sync via a regeneration step rather than by accident.

Re-run after scripts/extract_partners_data.py.
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    with open(os.path.join(ROOT, "data", "partners.json"), encoding="utf-8") as f:
        partners = json.load(f)
    with open(os.path.join(ROOT, "scripts", "city_urls.json"), encoding="utf-8") as f:
        city_urls = json.load(f)

    # slug -> [business name, city display name]
    listings = {}
    for p in partners:
        listings[p["slug"]] = [p["name"], p.get("city") or ""]

    # city slug -> display name, so /find/<svc>-<city>-va/ resolves to a real name
    cities = {}
    for name, url in city_urls.items():
        cities[url.strip("/").split("/")[-1]] = name

    out_dir = os.path.join(ROOT, "api", "analytics")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "_listings.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump({"listings": listings, "cities": cities}, f,
                  ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(dest)
    print(f"Wrote api/analytics/_listings.json "
          f"({len(listings)} listings, {len(cities)} cities, {size:,} bytes)")


if __name__ == "__main__":
    main()
