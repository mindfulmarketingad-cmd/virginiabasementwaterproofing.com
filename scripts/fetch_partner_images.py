#!/usr/bin/env python3
"""Optional: mirror the hotlinked Google business photos into /images/partners/.

Google's lh3.googleusercontent.com URLs rotate, so the hotlinked featured images
will eventually 404 (they fail soft -- the figure removes itself). Run this from
a machine with outbound access to googleusercontent.com to self-host them:

    python3 scripts/fetch_partner_images.py
    python3 scripts/patch_partner_images.py     # rewrites pages to /images/partners/
    python3 scripts/gen_directory.py

It rewrites data/partner-images.json in place, replacing remote URLs with local
paths, so the two patch/generate steps above pick the local copies up with no
further changes. Already-downloaded files are skipped, so it is safe to re-run
after a partial download.
"""
import os, json, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "images", "partners")
DATA = os.path.join(ROOT, "data", "partner-images.json")
UA = "Mozilla/5.0 (compatible; VBWDirectoryBot/1.0)"
TIMEOUT = 30


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return "cached"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read()
    if not data:
        raise ValueError("empty response")
    with open(path, "wb") as f:
        f.write(data)
    return "downloaded"


def main():
    os.makedirs(DEST, exist_ok=True)
    with open(DATA, encoding="utf-8") as f:
        images = json.load(f)

    counts = {"downloaded": 0, "cached": 0, "failed": 0, "local": 0}
    for slug, rec in images.items():
        for kind in ("photo", "logo", "street_view"):
            url = rec.get(kind) or ""
            if not url:
                continue
            if url.startswith("/"):
                counts["local"] += 1
                continue
            name = f"{slug}-{kind}.jpg"
            path = os.path.join(DEST, name)
            try:
                counts[fetch(url, path)] += 1
                rec[kind] = f"/images/partners/{name}"
            except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as e:
                counts["failed"] += 1
                print(f"  ! {slug} {kind}: {e}")

    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(images, f, indent=1, ensure_ascii=False)

    print(f"downloaded {counts['downloaded']}, cached {counts['cached']}, "
          f"already local {counts['local']}, failed {counts['failed']}")
    print("Now run: python3 scripts/patch_partner_images.py && python3 scripts/gen_directory.py")


if __name__ == "__main__":
    main()
