#!/usr/bin/env python3
"""Rewrite the primary header nav on every generated page to:
      Home | Find | Reviews | Partners | About

Also refreshes the footer "Explore" column and repoints footer service links at
the new /find/<service>-va/ searchmap pages. Idempotent.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_html import MAIN_NAV, SERVICE_BY_SLUG  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The old nav had a Services mega-menu plus a varying tail of links, so match
# the whole <nav> block rather than any one variant.
NAV_RE = re.compile(
    r'<nav class="main-nav" id="main-nav" aria-label="Primary">.*?</nav>', re.S)

FOOTER_EXPLORE_RE = re.compile(r"(<h4>Explore</h4>)<ul>.*?</ul>", re.S)
FOOTER_EXPLORE_NEW = (
    r'\1<ul><li><a href="/find/">Find a Pro</a></li>'
    '<li><a href="/reviews/">Reviews</a></li>'
    '<li><a href="/partners/">Partners</a></li>'
    '<li><a href="/virginia/">Cities</a></li>'
    '<li><a href="/get-a-quote/">Free Estimate</a></li>'
    '<li><a href="/blog/">Blog</a></li></ul>'
)

# /services/<slug>/ -> /find/<find>-va/  (only for the 12 known services;
# a bare /services/ link becomes the /find/ hub)
SERVICE_LINKS = {
    f'href="/services/{slug}/"': f'href="/find/{s["find"]}-va/"'
    for slug, s in SERVICE_BY_SLUG.items()
}

NAV_BLOCK = "    " + MAIN_NAV


def patch(html):
    html = NAV_RE.sub(lambda m: MAIN_NAV, html, count=1)
    html = FOOTER_EXPLORE_RE.sub(FOOTER_EXPLORE_NEW, html, count=1)
    for old, new in SERVICE_LINKS.items():
        html = html.replace(old, new)
    html = html.replace('href="/services/"', 'href="/find/"')
    # breadcrumbs that read "Home / Services / X" now point at the Find hub
    html = html.replace('<a href="/find/">Services</a>', '<a href="/find/">Find</a>')
    html = html.replace('<a href="/find/">View All Services &rarr;</a>',
                        '<a href="/find/">View All Services &rarr;</a>')
    return html


def main():
    scanned = changed = 0
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "scripts", "node_modules")]
        for fn in files:
            if not fn.endswith(".html"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                orig = f.read()
            scanned += 1
            new = patch(orig)
            if new != orig:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                changed += 1
    print(f"Scanned {scanned} html files, patched {changed}")


if __name__ == "__main__":
    main()
