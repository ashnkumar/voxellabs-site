#!/usr/bin/env python3
"""
Render every markdown file in content/ into a project page under projects/<slug>/.

    python3 build.py

The site itself has no build step — Vercel just serves what's committed. This
script exists so the writeups stay editable as markdown: edit content/<slug>.md,
re-run this, commit the generated HTML.

Images: any remote <img> is rewritten to projects/<slug>/img/<name>.webp. Fetch
and convert them once with fetch_images(), then they're served from the repo —
a writeup that depends on someone else's image host is a writeup with a
time bomb in it.

Requires: python-markdown (`pip install markdown`). cwebp for image conversion.
"""

import html
import os
import re
import subprocess
import sys
import urllib.request

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "projects")

FONTS = ("https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,300..600"
         "&family=Instrument+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap")

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E"
           "%3Crect width='24' height='24' rx='6' fill='%230d0d0d'/%3E%3Cpath d='M7 8.5l5 7 5-7' "
           "stroke='%23828df5' stroke-width='1.8' fill='none' stroke-linecap='round' "
           "stroke-linejoin='round'/%3E%3C/svg%3E")


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #

def split_front_matter(text):
    """Leading `---` block of `key: value` lines. No YAML dependency."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("\n---", 3)
    meta = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[end + 4:].lstrip("\n")


def find_remote_images(md):
    return re.findall(r"!\[[^\]]*\]\((https?://[^)\s]+)\)", md)


IMAGE_LINE = re.compile(r"^!\[[^\]]*\]\([^)\s]+\)\s*$")
LIST_LINE = re.compile(r"^(?:[*+-]|\d+\.)\s+")


def normalise(md):
    """DevPost writes without the blank lines markdown needs.

    Images and lists get glued onto the preceding paragraph, so they render as
    an inline <img> and a run-on sentence instead of a figure and an <ol>.
    Inserting the blank lines here means every future writeup can be pasted in
    exactly as it came out of DevPost.
    """
    out = []
    for line in md.split("\n"):
        blank = not out or not out[-1].strip()
        starts_block = IMAGE_LINE.match(line) or LIST_LINE.match(line)
        prev_is_list = bool(out) and bool(LIST_LINE.match(out[-1]))
        if starts_block and not blank and not (prev_is_list and LIST_LINE.match(line)):
            out.append("")
        out.append(line)
        if IMAGE_LINE.match(line):
            out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# images
# --------------------------------------------------------------------------- #

def fetch_images(slug, urls):
    """Download each remote image once and convert it to webp in the repo."""
    img_dir = os.path.join(OUT, slug, "img")
    os.makedirs(img_dir, exist_ok=True)
    for url in urls:
        name = os.path.splitext(os.path.basename(url))[0]
        dest = os.path.join(img_dir, name + ".webp")
        if os.path.exists(dest):
            continue
        print(f"  fetching {url}")
        tmp = os.path.join(img_dir, "." + name + ".tmp")
        req = urllib.request.Request(url, headers={"User-Agent": "voxellabs-site/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as f:
            f.write(r.read())
        subprocess.run(["cwebp", "-quiet", "-q", "84", "-resize", "2000", "0", tmp, "-o", dest],
                       check=True)
        os.remove(tmp)


def localise(md):
    """Rewrite remote image URLs to the local webp copy."""
    def sub(m):
        name = os.path.splitext(os.path.basename(m.group(2)))[0]
        return f"![{m.group(1)}](img/{name}.webp)"
    return re.sub(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)", sub, md)


# --------------------------------------------------------------------------- #
# html post-processing
# --------------------------------------------------------------------------- #

def promote_figures(body):
    """A paragraph that is nothing but an image becomes a click-to-open figure."""
    def sub(m):
        img = m.group(1)
        src = re.search(r'src="([^"]+)"', img).group(1)
        img = img.replace("<img ", '<img loading="lazy" decoding="async" ', 1)
        return (f'<figure><a href="{src}" target="_blank" rel="noopener" '
                f'aria-label="Open the full-size diagram">{img}</a></figure>')
    return re.sub(r"<p>(<img[^>]*>)</p>", sub, body)


def promote_callouts(body):
    """DevPost writes its lead note as _**Note:** …_ — render it as a callout."""
    return re.sub(r"<p>(<em><strong>.*?)</p>", r'<aside class="callout">\1</aside>',
                  body, count=1, flags=re.S)


# --------------------------------------------------------------------------- #
# page
# --------------------------------------------------------------------------- #

def page(meta, body):
    e = lambda k, d="": html.escape(meta.get(k, d) or "", quote=True)
    title, deck = e("title"), e("deck")
    url = f"https://voxellabs.ai/projects/{e('slug')}"

    crumbs = [f'<span>{e("year")}</span>'] if meta.get("year") else []
    if meta.get("comp"):
        crumbs.append(f'<span>{e("comp")}</span>')
    crumb_html = '<span class="sep">·</span>'.join(crumbs)
    if meta.get("award"):
        crumb_html += f'<span class="award">{e("award")}</span>'

    bar = ['<a href="/projects" class="back"><span class="arrow">&#8592;</span> All projects</a>']
    if meta.get("vimeo"):
        bar.append(f'<a href="https://vimeo.com/{e("vimeo")}" target="_blank" rel="noopener" '
                   f'class="back">Watch the demo <span class="arrow">&#8599;</span></a>')
    if meta.get("repo"):
        bar.append(f'<a href="{e("repo")}" target="_blank" rel="noopener" class="back">'
                   f'Source <span class="arrow">&#8599;</span></a>')

    chips = "".join(f'<span class="chip">{html.escape(s.strip())}</span>'
                    for s in meta.get("stack", "").split(",") if s.strip())

    # the writeup gets shared directly, so it carries the video itself rather than
    # assuming everyone arrived via the index. Facade, not an embed — see site.js.
    hero_video = ""
    if meta.get("vimeo"):
        poster = (f'<img src="{e("poster")}" alt="" fetchpriority="high" decoding="async">'
                  if meta.get("poster") else "")
        hero_video = (
            f'<button class="pj-media art-video" data-vimeo="{e("vimeo")}" '
            f'data-title="{title}" aria-label="Play the {title} demo">{poster}'
            f'<span class="pj-scrim"><span class="pj-play">'
            f'<svg viewBox="0 0 12 14" aria-hidden="true"><path d="M0 0l12 7-12 7z"/></svg>'
            f'</span></span></button>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Voxel Labs</title>
<meta name="description" content="{deck}">
<meta name="theme-color" content="#0d0d0d">
<link rel="canonical" href="{url}">
<link rel="icon" href="{FAVICON}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title} — Voxel Labs">
<meta property="og:description" content="{deck}">
<meta property="og:image" content="https://voxellabs.ai/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
</head>
<body>

<nav class="nav" id="nav">
  <div class="wrap nav-in">
    <a href="/" class="brand">
      <svg class="mk" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="1.5" y="1.5" width="21" height="21" rx="6" stroke="#828df5" stroke-width="1.4"/>
        <path d="M7 8.5l5 7 5-7" stroke="#828df5" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>Voxel Labs</span>
    </a>
    <div class="nav-links">
      <a href="/#build">What we build</a>
      <a href="/#how">How we work</a>
      <a href="/#work">Our work</a>
      <a href="/#cortana">Cortana</a>
      <a href="/projects" class="on">Projects</a>
    </div>
    <a href="mailto:ashwin@voxellabs.ai" class="btn btn-accent nav-cta">Get in touch</a>
  </div>
</nav>

<header class="phead">
  <div class="wrap">
    <div class="art-hero">
      <p class="pj-comp rv">{crumb_html}</p>
      <h1 class="rv">{title}</h1>
      <p class="lede rv rv-2">{deck}</p>
      <div class="pj-stk rv rv-2">{chips}</div>
      <div class="art-bar rv rv-3">{"".join(bar)}</div>
    </div>
  </div>
</header>

<div class="wrap">
  <article class="art-body">
{hero_video}
{body}
  </article>

  <div class="art-foot">
    <a href="/projects" class="back"><span class="arrow">&#8592;</span> All projects</a>
    <p class="byline">Voxel Labs — <b>Ashwin Kumar, CEO</b></p>
  </div>
</div>

<section class="cta">
  <div class="wrap">
    <h2 class="rv">Let's build your next agent.</h2>
    <a href="mailto:ashwin@voxellabs.ai" class="btn btn-accent rv rv-2">Get in touch <span class="arrow">&#8599;</span></a>
  </div>
</section>

<footer>
  <div class="wrap">
    <p>Voxel Labs AI, LLC · 2026</p>
    <p><a href="mailto:ashwin@voxellabs.ai">ashwin@voxellabs.ai</a></p>
  </div>
</footer>

<script src="/site.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------- #

def build(path):
    raw = open(path, encoding="utf-8").read()
    meta, md = split_front_matter(raw)
    slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
    print(f"{slug}:")

    remote = find_remote_images(md)
    if remote:
        fetch_images(slug, remote)
        md = localise(md)

    md = re.sub(r"(?:\s*<br\s*/?>\s*)+\n", "\n\n", md)   # DevPost pads with <br>; CSS handles spacing
    md = normalise(md)

    body = markdown.markdown(md, extensions=["extra", "sane_lists", "smarty"])
    body = promote_figures(body)
    body = promote_callouts(body)

    out_dir = os.path.join(OUT, slug)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(page(meta, body))
    print(f"  -> projects/{slug}/index.html  ({os.path.getsize(out_file)//1024} KB)")


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(
        os.path.join(CONTENT, f) for f in os.listdir(CONTENT) if f.endswith(".md"))
    if not files:
        sys.exit("no markdown in content/")
    for f in files:
        build(f)
