# voxellabs.ai

The Voxel Labs site. One self-contained `index.html` — no build step, no dependencies
beyond the Google Fonts link. Open it directly in a browser to preview.

## Editing

All copy lives in two places:

- **Sections and headings** — inline in the HTML.
- **Case studies and the phase map** — the `WORK` and `PHASES` objects in the
  `<script>` block at the bottom. Edit the data, not the markup.

## Design system

Inherits the Cortana design system: `#0d0d0d` background ladder, hairline structure,
tabular mono for every figure, and a single accent — `#5e6ad2`, with `#828df5` for
accent-coloured text on the dark background (contrast).

## Deploying

Deploys are manual — push-to-deploy is **not** wired up yet:

```
vercel deploy --prod
```

To enable pushes to `main` deploying automatically, add this repo to the Vercel
GitHub App (`github.com/settings/installations` → Vercel → Configure), then run
`vercel git connect` once.

## Domain

`voxellabs.ai` is on Cloudflare DNS. Both records must stay **grey-cloud (DNS only)** —
proxying them terminates TLS twice and breaks the site. Cloudflare shows a permanent
banner recommending you enable it. Don't.
