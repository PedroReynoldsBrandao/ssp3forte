# SSP3-Forte Website — CLAUDE.md

## Project overview

Single-page marketing website for **SSP3-Forte**, a natural prostate-health supplement distributed by Naturalfarma. Hosted at [ssp3forte.com](https://ssp3forte.com) via GitHub Pages (repo: `PedroReynoldsBrandao/ssp3forte`).

**Stack:** Pure HTML + CSS + vanilla JS in a single file (`index.html`). No build tools, no framework, no npm. What you edit is what ships.

## File map

| File | Purpose |
|---|---|
| `index.html` | The entire website — HTML, CSS, and JS all in one file |
| `index-v1.html` / `index-v2.html` | Earlier versions kept for reference |
| `frasco.jpg` | Product photo used as favicon and hero image |
| `imgs/` | Ingredient photos (numbered `01`–`08`), flags (`pt`, `gb`, `br`) |
| `CNAME` | GitHub Pages custom domain (`ssp3forte.com`) |
| `worker/worker.js` | Cloudflare Worker — handles order form submissions, sends emails via Resend |
| `worker/wrangler.toml` | Wrangler config for deploying the Worker |

## Multilingual system

The site supports three language variants switched at runtime via CSS class on `<body>`:

| Class | Language | Flag |
|---|---|---|
| `lang-pt` | European Portuguese | 🇵🇹 |
| `lang-br` | Brazilian Portuguese | 🇧🇷 |
| `lang-en` | English (Europe/international) | 🇬🇧 |

Default language on page load is **Brazilian Portuguese** (`lang-br`).

**Block-level content** uses `data-lang="pt"` / `"br"` / `"en"` on wrapper `<div>`s — only the active language's blocks are `display: block`.

**Inline content** uses `data-lang-inline="pt"` / `"en"` — toggled with `display: inline` / `display: none`. BR shares inline text with PT (both show `data-lang-inline="pt"`).

When editing copy: every user-facing string must exist in all three variants. Never add text to one language without adding the equivalents for the other two.

## Contact emails

| Context | Email |
|---|---|
| PT/BR orders/contact | `encomendas@ssp3forte.com` |
| EN orders/contact | `orders@ssp3forte.com` |

Both addresses route to `leptix@gmail.com` via email forwarding.

## Order system (Cloudflare Worker)

The order form POSTs JSON to the Cloudflare Worker at `https://ssp3forte-orders.leptix.workers.dev`.

The Worker:
1. Validates the payload and identifies the product
2. Generates a sequential order number via [counterapi.dev](https://counterapi.dev) — format `YYYYMMDD01`, `02`… resets daily
3. Sends a **confirmation email to the client** (branded, in their language)
4. Sends an **internal notification** to `encomendas@ssp3forte.com` or `orders@ssp3forte.com` with a plain data table

**Required Worker secret** (set via `wrangler secret put RESEND_API_KEY`):
- `RESEND_API_KEY` — from [resend.com](https://resend.com) dashboard

**To redeploy the Worker:**
```
cd worker
npx wrangler deploy
```

**Country code logic** in order numbers:
- `Brasil` / `Brazil` → `BR`
- `Portugal` → `PT`
- `Angola` → `AO`
- EN lang, other → `EU`

**Email routing:**
- PT/BR orders → from/to `encomendas@ssp3forte.com`
- EN orders → from/to `orders@ssp3forte.com`

## Design tokens (CSS variables)

```css
--green-deep:  #0d3d2b   /* dark backgrounds, headings */
--green-mid:   #1a6645   /* buttons, accents */
--green-light: #2a9460   /* hover states */
--green-pale:  #e8f4ee   /* section backgrounds */
--gold:        #c9a84c   /* primary accent, CTAs */
--gold-light:  #f0e0a8   /* hover on gold */
--cream:       #faf8f3   /* page background */
```

Fonts loaded from Google Fonts: **Lora** (headings, serif) + **Source Sans 3** (body, UI).

## Sections (in order)

1. Sticky language switcher bar
2. Hero (2-col grid: copy + product image)
3. Social-proof bar
4. Symptoms grid
5. Ingredients list (with lightbox) + sticky callout
6. Testimonials (`#testemunhos`)
7. Video (`#video`) — "Ver em acção / Watch in action"
8. Pricing cards (`#precos`, EUR and BRL toggle)
9. Order form (`#encomenda`, submits via Cloudflare Worker → Resend email)
10. Blog redirect CTA
11. FAQ accordion (`#faq`)
12. Footer

## Testimonials

4 real testimonials sourced verbatim from the Naturalfarma blog: http://problemasnaprostata.blogspot.com/2013/10/faq-perguntas-e-comentarios-frequentes.html

| Author | Location | Key result |
|---|---|---|
| A. Arruda | SC, Brasil | 7–8h sleep, no nocturia, sexual function restored |
| Roberto A. | SP, Brasil | PSA dropped from 3,080 to 1.61 in 2 months |
| L. Santos | SP, Brasil | Prostate reduced to 30g, 1 bathroom visit/night |
| Herculano | Lisboa, Portugal | PSA stable at 1.4 at age 68 |

**Rules:** quotes must remain verbatim (original Brazilian Portuguese) in both PT and BR blocks. EN block is a faithful translation. Never paraphrase or adapt these quotes — they are real customer statements.

## Order form behaviour

- **Default country:** "Portugal" for PT/BR, empty for EN/EU
- **BRL checkbox:** checking it sets country to "Brasil" and switches pricing to BRL; unchecking restores "Portugal"
- **Shipping calc:** Portugal €4.99, other PT/BR countries €9.00, EN/EU and BR → "to confirm"
- **Submit:** async fetch to Worker; shows success message on screen on success, alert with support email on failure

## Deployment

Push to `main` on GitHub → GitHub Pages rebuilds automatically in ~30 s. No CI, no build step. The `CNAME` file must remain at repo root.

Worker changes require a separate `npx wrangler deploy` from the `worker/` directory.

## Ingredients

8 ingredients, each with a photo (`imgs/0N_*.jpg/png`), botanical name in italics, description, and superscript citation(s). Both PT/BR and EN versions must be kept in sync. Citation numbering follows the bibliography order below.

| # | Name (PT) | Name (EN) | Image | Citations |
|---|---|---|---|---|
| 01 | Saw Palmetto *(Serenoa repens)* | Saw Palmetto *(Serenoa repens)* | `01_sawpalmetto.jpg` | [1,2] |
| 02 | Pygeum africanum | Pygeum africanum | `02_pygeum_africanum.jfif` | [3,4] |
| 03 | Beta-Sitosterol | Beta-Sitosterol | `03_beta_sitosterol.png` | [5-7] |
| 04 | Zinco | Zinc | `04_zinc.png` | [8,9] |
| 05 | Urtica dioica *(Urtiga)* | Urtica dioica *(Nettle)* | `05_urtica_dioica.png` | [10-12] |
| 06 | Semente de Abóbora *(Cucurbita pepo)* | Pumpkin Seed *(Cucurbita pepo)* | `06_semente_abobora.png` | [13,14] |
| 07 | Licopeno | Lycopene | `07_licopeno.png` | [15] |
| 08 | Vitamina E | Vitamin E | `08_vitamina_e.png` | [16] |

Bibliography has 16 references in both PT and EN. Zinc refs: [8] Costello & Franklin DOI `10.3390/biomedicines10123206`; [9] Chen et al. 2025 DOI `10.1016/j.jtemb.2025.127605`.

## Key conventions

- All CSS lives inside a single `<style>` block in `<head>`.
- JS lives in a `<script>` block at the bottom of `<body>`.
- `font-size: 110%` on `html` and `font-size: 18px` on `body` set the baseline; don't shrink these.
- Ingredient images use a click-to-zoom lightbox (`#lightbox`).
- The `currentRegion` JS variable tracks `'pt'`, `'br'`, or `'eu'` — distinct from the `lang-*` body class.
