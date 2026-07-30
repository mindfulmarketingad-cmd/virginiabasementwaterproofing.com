#!/usr/bin/env python3
"""Retire the /virginia/<region>/<city>/ pages sitewide.

These 125 pages (one per named city) were thin, redundant with the much richer
/find/<service>-<city>-va/ searchmap pages, and are being removed entirely:
  - every href="/virginia/<region>/<city-slug>/" across the whole site is
    rewritten to the best available /find/<service>-<city-slug>-va/ page
    (preferring basement waterproofing; falling back through the other
    services -- basement-finishing/mold-removal/mold-remediation cover every
    city, so this always resolves to something real)
  - the 125 page directories themselves are deleted
  - vercel.json gets a 301 redirect for each retired URL, to the homepage

Safe to re-run: skips files with no matching links, and re-deleting an
already-deleted directory is a no-op.
"""
import os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from shared_html import best_city_find_url  # noqa: E402

with open(os.path.join(ROOT, "scripts", "city_urls.json"), encoding="utf-8") as f:
    CITY_URLS = json.load(f)

# every retired URL, keyed by its city-slug (last path segment)
RETIRED = {}   # city_slug -> old url
for name, url in CITY_URLS.items():
    parts = url.strip("/").split("/")
    if len(parts) == 3 and parts[0] == "virginia":
        RETIRED[parts[2]] = url

LINK_RE = re.compile(r'href="(/virginia/[a-z-]+/([a-z0-9-]+)/)"')


def replacement_for(old_url, city_slug):
    if city_slug not in RETIRED:
        return None  # not one of the retired city pages (e.g. a region hub link)
    return best_city_find_url(ROOT, city_slug, preferred="waterproofing")


def patch_links():
    scanned = changed_files = changed_links = 0
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "scripts", "node_modules")]
        for fn in files:
            if not fn.endswith(".html"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                src = f.read()
            scanned += 1

            def sub(m):
                nonlocal changed_links
                new = replacement_for(m.group(1), m.group(2))
                if new is None:
                    return m.group(0)
                changed_links += 1
                return f'href="{new}"'

            new_src = LINK_RE.sub(sub, src)
            if new_src != src:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_src)
                changed_files += 1
    print(f"Scanned {scanned} html files, rewrote {changed_links} links across {changed_files} files")


def delete_pages():
    removed = 0
    for city_slug, url in RETIRED.items():
        region = url.strip("/").split("/")[1]
        d = os.path.join(ROOT, "virginia", region, city_slug)
        if os.path.isdir(d):
            for root, dirs, files in os.walk(d, topdown=False):
                for fn in files:
                    os.remove(os.path.join(root, fn))
                os.rmdir(root)
            removed += 1
    print(f"Removed {removed} /virginia/<region>/<city>/ page directories")


def add_redirects():
    path = os.path.join(ROOT, "vercel.json")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    existing = {r["source"] for r in cfg["redirects"]}
    added = 0
    for city_slug, url in sorted(RETIRED.items()):
        src_slash = url  # already has leading+trailing slash
        src_bare = url.rstrip("/")
        for src in (src_bare, src_slash):
            if src not in existing:
                cfg["redirects"].append({"source": src, "destination": "/", "permanent": True})
                existing.add(src)
                added += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print(f"Added {added} redirect entries to vercel.json ({len(cfg['redirects'])} total)")


def main():
    print(f"{len(RETIRED)} city pages to retire")
    patch_links()
    delete_pages()
    add_redirects()


if __name__ == "__main__":
    main()
