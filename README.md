# VirginiaBasementWaterproofing.com

A minimalistic, authoritative directory website connecting Virginia homeowners with
licensed basement waterproofing contractors. Static HTML/CSS/JS — no build step required.

## Site Structure

```
/                                         Homepage (H1: Virginia Basement Waterproofing)
/services/                                Services hub
/services/[service-slug]/                 Individual service page (e.g. basement-waterproofing)
/virginia/                                State hub (cities)
/virginia/[region]/                       Regional hub (e.g. hampton-roads)
/virginia/[region]/[city]/                City page (e.g. .../virginia-beach)
/[city]/[service]/                        SEO money page (e.g. /virginia-beach/basement-waterproofing/)
/partners/                                Partner / contractor hub
/partners/[contractor-slug]/              Individual partner page
/get-a-quote/                             Lead capture form
/about/                                   About page
/blog/                                    Blog index
```

### Legal & SEO files (Google AdSense ready)
- `/privacy-policy/` — Privacy Policy (cookies + AdSense disclosures)
- `/terms-of-service/` — Terms of Service
- `/disclaimer/` — Disclaimer (directory, not a contractor)
- `/sitemap.xml`, `/robots.txt`, `/ads.txt`, `/404.html`

## Example pages already built (templates to clone)
- Service: `/services/basement-waterproofing/`
- Region: `/virginia/hampton-roads/`
- City: `/virginia/hampton-roads/virginia-beach/`
- City landing: `/virginia-beach/`
- Money page: `/virginia-beach/basement-waterproofing/`
- Partner: `/partners/tidewater-dry-basements/`

To add a new page, copy the matching example folder, rename it, and update the
content, `<title>`, meta description, canonical URL, and breadcrumb. Then add the
new URL to `sitemap.xml`.

## Assets
- `/css/styles.css` — all global styles (responsive, mobile menu, forms, cards)
- `/js/main.js` — mobile nav, ZIP search redirect, quote-form confirmation, footer year

## Before going live
1. Replace `ca-pub-XXXXXXXXXXXXXXXX` (AdSense client) in each page's `<head>`.
2. Replace `pub-XXXXXXXXXXXXXXXX` in `ads.txt` after AdSense approval.
3. Wire the quote forms (`<form data-quote>`) to a backend / email service. They
   currently show a client-side confirmation only.
4. Confirm the canonical domain (https://virginiabasementwaterproofing.com).

## Contact
Phone: (757) 743-9050
