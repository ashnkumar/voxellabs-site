#!/usr/bin/env python3
"""
Pull a Vimeo video's thumbnail into the repo as a poster frame.

    python3 poster.py <vimeo-id> <name>
    python3 poster.py 22439234 logcraft-rag

Writes assets/posters/<name>.webp, which the PROJECTS entry references as its
`poster`. Same reasoning as the writeup images: the index shouldn't hot-link
someone else's CDN, and a poster we serve ourselves loads with the page instead
of after it.

Uses Vimeo's public oEmbed endpoint — no API key, no auth.
"""

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "posters")

# oEmbed returns a thumbnail sized to the width you ask for, so ask big
OEMBED = "https://vimeo.com/api/oembed.json?url={}&width=1600"


def fetch(url, **kw):
    req = urllib.request.Request(url, headers={"User-Agent": "voxellabs-site/1.0"}, **kw)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main(vimeo_id, name):
    meta = json.loads(fetch(OEMBED.format(
        urllib.parse.quote(f"https://vimeo.com/{vimeo_id}", safe=""))))
    thumb = meta["thumbnail_url"]
    print(f'  "{meta.get("title", "?")}"  {meta.get("width")}x{meta.get("height")}')
    print(f"  thumbnail {thumb}")

    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, "." + name + ".tmp")
    dest = os.path.join(OUT, name + ".webp")
    with open(tmp, "wb") as f:
        f.write(fetch(thumb))
    subprocess.run(["cwebp", "-quiet", "-q", "82", "-resize", "1280", "0", tmp, "-o", dest],
                   check=True)
    os.remove(tmp)
    print(f"  -> assets/posters/{name}.webp  ({os.path.getsize(dest) // 1024} KB)")
    print(f'\n  In the PROJECTS entry:  vimeo:"{vimeo_id}", poster:"/assets/posters/{name}.webp"')


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
