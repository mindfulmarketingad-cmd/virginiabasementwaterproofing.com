#!/usr/bin/env python3
"""Shared page-assembly helper for hand-authored blog posts.

Blog posts themselves are one-off content (not templated like /find/), but the
surrounding shell -- header, footer, JSON-LD wrapper, sidebar boilerplate --
is identical everywhere and easy to get subtly wrong by hand-copying it 16
times. This module assembles that shell from shared_html.py (so nav/footer
service links always match the rest of the site) around content each post
script supplies.
"""
import os, sys, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.virginiabasementwaterproofing.org"
ADSENSE = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
           '?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>')

sys.path.insert(0, os.path.join(ROOT, "scripts"))
from shared_html import SITE_HEADER, FOOTER  # noqa: E402


def esc(s):
    return html.escape(str(s or ""), quote=True)


def faq_schema(qa_pairs):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qa_pairs],
    })


def faq_html(qa_pairs, heading="Frequently Asked Questions"):
    items = "".join(f'<div class="faq-item"><h2>{q}</h2><p>{a}</p></div>' for q, a in qa_pairs)
    return f'<h2>{heading}</h2>\n        <div class="faq-list">{items}</div>'


def related_reading(items):
    """items: list of (href, label) tuples."""
    lis = "".join(f'<li><a href="{h}">{l}</a></li>' for h, l in items)
    return (f'<div class="fact-card" style="margin-bottom:22px;">'
            f'<h3 style="margin-top:0; font-size:1rem;">Related Reading</h3>'
            f'<ul style="font-size:.9rem; padding-left:18px; margin:0;">{lis}</ul></div>')


def build(slug, title_tag, h1, description, date, read_time, body_html, sidebar_html,
          og_image=None, extra_schema=None):
    """Assemble and write blog/<slug>/index.html."""
    og = f'\n<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    extra = f'\n<script type="application/ld+json">{extra_schema}</script>' if extra_schema else ""

    article_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": h1,
        "description": description,
        "image": og_image or f"{BASE}/favicon.svg",
        "publisher": {"@type": "Organization", "name": "Virginia Basement Waterproofing",
                     "url": f"{BASE}/"},
        "mainEntityOfPage": f"{BASE}/blog/{slug}/",
        "datePublished": date,
    })

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_tag)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{BASE}/blog/{slug}/">
<meta name="robots" content="index, follow">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(h1)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{BASE}/blog/{slug}/">{og}
<link rel="stylesheet" href="/css/styles.css">
{ADSENSE}
<script type="application/ld+json">{article_schema}</script>{extra}
</head>
<body>

{SITE_HEADER}

<div class="page-head">
  <div class="container">
    <div class="breadcrumb"><a href="/">Home</a> / <a href="/blog/">Blog</a> / {esc(h1)}</div>
    <h1>{esc(h1)}</h1>
    <p class="text-muted" style="font-size:.9rem; margin-top:8px;">Published {date_disp(date)} &nbsp;&middot;&nbsp; {read_time} min read</p>
  </div>
</div>

<main>
<article>
<section class="section">
  <div class="container">
    <div class="grid-2" style="align-items:start; gap:48px;">

      <div class="prose">
{body_html}
      </div>

      <aside>
{sidebar_html}
      </aside>

    </div>
  </div>
</section>
</article>
</main>

{FOOTER}

<script src="/js/main.js"></script>
</body>
</html>
'''
    out_dir = os.path.join(ROOT, "blog", slug)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    return page


def date_disp(iso):
    import datetime
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")


def cta_card(provider_find="/find/", quote_note="A licensed Virginia contractor can help — free estimate, no obligation."):
    return f'''<div class="fact-card">
          <h3 style="margin-top:0; font-size:1rem;">Ready to Get This Fixed?</h3>
          <p class="text-muted" style="font-size:.88rem;">{quote_note}</p>
          <a href="/get-a-quote/" class="btn btn--primary btn--block" style="margin-bottom:10px;">Call or Text for Quote</a>
          <a href="{provider_find}" class="btn btn--blue btn--block">Find a pro near me</a>
        </div>'''
