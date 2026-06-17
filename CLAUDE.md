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

## Multilingual system

The site supports three language variants switched at runtime via CSS class on `<body>`:

| Class | Language | Flag |
|---|---|---|
| `lang-pt` | European Portuguese | 🇵🇹 |
| `lang-br` | Brazilian Portuguese | 🇧🇷 |
| `lang-en` | English (Europe/international) | 🇬🇧 |

**Block-level content** uses `data-lang="pt"` / `"br"` / `"en"` on wrapper `<div>`s — only the active language's blocks are `display: block`.

**Inline content** uses `data-lang-inline="pt"` / `"en"` — toggled with `display: inline` / `display: none`. BR shares inline text with PT (both show `data-lang-inline="pt"`).

When editing copy: every user-facing string must exist in all three variants. Never add text to one language without adding the equivalents for the other two.

## Contact emails

| Context | Email |
|---|---|
| PT orders/contact | `encomendas@ssp3forte.com` |
| EN/BR orders/contact | `orders@ssp3forte.com` |
| Order form `mailto:` action | `prostatasaudavel@gmail.com` |

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
6. Testimonials
7. Pricing cards
8. Order form (sends via `mailto:`)
9. FAQ accordion
10. Footer

## Deployment

Push to `main` on GitHub → GitHub Pages rebuilds automatically in ~30 s. No CI, no build step. The `CNAME` file must remain at repo root.

## Key conventions

- All CSS lives inside a single `<style>` block in `<head>`.
- JS lives in a `<script>` block at the bottom of `<body>`.
- `font-size: 110%` on `html` and `font-size: 18px` on `body` set the baseline; don't shrink these.
- Order buttons open a pre-filled `mailto:` — there is no backend.
- Ingredient images use a click-to-zoom lightbox (`#lightbox`).
