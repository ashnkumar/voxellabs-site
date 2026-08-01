# voxellabs.ai

Static site, no framework. Vercel serves exactly what's committed — there is no
deploy-time build.

```
/                        index.html          the landing page
/projects                projects/index.html the index of talks, demos and writeups
/projects/<slug>         projects/<slug>/    one writeup per project, generated
/style.css                                   the whole design system, every page
/site.js                                     nav state, scroll reveal, video facades
```

## Editing

**Landing page** — sections and headings are inline; the case studies and phase map
are the `WORK` and `PHASES` objects in the `<script>` at the bottom. Edit the data,
not the markup.

**Projects index** — the `PROJECTS` array at the bottom of `projects/index.html`.
Add an entry, it renders. Entries appear in array order. Fields are documented in
place; the ones that matter:

- `vimeo` — a numeric Vimeo id turns the tile into a click-to-play facade. Leave it
  null and the tile renders as "video pending" instead.
- `stub: true` — marks a row as scaffolding rather than content (dimmed, italic
  title, `PLACEHOLDER` chip). Drop it once the entry is real.
- `year` / `award` — leave out anything unverified. `—` is better than a wrong year.

**Writeups** — markdown in `content/<slug>.md`, with a `---` front-matter block for
title, deck, year, competition, award, repo, vimeo and stack. Then:

```
python3 build.py                    # all of content/
python3 build.py content/foo.md     # just one
```

Requires `python-markdown` and `cwebp`. It writes `projects/<slug>/index.html` —
**commit the generated HTML**, since nothing runs at deploy time.

The writeups mostly come from DevPost submissions, so `build.py` does the tidying
that needs: it inserts the blank lines DevPost omits (otherwise images and numbered
lists get glued onto the previous paragraph), strips the `<br>` padding, turns a
standalone image into a click-to-open figure, and renders a leading `_**Note:** …_`
as a callout. Paste a submission in as-is and it should come out right.

### Images

`build.py` downloads every remote image once, converts it to WebP, and rewrites the
markdown to point at `projects/<slug>/img/`. **Nothing is hot-linked** — a writeup
that depends on someone else's image host is a writeup with a time bomb in it.
Re-running is cheap: files already in `img/` are left alone.

## Design system

Inherits the Cortana design system: `#0d0d0d` background ladder, hairline structure,
tabular mono for every figure.

The accent is split two ways on purpose — **don't collapse it.** `--accent #5e6ad2`
for solid fills and borders; `--accent-hi #828df5` for accent-coloured *text*.
`#5e6ad2` on `#0d0d0d` is only 4.10:1, too dim for small type; `#828df5` is 6.49:1.
White on the `#5e6ad2` button is 4.70:1 and passes AA, which is why button text is
white and not near-black. Long-form body uses `--t-read #b4b4b4` (9.4:1) rather than
the UI grey, because `--t2` is tiring to read at length.

## Deploying

Deploys are manual — push-to-deploy is **not** wired up yet:

```
vercel deploy            # preview URL
vercel deploy --prod     # voxellabs.ai
```

To enable pushes to `main` deploying automatically, add this repo to the Vercel
GitHub App (`github.com/settings/installations` → Vercel → Configure), then run
`vercel git connect` once.

Preview locally with a server, not `file://` — pages reference `/style.css` by
absolute path:

```
python3 -m http.server 8794 --bind 127.0.0.1
```

## Domain

`voxellabs.ai` is on Cloudflare DNS. Both records must stay **grey-cloud (DNS only)** —
proxying them terminates TLS twice and breaks the site. Cloudflare shows a permanent
banner recommending you enable it. Don't.
