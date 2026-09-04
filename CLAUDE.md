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
| `imgs/` | Ingredient photos (`01`–`08`), flags (`pt`, `br`, `eu`, `world`) |
| `imgs/zinc.png` | Zinc ingredient photo |
| `CNAME` | GitHub Pages custom domain (`ssp3forte.com`) |
| `worker/worker.js` | Cloudflare Worker — handles order form submissions, sends emails via Resend |
| `worker/wrangler.toml` | Wrangler config for deploying the Worker |
| `O que o SSP3-Forte pode fazer por Você.txt` | Source text for the info modal (PT/BR only) — written by the product author |

## Multilingual system

The site supports three language variants switched at runtime via CSS class on `<body>`:

| Class | Language | Flag | Button ID |
|---|---|---|---|
| `lang-pt` | European Portuguese | 🇵🇹 | `btn-pt` |
| `lang-br` | Brazilian Portuguese | 🇧🇷 | `btn-br` |
| `lang-en` | English (EU) | 🇬🇧 | `btn-eu` |

Default language on page load is **European Portuguese** (`lang-pt`).

**Block-level content** uses `data-lang="pt"` / `data-lang="br"` / `data-lang="en"` on wrapper `<div>`s — only the active language's blocks are `display: block`. PT and BR are **fully separate block variants** with genuine language differences (spelling, vocabulary, grammar — see below).

**Inline content** uses `data-lang-inline="pt"` / `"en"` — toggled with `display: inline` / `display: none`. BR shares inline text with PT (both show `data-lang-inline="pt"`); `body.lang-br [data-lang-inline="en"]` is hidden.

**PT vs BR language differences** applied throughout all content blocks:

| Feature | PT (European) | BR (Brazilian) |
|---|---|---|
| Spelling | extracto, afecta, eréctil, crónica, acção, contacto, optimizada | extrato, afeta, erétil, crônica, ação, contato, otimizada |
| Vocabulary | ácidos gordos, casa de banho, utilizadores, efeitos secundários, pretendida | ácidos graxos, banheiro, usuários, efeitos colaterais, desejada |
| Grammar | "a sua opção", "entraremos em contacto" | "sua opção", "entre em contato" |
| Tone | formal | direct, uses "você" |

When editing copy: every user-facing string must exist in all three variants (pt, br, en). Never add text to one language without adding the equivalents for the other two.

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

## Navigation

**Language bar** — sticky top bar with PT 🇵🇹, BR 🇧🇷, EU 🇬🇧 flag buttons. Clicking BR also activates BRL pricing (equivalent to checking the BRL checkbox).

**Top nav menu** (`#top-nav`) — fixed top-left hamburger button (☰) that expands **downwards into a compact vertical list**: Início/Home, Testemunhos/Testimonials, Encomenda/Order, Perguntas frequentes/FAQ, Artigos. Collapsed it is 38×34px; open it is 178px wide and grows to fit (`max-height: 280px`), animating `width` and `max-height`. Links are 13px. Closes on link click or outside click. The Artigos entry carries `li.nav-pt-only` and is hidden for EN/INT, matching the PT/BR-only `#artigos` section. Not hidden on mobile.

## Sections (in order)

1. Sticky language switcher bar (3 flags: PT, BR, EU)
2. `#top-nav` — sticky top-left hamburger nav menu
3. `#hero` — Hero: 3 CTA buttons (order → `#precos`, ingredients, Blog)
4. Social-proof bar
5. Symptoms grid
6. `#ingredientes` — Ingredients list (with lightbox) + sticky callout
7. `#testemunhos` — Testimonials
8. Video — "Ver em acção / Ver em ação / Watch in action"
9. `#precos` — Pricing cards (EUR and BRL toggle) — PT/BR have "O que este produto pode fazer" button
10. `#encomenda` / `#order` — Order form (submits via Cloudflare Worker → Resend email)
11. `#faq` — FAQ accordion — includes blog CTA (PT/BR only)
12. `#artigos` — Blog articles grid, 6 of 16 drawn weekly (PT/BR only — see below)
13. References section (scientific bibliography)
14. Footer

**Blog articles section** (`#artigos`) — a grid of 6 articles from the Naturalfarma blog, rendered by JS from a hand-curated pool of 16 (`BLOG_POSTS`, at the bottom of the script block). The two grids are empty containers `#blog-grid-pt` / `#blog-grid-br`, both filled on load by `renderBlogCards()`; CSS shows only the active language’s. Hidden for EN/INT via `body.lang-en .blog-section, body.lang-world .blog-section { display: none; }` because the blog is Portuguese-only.

