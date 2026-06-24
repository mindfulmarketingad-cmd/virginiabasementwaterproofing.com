#!/usr/bin/env python3
"""Patch every .html file site-wide for the header/footer refresh:
  - brand text mark  -> VBW image logo
  - remove "Contractors" (/partners/) nav link + footer link
  - remove "Free Estimate" link from the HEADER nav only (footer keeps it)
  - strip emoji icons from the services mega-menu dropdown
  - repoint any stray /partners/ directory links to /virginia/
Idempotent: running twice is a no-op.
"""
import os, re

ROOT = "/home/user/virginiabasementwaterproofing.com"

BRAND_OLD = '<span class="brand__mark"><span class="bm-v">V</span><span class="bm-bw">BW</span></span>'
BRAND_NEW = '<img class="brand__logo" src="/img/vbw-logo.svg" alt="VBW — Virginia Basement Waterproofing" width="62" height="26">'

NAV_OLD = ('      <a href="/virginia/">Cities</a>\n'
           '      <a href="/partners/">Contractors</a>\n'
           '      <a href="/get-a-quote/">Free Estimate</a>\n'
           '    </nav>')
NAV_NEW = ('      <a href="/virginia/">Cities</a>\n'
           '    </nav>')

FOOTER_OLD = '<li><a href="/partners/">Contractors</a></li>'

icon_re = re.compile(r'\s*<span class="mega-menu__icon">.*?</span>', re.S)

changed = 0
scanned = 0
for dirpath, _dirs, files in os.walk(ROOT):
    if "/.git" in dirpath:
        continue
    for fn in files:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, encoding="utf-8") as f:
            html = f.read()
        scanned += 1
        orig = html

        html = html.replace(BRAND_OLD, BRAND_NEW)
        html = html.replace(NAV_OLD, NAV_NEW)
        # fallback: remove either nav link individually if the combined block didn't match
        html = html.replace('      <a href="/partners/">Contractors</a>\n', '')
        html = html.replace('      <a href="/get-a-quote/">Free Estimate</a>\n    </nav>', '    </nav>')
        html = html.replace(FOOTER_OLD, '')
        html = icon_re.sub('', html)
        # any remaining bare /partners/ directory link -> /virginia/
        html = html.replace('href="/partners/"', 'href="/virginia/"')
        html = html.replace('href="/partners/" style="color:#cfe0f0;"', 'href="/virginia/" style="color:#cfe0f0;"')

        if html != orig:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            changed += 1

print(f"Scanned {scanned} html files, patched {changed}")
