#!/usr/bin/env python3
"""Rebuild sitemap.xml by walking the published tree.

Replaces the previously hand-maintained file, which had drifted (stale
/services/ URLs, entries for pages that no longer exist).
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.virginiabasementwaterproofing.org"

SKIP_DIRS = {".git", "scripts", "js", "css", "data", "img", "images", "node_modules"}
NOINDEX = re.compile(r'<meta name="robots" content="[^"]*noindex', re.I)

# most specific prefix wins
PRIORITY = [
    ("/find/",     "weekly",  "0.8"),
    ("/reviews/",  "weekly",  "0.7"),
    ("/partners/", "weekly",  "0.7"),
    ("/virginia/", "monthly", "0.7"),
    ("/blog/",     "weekly",  "0.6"),
]
HUBS = {
    "/":            ("weekly",  "1.0"),
    "/find/":       ("daily",   "1.0"),
    "/partners/":   ("weekly",  "0.9"),
    "/reviews/":    ("weekly",  "0.9"),
    "/virginia/":   ("weekly",  "0.9"),
    "/get-a-quote/": ("monthly", "0.9"),
    "/claim-listing/": ("monthly", "0.8"),
    "/about/":      ("monthly", "0.6"),
    "/blog/":       ("weekly",  "0.7"),
}
LOW = {"/privacy-policy/", "/terms-of-service/", "/disclaimer/"}


def classify(url):
    if url in HUBS:
        return HUBS[url]
    if url in LOW:
        return ("yearly", "0.2")
    for prefix, freq, pri in PRIORITY:
        if url.startswith(prefix):
            return (freq, pri)
    return ("monthly", "0.8")   # city and city+service money pages


def main():
    urls = []
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        if "index.html" not in files:
            continue
        path = os.path.join(dirpath, "index.html")
        with open(path, encoding="utf-8") as f:
            head = f.read(4000)
        if NOINDEX.search(head):
            continue
        rel = os.path.relpath(dirpath, ROOT)
        url = "/" if rel == "." else "/" + rel.replace(os.sep, "/") + "/"
        urls.append(url)

    urls.sort(key=lambda u: (u != "/", u))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        freq, pri = classify(u)
        lines.append(f"  <url><loc>{BASE}{u}</loc>"
                     f"<changefreq>{freq}</changefreq><priority>{pri}</priority></url>")
    lines.append("</urlset>")

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    def n(prefix):
        return sum(1 for u in urls if u.startswith(prefix))

    print(f"sitemap.xml: {len(urls)} URLs "
          f"(find {n('/find/')}, reviews {n('/reviews/')}, partners {n('/partners/')}, "
          f"virginia {n('/virginia/')}, blog {n('/blog/')})")


if __name__ == "__main__":
    main()
