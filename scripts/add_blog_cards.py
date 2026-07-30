#!/usr/bin/env python3
"""Add cards for the black-mold and damp-basement/wet-wall clusters to
blog/index.html, right after the existing French-drain cards. Idempotent --
skips any slug that already has a card.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "blog", "index.html")

DATE_MOLD = "July 31, 2026"
DATE_DAMP = "August 1, 2026"

NEW_CARDS = [
    (DATE_MOLD, "what-is-black-mold", "What Is Black Mold?",
     "What \"black mold\" actually refers to, why several mold species can look black, and what it needs to grow."),
    (DATE_MOLD, "what-causes-black-mold", "What Causes Black Mold?",
     "Where black mold's moisture actually comes from -- basement seepage, leaks, condensation, humidity -- and why cleaning without fixing the source never solves it."),
    (DATE_MOLD, "how-to-get-rid-of-black-mold", "How To Get Rid Of Black Mold?",
     "A detailed, step-by-step removal process: what you can clean, what you need to remove instead, containment, drying, and fixing the moisture source."),
    (DATE_MOLD, "who-can-get-rid-of-black-mold", "Who Can Get Rid Of Black Mold?",
     "Who actually does mold work, the questions worth asking before hiring, and what it costs."),
    (DATE_MOLD, "is-black-mold-deadly", "Is Black Mold Deadly?",
     "A careful, hedged look at what's actually established about black mold health risk versus the sensationalized \"toxic mold\" narrative -- not medical advice."),
    (DATE_MOLD, "can-i-get-out-of-my-lease-if-i-have-black-mold", "Can I Get Out Of My Lease If I Have Black Mold?",
     "Habitability law, tenant remedies, and Virginia's landlord-tenant act as they relate to mold -- not legal advice."),
    (DATE_DAMP, "why-is-my-basement-damp", "Why Is My Basement Damp?",
     "The two very different problems people call \"basement dampness\" -- liquid water intrusion versus humidity and condensation -- and a test to tell them apart."),
    (DATE_DAMP, "why-is-there-water-in-my-basement", "Why Is There Water In My Basement?",
     "The real sources of actual water in a basement -- hydrostatic pressure, cracks, window wells, sump failure, plumbing leaks -- and how to trace it back."),
    (DATE_DAMP, "who-can-dehumidify-my-basement", "Who Can Dehumidify My Basement?",
     "Sizing a dehumidifier correctly, portable vs. whole-home systems, and when dehumidification alone won't be enough."),
    (DATE_DAMP, "why-are-my-basement-walls-wet", "Why Are My Basement Walls Wet?",
     "The two real mechanisms behind wet basement walls and a simple test to tell them apart before you pay for the wrong fix."),
    (DATE_DAMP, "how-to-fix-a-wet-basement-wall", "How Do You Fix A Wet Basement Wall?",
     "The real repair options for a wet basement wall, from cheapest to most involved, and how to pick the right one."),
    (DATE_DAMP, "how-to-keep-moisture-out-of-basement-walls", "How To Keep Moisture Out Of Basement Walls",
     "The seasonal maintenance habits that actually keep a repaired basement wall dry long term."),
    (DATE_DAMP, "why-is-my-wall-wet-but-no-leak", "Why Is My Wall Wet But No Leak?",
     "Why a basement wall can be wet with no leak at all -- the condensation mechanism and how to confirm it."),
    (DATE_DAMP, "why-is-my-basement-floor-wet-but-no-leak", "Why Is My Basement Floor Wet But No Leak?",
     "Rising damp through the slab versus condensation, and the moisture tests that tell them apart before you install flooring."),
    (DATE_DAMP, "what-draws-moisture-out-of-walls", "What Draws Moisture Out Of Walls?",
     "How moisture actually leaves a wall -- evaporation, airflow, dehumidification, and capillary breaks."),
    (DATE_DAMP, "how-can-i-tell-if-there-is-moisture-in-my-walls", "How Can I Tell If There Is Moisture In My Walls?",
     "The actual detection methods for wall and floor moisture, and when each one is worth using."),
]


def card(date, slug, title, desc):
    return f'''      <article class="card">
        <div class="text-muted" style="font-size:.8rem; text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px; font-weight:700;">{date}</div>
        <h3><a href="/blog/{slug}/" style="color:var(--navy);">{title}</a></h3>
        <p class="text-muted">{desc}</p>
        <p><a href="/blog/{slug}/">Read article &rarr;</a></p>
      </article>
'''


def main():
    with open(PATH, encoding="utf-8") as f:
        src = f.read()

    anchor = '<h3><a href="/blog/how-to-clean-a-french-drain/" style="color:var(--navy);">How To Clean a French Drain</a></h3>'
    idx = src.find(anchor)
    if idx == -1:
        raise SystemExit("anchor card not found -- blog/index.html structure may have changed")
    end = src.find("</article>", idx) + len("</article>")

    added = 0
    cards = ""
    for date, slug, title, desc in NEW_CARDS:
        if f'href="/blog/{slug}/"' in src:
            continue
        cards += "\n" + card(date, slug, title, desc)
        added += 1

    new_src = src[:end] + cards + src[end:]
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_src)
    print(f"Added {added} new cards to blog/index.html")


if __name__ == "__main__":
    main()