**Weekly rotation** — `blogWeekSeed()` returns whole Monday-based weeks since the Unix epoch and seeds a mulberry32 PRNG, so the draw is deterministic: every visitor sees the same six articles all week and the set changes each Monday, with no server and no storage. `blogWeeklyPick()` draws `BLOG_WITH_IMG` (4) from the entries that have a photo and fills the remaining 2 from those without, so the grid is never mostly placeholders — the pool is split 8/8. Both section leads say the selection changes weekly ("A selecção muda todas as semanas" / "A seleção muda toda semana").

**Why curated and not a live feed:** the blog's 2026 output (122 posts) is AI-generated SEO content — slug titles (`Toque-retal-exame-prostata`), a rigid "symptom list → target keyword restated → answer" template, batches of 10 posts published within 28 minutes, and several posts whose title field is empty with the title left as the body's first line. Pulling the feed live would surface that content. The 16 pooled articles are all pre-2024 and genuinely authored, chosen for educational value and for making no therapeutic claims about the product — several otherwise good posts were rejected only because they close with a product pitch (`O Gengibre e a saúde da Próstata`, `PRÓSTATA X CHURRASCO`, `Termos sobre a Próstata`, `Função da próstata`, `Próstata está no tamanho certo?`, all ending on "normalizando o PSA, o tamanho da próstata"). Deliberately excluded: `SSP3-Forte tem Antivirais` (immunity-against-viruses claim), `SSP3_Forte, perguntas e respostas` ("prevenir e/ou tratar a hiperplasia"), and `Onde adquirir o SSP3-Forte em Portugal` / `SSP3 Testemunhos (PARTE 2)` (contain third-party names, addresses, phone numbers and an email address).

To add an article to the pool: append one entry to `BLOG_POSTS` — `u` (url), `i` (image url, or `''` for the `.blog-card-ph` inline-SVG placeholder), `d` (date label), `tp`/`tb` (title PT/BR) and `ep`/`eb` (excerpt PT/BR). PT and BR strings must both be filled even when identical. Blogger thumbnails come from the feed (`/feeds/posts/default?alt=json`) at `/s72-c/`; swap that for `/s400/` (or `=s72-c` → `=s400`) for a usable size.

**Info modal** (`#info-modal`) — floating overlay, PT/BR only. Triggered from hero "Saber mais" dropdown and pricing section button. Source text: `O que o SSP3-Forte pode fazer por Você.txt`.

**Survey modal** (`#survey-modal`) — floating overlay in all four languages (pt/br/en blocks; `lang-world` shows the `en` one), opened by `openSurveyModal()` from the second entry of the "Saber mais" / "Learn more" dropdown. It reports the 2017 satisfaction survey **for one subgroup only**: the 67 respondents who declared regular use *and* declared no medication — 88.1% satisfied or very satisfied [95% CI 80.3–95.8], 32.8% very satisfied, one respondent not satisfied.

The modal is built so the headline number cannot be read out of context: the comparison table shows the full sample (289, 81.3%) and the regular-use-only cut (185, 81.1%) alongside it, the text states that the 8.8-point gap is not significant (p=0.106) with overlapping CIs, and a closing `.sv-disclaimer` block spells out that 223 of 290 questionnaires (77%) were excluded, that "no medication" is really a blank field, that the subgroup was chosen post hoc, that survivorship bias inflates it, that no improvement can be measured without a control group or a baseline, and that nothing in it supports a health claim under Regulation (EC) 1924/2006. **Do not quote "88%" anywhere on the site without both filters and the n=67** — the figure for all respondents is 81.3%.

Numbers come from `satisfaction_dataset/Inqueritos (290), Mapa em 02102017.xls`, sheet "Dados Actualizados"; the full working analysis lives in the scratchpad generators (`gen_semmeds.py` and siblings), not in the repo.

**"Saber mais" dropdown order** (`.hero-dropdown-menu`): product info modal → survey modal → Blog → free Ebook. The EN/INT block carries only the two modals.

**Hero CTA buttons** — font size 21px (scoped to `.hero-cta`). The order button links to `#precos` (pricing section), not `#encomenda`. The Blog button uses `.btn-blog` class (gold border, bold) to stand out.

## Testimonials

4 real testimonials sourced verbatim from the Naturalfarma blog: http://problemasnaprostata.blogspot.com/2013/10/faq-perguntas-e-comentarios-frequentes.html

