# SSP3-Forte Website — CLAUDE.md

## Project overview

Single-page marketing website for **SSP3-Forte**, a natural prostate-health supplement distributed by Naturalfarma. Hosted at [ssp3forte.com](https://ssp3forte.com) via GitHub Pages (repo: `PedroReynoldsBrandao/ssp3forte`).

**Stack:** Pure HTML + CSS + vanilla JS in a single file (`index.html`). No build tools, no framework, no npm. What you edit is what ships.

## Working on another machine

Everything the site needs is in the repo. Three things are **not**, and they are the ones that catch you out.

```bash
git clone https://github.com/PedroReynoldsBrandao/ssp3forte.git
cd ssp3forte
```

**Prerequisites:** git, Python 3 (the two modal generators, no third-party packages), Node (only for `node --check` and `npx wrangler`), curl. Nothing to install, no `npm install`, no build step.

**What is not in the repo, and why**

| Missing | Where it lives | Consequence |
|---|---|---|
| `satisfaction_dataset/` | Pedro's OneDrive only — gitignored | The survey figures cannot be re-derived without it. The numbers that matter are written down under *Survey figures* below, so the site is maintainable without the file. Copy it across manually if you need to re-run the analysis. **Do not commit it: the repo is public and the file holds customer records.** |
| Wrangler credentials | `worker/.wrangler/` on the machine you last deployed from — gitignored | On a new machine the first `npx wrangler deploy` opens a browser to log in to Cloudflare. Expected, not an error. |
| `RESEND_API_KEY` | A Cloudflare secret, server-side | Never on any machine. It survives redeploys; you do not need to re-enter it. |

**Deploying**

- **Site:** push to `main`. GitHub Pages rebuilds in roughly 30–90 seconds. Confirm with `curl -s https://ssp3forte.com/ | grep <something you changed>` rather than trusting the push.
- **Worker:** `cd worker && npx wrangler deploy`. On Windows PowerShell the execution policy blocks the `npx.ps1` shim — use `npx.cmd wrangler deploy`. **The live config is `worker/wrangler.toml`** (that is the directory you deploy from); the `wrangler.jsonc` at the repo root is a leftover duplicate and is not what ships.

**Editing the two modals**

Do not hand-edit the three language blocks in `index.html`. Edit the generator, then splice:

```bash
python tools/apply_modal.py both     # or: info | survey
```

It runs the generator, replaces the block between the right markers, checks the tags balance and deletes the temporary file. It is idempotent — running it with no changes reproduces the file byte for byte, which makes it safe to run just to check.

**Checking prices before publishing**

```bash
python tools/check_prices.py
```

The price is written in places that do not know about each other: the `PRICES`
object, the pricing cards in each language block, the form's `<option>` labels
and the `OPT` map (all in `index.html`), the `PRODUCTS` table in
`worker/worker.js`, and the tables in this file. The Worker deliberately prices
from its own table rather than from the submitted payload — otherwise anyone
could forge an order at an invented price — so the two can drift with nothing to
catch it. **They did: from 20 Jul to 12 Sep 2026 the site charged R$210 while
every Brazilian confirmation email said R$165**, because the price rise touched
`index.html` and `CLAUDE.md` and not the Worker.

The script treats `PRICES` as the source of truth, reports every disagreement
with a line number, and exits non-zero. Run it whenever you touch prices,
shipping or the contact emails. A `worker.js` mismatch is only really fixed once
you `cd worker && npx wrangler deploy` — a git push does not touch the Worker.

**Checking your work before committing**

```bash
python -c "import io,re; s=io.open('index.html',encoding='utf-8').read(); io.open('_p.js','w',encoding='utf-8').write(re.findall(r'<script>(.*?)</script>',s,re.S)[0])" && node --check _p.js && rm _p.js
```

All the CSS and JS is inside `index.html`, so a stray quote takes the whole page down with no build step to catch it. To read a language variant as a visitor sees it, write `index.html` out with `<body class="lang-pt|lang-br|lang-en|lang-world">` and open that file — the switching is pure CSS, so a static copy renders correctly (the JS-rendered blog grid will be empty).

## Survey figures (so the site is maintainable without the dataset)

From `Inqueritos (290), Mapa em 02102017.xls`, sheet "Dados Actualizados". Satisfied = "satisfeito" + "muito satisfeito".

| Group | n | Satisfied | 95% CI |
|---|---|---|---|
| All respondents | 289 | **81.3%** | 76.8–85.8 |
| Regular use only | 185 | 81.1% | 75.4–86.7 |
| No medication only | 108 | 85.2% | 78.5–91.9 |
| **Regular use + no medication** | **67** | **88.1%** | 80.3–95.8 |

Within the n=67 group: very satisfied 22 (32.8%), satisfied 37 (55.2%), slightly satisfied 7 (10.4%), not satisfied 1 (1.5%). By length of use: 3 months 81.8% (n=11), 6 months 80.0% (n=15), over a year 92.1% (n=38); the 1-month band held three answers and is omitted. The n=67 group differs from the rest at p=0.106 — not significant. "No medication" means the questionnaire field was left blank, which may mean "none" or "did not answer". No control group, no baseline, so no improvement can be measured from it.

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
| `O que o SSP3-Forte pode fazer por Você.txt` | Superseded source text for the info modal — written by the product author |
| `tools/gen_survey.py`, `tools/gen_info_modal.py` | Generators for the two modals’ three-language markup |
| `tools/apply_modal.py` | Runs a generator and splices the result into `index.html` |
| `tools/check_prices.py` | Checks the price in index.html, worker.js and this file still agree |
| `registo_SSP3forte_ideias.txt` | Notes on trademark registration for the SSP3-Forte name (not website content) |
| `.gitignore` | Keeps customer data and Cloudflare credentials out of a public repo |
| `wrangler.jsonc` (root) | Leftover duplicate — the live Worker config is `worker/wrangler.toml` |

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

## Blog links per language

PT/BR point at problemasnaprostata.blogspot.com; EN/INT point at bph-prostate-enlarged.blogspot.com. That covers three places: the hero "Saber mais" / "Learn more" dropdown, the FAQ call-to-action, and the footer (the footer link is split with `data-lang-inline`). Check all three whenever either blog URL changes.

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

**Language bar** — sticky top bar with PT 🇵🇹, BR 🇧🇷, EU 🇬🇧 flag buttons. Clicking BR also activates BRL pricing (equivalent to checking the BRL checkbox). It also carries an **Aviso Legal / Legal Notice** button that opens `#disclaimer-modal`.

**Top nav menu** (`#top-nav`) — fixed top-left hamburger button (☰) that expands **downwards into a compact vertical list**: Início/Home, Testemunhos/Testimonials, Encomenda/Order, Perguntas frequentes/FAQ, Artigos. Collapsed it is 38×34px — a gold button with green bars; open it is 178px wide on a `--green-deep` panel and grows to fit (`max-height: 280px`), animating `width` and `max-height`. Links are 13px. It sits at `top: 48px`, and at `top: 66px` below 600px, because the language bar wraps to two rows on phones and the button was covering the PT flag. Closes on link click or outside click. The Artigos/Articles entry is shown in every language, since `#artigos` now has an EN block too. Not hidden on mobile.

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
11. `#faq` — FAQ accordion — includes a blog CTA in every language, pointing at that language’s blog
12. `#artigos` — Blog articles grid, shown in all four languages: 6 of 16 drawn weekly for PT/BR, 6 of 7 for EN/INT (see below)
13. References section (scientific bibliography)
14. Footer

**Blog articles section** (`#artigos`) — a grid of articles rendered by JS, shown in **all four languages**. PT and BR draw from `BLOG_POSTS` (the Portuguese blog, problemasnaprostata.blogspot.com, pool of 16); EN and INT draw from `BLOG_POSTS_EN` (the English blog, **bph-prostate-enlarged.blogspot.com**, pool of 7). The three grids are empty containers `#blog-grid-pt` / `#blog-grid-br` / `#blog-grid-en`, all filled on load by `renderBlogCards()`; CSS shows only the active language’s. EN entries carry `tp`/`ep` only (no PT/BR split). **The pool contains only the seven articles written in September 2026** — none of the 24 legacy posts is featured any more. Six of the seven carry a photograph; the Vitamin D one takes the `sun` drawn cover. The card CTA is "Read article" for EN, "Ler artigo" otherwise.

**Weekly rotation** — `blogWeekSeed()` returns whole Monday-based weeks since the Unix epoch and seeds a mulberry32 PRNG, so the draw is deterministic: every visitor sees the same six articles all week and the set changes each Monday, with no server and no storage. `blogWeeklyPick()` draws `BLOG_WITH_IMG` (4) from the entries that have a photo and fills the remaining 2 from those without, so the grid is never mostly placeholders — the pool is split 8/8. Both section leads say the selection changes weekly ("A selecção muda todas as semanas" / "A seleção muda toda semana").

**The seven English articles (8–9 Sep 2026)** — *What actually happens when the prostate grows*, *PSA total and free PSA*, *Belly fat and prostate health*, *Coffee, caffeine and the prostate*, *Smoking, circulation and prostate health*, *Colour on the plate*, *Vitamin D and the prostate*. They were written for this site and published to the blog, and they **replaced the legacy posts in the site pool entirely**. The reason: none of the 24 legacy English posts passes the curation criterion — every one closes on a product pitch, and several carry claims far stronger than anything on the site ("The best Doctors in EUROPE prescribe this natural miracle to 80% of their prostate patients", "90% improvement in symptoms in 8-12 weeks", "SSP3-Forte can heals Naturally, there absolutely NO side effects"). The seven name no product, make no health claim, and close by pointing the reader at their doctor. **Keep that standard for anything added to the English blog or the EN pool.** Their photographs are Naturalfarma's own, reused from the Portuguese blog.

**English blog admin:** `pedrorbrandao@gmail.com` was promoted to administrator on 9 Sep 2026. The theme was changed from **Simple Pale** (a 2011-era template: narrow column, clipped title, tiny type) to **Contempo Light** — responsive, image-led, readable. No backup of the old theme was taken; Simple Pale is a stock theme and can be reselected from the gallery if ever needed. The 24 legacy posts are still authored by "Nutrition for Good" and are left untouched.

One thing deliberately *not* fixed: `What you must know about prostate problems` contains two `file:///C:/Users/Pedro/...` image references left by a Word paste. They are `height="1"` spacers inside VML conditional comments — invisible in practice, not the broken pictures they first appear to be. Editing a 221 KB Word-pasted body to remove two one-pixel images is not worth the risk of mangling the post.

**Why curated and not a live feed:** the blog's 2026 output (122 posts) is AI-generated SEO content — slug titles (`Toque-retal-exame-prostata`), a rigid "symptom list → target keyword restated → answer" template, batches of 10 posts published within 28 minutes, and several posts whose title field is empty with the title left as the body's first line. Pulling the feed live would surface that content. The 16 pooled articles are all pre-2024 and genuinely authored, chosen for educational value and for making no therapeutic claims about the product — several otherwise good posts were rejected only because they close with a product pitch (`O Gengibre e a saúde da Próstata`, `PRÓSTATA X CHURRASCO`, `Termos sobre a Próstata`, `Função da próstata`, `Próstata está no tamanho certo?`, all ending on "normalizando o PSA, o tamanho da próstata"). Deliberately excluded: `SSP3-Forte tem Antivirais` (immunity-against-viruses claim), `SSP3_Forte, perguntas e respostas` ("prevenir e/ou tratar a hiperplasia"), and `Onde adquirir o SSP3-Forte em Portugal` / `SSP3 Testemunhos (PARTE 2)` (contain third-party names, addresses, phone numbers and an email address).

To add an article to the pool: append one entry to `BLOG_POSTS` — `u` (url), `i` (image url, or `''` for the `.blog-card-ph` inline-SVG placeholder), `d` (date label), `tp`/`tb` (title PT/BR) and `ep`/`eb` (excerpt PT/BR). PT and BR strings must both be filled even when identical. Blogger thumbnails come from the feed (`/feeds/posts/default?alt=json`) at `/s72-c/`; swap that for `/s400/` (or `=s72-c` → `=s400`) for a usable size.

**Card covers** — an entry with `i: ''` renders `.blog-card-cover` instead of a photo: a green gradient ground with a diagonal texture and a gold line icon, chosen by the entry's `k` key from `BLOG_COVERS` (doc, guide, flame, moon, dna, bike, sun, leaf, drop, heart, fish, cup, check, clock; unknown keys fall back to `doc`). `blogCoverGround()` hashes the URL into one of four gradient variants so neighbouring covers differ and a given post always looks the same. This replaced the single grey `.blog-card-ph` placeholder, which made the EN grid look broken because none of its posts has a photo.

**Info modal** (`#info-modal`) — floating overlay in all three languages (pt/br/en), opened from the hero "Saber mais" dropdown and the pricing-section button. Markup is generated by `tools/gen_info_modal.py`; edit that script and re-paste rather than hand-editing three blocks.

**Rewritten Sep 2026 at the client’s request.** The previous copy presented the product as a "remédio"/"tratamento" for a named disease and claimed effects on PSA, prostate size, urinary flow, nocturia, erection and spermatogenesis — none of which is on the authorised list under Regulation (EC) 1924/2006, and the medicinal framing exposed the product to being treated as a medicine by presentation. It also carried a structured comparison against prescription medicines listing their adverse effects, and the phrase "garante total segurança".

The current copy sells on what is verifiable: EU manufacture under GMP, ISO 22000 certification with batch control, the eight named ingredients (listed, never with claimed effects — botanical claims are still "on hold" in the EU), the satisfaction survey, how to take it, and lifestyle advice. **Do not reintroduce claims about PSA, prostate size, urinary symptoms, erection or fertility here.**

*Available upgrade:* zinc and vitamin E carry genuinely authorised claims ("o zinco contribui para a manutenção de níveis normais de testosterona no sangue", "para a fertilidade e reprodução normais", "o zinco e a vitamina E contribuem para a protecção das células contra as oxidações indesejadas"). They are **not** in the copy because they require the daily dose to supply ≥15% of the NRV (1.5 mg zinc, 1.8 mg vitamin E) and the label quantities are not documented anywhere in this repo. Confirm them against the label and these three lines can be added — they are the strongest legitimate claims available to this product.

The modal quotes **"perto de 9 em cada 10" / "close to 9 in 10"** of *users*, unqualified. That figure is the n=67 subgroup (regular use + no medication declared, 88.1%). The number for "users" without qualification is **81.3%** across all 290 respondents, and 81.1% for regular use alone. The unqualified wording was the client’s express decision in Sep 2026, taken after the discrepancy was put to him in writing three times; he stated the responsibility was his. Do not silently "fix" it — and do not extend it to new places without asking him. The full framing remains one click away in `#survey-modal`, which this modal links to. Older source text: `O que o SSP3-Forte pode fazer por Você.txt`.

**Survey modal** (`#survey-modal`) — floating overlay in all four languages (pt/br/en blocks; `lang-world` shows the `en` one), opened by `openSurveyModal()` from the second entry of the "Saber mais" / "Learn more" dropdown. Title: **"Estudo de satisfação a utilizadores"** (no year in the title — 2017 appears only in the small print). It reports the 2017 survey for the group of 67 respondents who declared regular use *and* declared no medication.

It is a **sales page, not a report**: donut at 88%, a 9-in-10 pictogram, the responses table (22 / 37 / 7 / 1 with bars), satisfaction by length of use, and a closing highlight on the 92% among users of more than a year. Constraints agreed with the client, do not undo them:

- The base of 290 questionnaires appears **only** in the small print at the very bottom, never in the body.
- The word "apenas" must not appear anywhere in the modal.
- **No comparison with the full sample in the body** — that analysis is internal.
- Confidence intervals and p-values are allowed, but only in the small `.sv-cap` / `.sv-fine` type.

The caption under the length-of-use table is a **selling line, not a caveat** ("Mais de metade deste grupo já tomava o SSP3-Forte há mais de um ano — e é nesse grupo que a satisfação é mais alta" — 38 of 67); the omitted 1-month band and the width of the intervals moved to the small print, at the client’s request. The `.sv-fine` block at the end carries everything else in 0.68rem grey: the 290 base, the 223 excluded questionnaires, the 81.3% across all respondents, the blank-field caveat behind "no medication", post-hoc selection with p=0.106, survivorship bias, the absence of a control group or baseline, and Regulation (EC) 1924/2006. **Anywhere "88%" or "9 in 10" appears outside `#survey-modal`, the two filters must appear in the same sentence.** The figure for all respondents is 81.3%; for regular use alone, 81.1%.

The markup is generated by `tools/gen_survey.py` (donut, pictogram and tables are computed there); edit that script and re-paste rather than hand-editing three language blocks. Numbers come from `satisfaction_dataset/Inqueritos (290), Mapa em 02102017.xls`, sheet "Dados Actualizados" — **not in the repo** (see *Working on another machine*); the figures are tabulated under *Survey figures*.

**Disclaimer modal** (`#disclaimer-modal`) — "Aviso Legal e Declaração de Responsabilidade" / "Legal Notice and Disclaimer", opened by `openDisclaimerModal()` from the language bar. Three hand-written blocks (pt/br/en) — **not generated**, unlike the other two modals, so the PT/BR spelling table above has to be applied by hand when editing it. It carries the supplement-law boilerplate (not a substitute for a varied diet, do not exceed the dose, keep away from children, not for under-18s or pregnant women, consult a doctor if medicated), the statement that the site's content is educational and does not diagnose or treat, that results vary, that any reference to urinary wellbeing or prostate comfort is to be read within the authorised-claims framework and is not a promise of results, and that testimonials are individual experiences. This is the page's legal backstop for the claims still outstanding under *Global review* — do not weaken it.

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

Shipping (EUR orders): Portugal €5.99, other countries €9.00. JS `SHIPPING` object: `{ PT: 5.99, default: 9.00 }`.

## Order form behaviour

- **Default country:** "Portugal" for PT/BR, empty for EN/EU
- **BR flag / BRL checkbox:** activates `brl-pricing` body class, sets country to "Brasil", switches pricing display to BRL. Both the flag button and checkbox are kept in sync.
- **Submit:** async fetch to Worker; shows success message on screen on success, alert with support email on failure

## Deployment

Push to `main` → GitHub Pages rebuilds automatically. No CI, no build step. The `CNAME` file must remain at repo root. Worker changes need a separate deploy from `worker/`. Commands, the PowerShell gotcha and which wrangler config is live are all under *Working on another machine*.

## Global review, Sep 2026

A pass over all four language variants turned up defects that had been live for some time:

- **The English bibliography was broken.** It had 15 references against 16 in PT/BR: the Chen et al. 2025 zinc reference was missing, and `[8]` read "DOI to verify before publication" — an editorial placeholder that had shipped. Because one entry was missing, **every citation from `[9]` onwards in the English ingredient list pointed at the wrong paper.** Fixed; all three lists are now 16 and aligned.
- The "6ª" in the results callout was a shared element, so English read "6ª week". Now switched per language.
- The footer said © 2024.
- The product `<select>` carried both languages in one label ("1 frasco / 1 bottle — €29,95"). CSS cannot hide an `<option>` reliably across browsers, so `setLang()` relabels the two EUR options instead (`OPT` map).
- The English blog lead did not mention the weekly rotation, which it now does — the EN pool rotates too.
- The results callout quoted **Naturalfarma quoting itself**. It now cites the 2017 survey: "Mais de 8 em cada 10 utilizadores inquiridos declararam-se satisfeitos ou muito satisfeitos" — the unconditional 81.3% figure, attributed to a source rather than asserted by the seller.

**Still outstanding, put to the client and awaiting his decision** (all are claims, not defects):

- H1 "Trate a Próstata, **Evite a Cirurgia**" / "avoid surgery" — the surgery-avoidance claim removed from the info modal still sits in the headline.
- Proof bar "Sem efeitos adversos" / "No adverse effects" — absolute; the FAQ’s "geralmente bem tolerado" is the defensible version.
- Symptom card: erectile dysfunction "— tratável com abordagem natural" / "treatable with a natural approach".
- Callout stat: "70% dos homens com HPB têm disfunção eréctil associada. **SSP3-Forte ajudará.**"
- Section heading "Ingredientes com eficácia comprovada" / "Ingredients with proven efficacy".

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