| Author | Location | Key result |
|---|---|---|
| A. Arruda | SC, Brasil | 7–8h sleep, no nocturia, sexual function restored |
| Roberto A. | SP, Brasil | PSA dropped from 3,080 to 1.61 in 2 months |
| L. Santos | SP, Brasil | Prostate reduced to 30g, 1 bathroom visit/night |
| Herculano | Lisboa, Portugal | PSA stable at 1.4 at age 68 |

**Rules:** quotes must remain verbatim (original Brazilian Portuguese) in both PT and BR blocks. EN block is a faithful translation. Never paraphrase or adapt these quotes — they are real customer statements.

## Pricing

### EUR prices
| Product | Price |
|---|---|
| 1 frasco / bottle | €29.95 |
| Kit 3 frascos / 3-bottle kit | €80.86 (saves 10% off €89.85) |

### BRL prices (R$) — shown when BR flag or BRL toggle is active
| Product | Price |
|---|---|
| 1 frasco | R$210 |
| Kit 3 frascos | R$567 (saves 10% off R$630) |

JS `PRICES` object: `{ '1x': 29.95, '3x': 80.86, '1x-br': 210, '3x-br': 567 }`

Shipping (EUR orders): Portugal €4.99, other countries €9.00.

## Order form behaviour

- **Default country:** "Portugal" for PT/BR, empty for EN/EU
- **BR flag / BRL checkbox:** activates `brl-pricing` body class, sets country to "Brasil", switches pricing display to BRL. Both the flag button and checkbox are kept in sync.
- **Submit:** async fetch to Worker; shows success message on screen on success, alert with support email on failure

## Deployment

Push to `main` on GitHub → GitHub Pages rebuilds automatically in ~30 s. No CI, no build step. The `CNAME` file must remain at repo root.

Worker changes require a separate `npx wrangler deploy` from the `worker/` directory.

## Ingredients

8 ingredients, each with a photo (`imgs/0N_*.jpg/png`), botanical name in italics, description, and superscript citation(s). PT, BR, and EN versions must all be kept in sync. Citation numbering follows the bibliography order below.

| # | Name (PT/BR) | Name (EN) | Image | Citations |
|---|---|---|---|---|
| 01 | Saw Palmetto *(Serenoa repens)* | Saw Palmetto *(Serenoa repens)* | `01_sawpalmetto.jpg` | [1,2] |
| 02 | Pygeum africanum | Pygeum africanum | `02_pygeum_africanum.jfif` | [3,4] |
| 03 | Beta-Sitosterol | Beta-Sitosterol | `03_beta_sitosterol.png` | [5-7] |
| 04 | Zinco | Zinc | `04_zinc.png` | [8,9] |
| 05 | Urtica dioica *(Urtiga)* | Urtica dioica *(Nettle)* | `05_urtica_dioica.png` | [10-12] |
| 06 | Semente de Abóbora *(Cucurbita pepo)* | Pumpkin Seed *(Cucurbita pepo)* | `06_semente_abobora.png` | [13,14] |
| 07 | Licopeno | Lycopene | `07_licopeno.png` | [15] |
| 08 | Vitamina E | Vitamin E | `08_vitamina_e.png` | [16] |

Bibliography has 16 references in PT, BR, and EN. Zinc refs: [8] Costello & Franklin DOI `10.3390/biomedicines10123206`; [9] Chen et al. 2025 DOI `10.1016/j.jtemb.2025.127605`.

## Key conventions

- All CSS lives inside a single `<style>` block in `<head>`.
- JS lives in a `<script>` block at the bottom of `<body>`.
- `font-size: 110%` on `html` and `font-size: 18px` on `body` set the baseline; don't shrink these.
- Ingredient images use a click-to-zoom lightbox (`#lightbox`).
- The `currentRegion` JS variable tracks `'pt'`, `'br'`, or `'eu'` — maps to body classes `lang-pt`, `lang-br`, `lang-en`.
- `setLang(region)` sets `body.className` to `lang-pt`, `lang-br`, or `lang-en` and syncs all UI state (BRL toggle, country input, active flag buttons, order link href).
- The `#encomenda` section ID becomes `#order` when EN is active (swapped by `setLang`); the top-nav order link href is updated in sync.
- PT/BR-only features (info modal, "Saber mais" dropdown, blog CTA in FAQ) use `[data-lang="pt"]` / `[data-lang="br"]` blocks — invisible to EN visitors automatically.
- `.btn-blog` — special class on Blog buttons for visual emphasis (gold border, bold, hover fills gold).
- `.hero-cta .btn-primary` and `.hero-cta .btn-ghost` — font-size scoped to 21px; other buttons on the page remain at their own sizes.
