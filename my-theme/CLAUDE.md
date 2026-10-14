# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-product Shopify storefront theme, built on Shopify's **Skeleton theme**. It sells one hero product (currently a portable espresso machine).

**The design is dark-led, restrained and product-first.** Near-black ground, warm cream text, clay accent, with cream bands for relief. The client's references are Ka'Chava (warm tones, whitespace, bold spec numerals) and Starface *for its simplicity only* — explicitly not its colour or its humour.

**Why dark:** the client's wordmark is a metallic Bodoni (now toned clay/copper from the palette). A metallic reads as metal on a dark ground and as mud on a light one. Earlier cream-led versions left the mark, the labels and the numerals all looking washed out. If the palette is ever inverted, the metallic mark has to go with it.

Liquid + CSS only: no build step, no `package.json`, no test suite, no bundler. Files are pushed to Shopify as-is.

The theme lives in `my-theme/`, not at the repo root. Run all commands from `my-theme/`.

## Commands

Requires the Shopify CLI (v4.8.0 installed globally; no local dependencies to install).

```bash
shopify theme dev      # local preview with hot reload against a dev store
shopify theme check    # lint (theme-check:recommended, see .theme-check.yml)
shopify theme push     # upload to a store
shopify theme pull     # download store changes (overwrites local JSON templates)
shopify theme console  # Liquid REPL against the store — use to check object/filter output
```

There are no tests. `shopify theme check` is the only verification step. It currently reports 4 `RemoteAsset` warnings, all from the optional Google Fonts display face in `layout/theme.liquid` — see *The display font is deliberately remote* below.

## How a section finds the product

Every section that sells resolves the product the same way, in this order:

1. the section's own `product` setting,
2. `settings.featured_product` (Theme settings → Product),
3. **`collections['all'].products.first`**.

Step 3 matters more than it looks. Without it, an unset featured product meant
*every* buy control on the site rendered nothing: no Add to cart in the hero, no
sticky bar, an empty closing CTA, no Shop button, and therefore no route to the
product page at all. The store looked finished and could not be bought from.
Falling through to the catalogue means the theme sells whatever the store has
from the first product onward, and choosing a featured product still overrides it.

Seven sections carry this chain: `hero-product`, `sticky-buy-bar`, `cta-banner`,
`header`, `product-gallery`, `split-feature`, `cart`. Add it to any new section
that renders a price or a buy button.

**The buy path**, end to end: hero Add to cart (or the header Shop button →
product page → Add to cart) → `/cart` → Checkout → Shopify's hosted checkout.
The sticky bar repeats the first step on mobile, and the closing CTA repeats it
at the bottom of the homepage.

## The core constraint: the product must be swappable

The client may change what this site sells. Nothing about the current product may be hardcoded.

Two rules enforce this:

1. **No section names a product.** Every section that needs one has a `product` setting that falls back to `settings.featured_product`:
   ```liquid
   assign product = section.settings.product | default: settings.featured_product
   ```
   Changing the product the whole site sells is one field in Theme settings → Product.
2. **No section hardcodes a colour, and all copy is a setting.** Headlines, kickers, body copy, bullets, FAQ entries and review quotes are all schema settings or blocks, editable in the theme editor without touching Liquid.

When adding a section, follow both. A section that renders `{{ product.title }}` from a hardcoded handle, or that sets `color: #FF5C29`, breaks the brief.

## Architecture

### The section grid is the layout system

`assets/critical.css` gives every `.shopify-section` a three-column grid: `margin | content | margin`. Direct children land in the centre column; a child with class `full-width` spans `1 / -1` to reach the viewport edge. Every custom section wraps itself in `full-width` and then re-declares `grid-template-columns: var(--content-grid)` on an inner element, so a background colour bleeds edge to edge while the text stays in the measure.

Consequence: sections never set their own page margins or max-widths.

### Bands are the colour-blocking engine

This is the most important thing to understand before editing a section.

Every section has a `band` select whose values are CSS class names (`band--brand-1`, `band--ink`, …). Each band class sets `--band-bg` *and* `--band-fg` together, defined in `critical.css`. Section CSS then uses `var(--band-fg)` and `currentcolor` — never a literal colour, and never `var(--color-brand-1)` directly for text or borders.

The `--on-*` foreground tokens are **derived, not configured**: `snippets/css-variables.liquid` measures each brand colour with `color_brightness` and picks a light or dark foreground. That is why a merchant can set any brand colour without producing unreadable text. Bypassing the band system to hardcode a colour pair defeats this.

Current palette (the client's five colours): near-black `#1D1D1B` ground with cream `#F2EBDD` text, and three brand slots — clay `#B78368` (labels, numerals, every buy button), brown `#795A45` for the dark2 separation band, and cream `#F2EBDD` for product panels. `surface` is cream `#F2EBDD`, the light relief band. Olive `#777A4B` is `support_color` (`--color-support`), for small indicators such as the in-stock dot only: it is 3.8:1 against both cream and near-black, so it must never carry text or be a band.

Band usage on the homepage: dark, dark, dark2, dark, **cream**, photo, dark, **cream**, cream, dark, dark2. The two cream stretches are the rests; everything else is dark. Resist adding more light bands — the contrast between the two is what carries the page.

A matte-black product needs a light ground, which is why `hero-product` and `product-gallery` put their images on `brand-3` light panels regardless of the surrounding band.

### Settings flow into CSS variables, not into Liquid conditionals

`config/settings_schema.json` defines merchant settings → `snippets/css-variables.liquid` renders them into `:root` custom properties inside a `{% style %}` tag → `critical.css` and per-component styles consume them. Adding a global design token means editing both files.

Token groups: type scale (`--text-xs` … `--text-4xl`, all `clamp()`-based), spacing (`--space-*`, `--section-rhythm`), colour (`--color-brand-1..3` plus derived `--color-on-brand-*`, `--color-muted`, `--color-hairline`), shape (`--radius-block`, `--radius-pill`, `--outline-width`), motion (`--ease-out`, `--ease-spring`, `--dur-fast|base|slow`).

`layout/theme.liquid` renders `css-variables` first (inline, before `critical.css`) so the variables exist before any stylesheet reads them.

### The display font is deliberately remote, and needs its optical-size axis

Shopify's `font_picker` only offers its own library, which does not carry Bodoni Moda. So `settings.type_display_font` takes a **Google Fonts family name as plain text** (default `Bodoni Moda`), loaded non-blockingly in `layout/theme.liquid` via `media="print" onload="this.media='all'"`. Leaving it blank drops the external request and falls back to the picked heading font. That is the tradeoff behind the 2 `RemoteAsset` warnings from `theme check` — expected, not a regression.

**Bodoni is a Didone, so optical size is load-bearing.** The font is requested as `:opsz,wght@6..96,...`; without the axis in the *request*, Google serves a static instance and `font-variation-settings` is silently ignored. Two tokens carry it: `--display-variation` (`opsz 96`, thin hairlines for headlines) and `--label-variation` (`opsz 8`, sturdy hairlines for small letterspaced caps). A small label set at `opsz 96` visibly disintegrates.

The display and wordmark faces are usually the same family. `theme.liquid` detects that and emits **one** combined request — asking twice would let the second win and drop the axis.

Body text never uses the display face. A Didone at paragraph size is slow to read on screen.

### CSS and JS are colocated per component

Use `{% stylesheet %}` / `{% javascript %}` inside the component file. These tags work **only** in `sections/`, `blocks/`, and `snippets/`. Shopify deduplicates and concatenates them, so there is no import graph. `critical.css` holds the reset, the section grid, the band classes and shared primitives (`.btn`, `.display`, `.eyebrow`, `.card`, `.reveal`, `.visually-hidden`).

**Every `{% stylesheet %}` block is concatenated into ONE global sheet.** There is no scoping. This has already caused two live bugs:

- `sections/hello-world.liquid` (the unused upstream demo) carried `.icon { width: 300px }` for its logo. That rule sized **every icon on the site** to 300px, because it shares a class name with `snippets/icon.liquid`. The section is deleted.
- `sections/header.liquid` styled the bare element `header { height: 5rem; display: flex; justify-content: space-between }`. Six content sections use `<header>` for their heading block, so all of them were being squashed into the site-header's shape. Header and footer CSS is now scoped to `.site-header` / `.site-footer`.

Two rules follow. **Never use a bare element selector** in a section stylesheet — scope it to a class the section owns. **Never reuse a class name** across files unless it is a shared primitive from `critical.css`.

Run `python .tools/css-collisions.py` from `my-theme/` after touching any section CSS; it reports duplicate class ownership and bare element selectors. `theme check` catches neither.

### Colour is derived per band, and verified

`snippets/css-variables.liquid` derives two things that must not be hardcoded:

- **The inks.** `dark_ink` and `light_ink` are the palette's brightness extremes, *not* `foreground_color` and white. Assuming foreground is the dark one breaks on a dark-led palette — which this theme is — and every light band renders cream text on a cream ground.
- **The accent.** One clay cannot serve every band: it is 5.2:1 on the page ground, 2.7:1 on cream and 1.9:1 on the brown band. A variant is derived **per band** by stepping the colour with `color_contrast` until it clears 4.5:1 against that band's own ground, and each band class picks its own via `--color-accent`. Don't collapse this to one variant per light/dark kind: stepping against the worst dark band washed the page accent out to near-cream where raw clay already passed. Use `var(--color-accent)`, never `var(--color-brand-1)`, for text.

`--color-hairline` and `--color-muted` are redefined on `.band` as `color-mix` against `currentcolor`, so they follow the band rather than the page.

Run `python .tools/band-contrast.py` after any palette change. It reimplements the derivation against the real defaults and reports WCAG ratios; all bands currently pass AA for body text.

### Storefront templates

The upstream Skeleton ships these as bare unstyled markup. All are now themed and share `snippets/product-card.liquid` so a product looks the same wherever it is listed:

- `product.liquid` — PDP built like the homepage hero: media bleeding to the edge, copy on the container inset. Gallery and variant picker are both **radio inputs**, so image switching and variant selection work with no JavaScript. Variants are `name="id"`, each showing its own price and availability.
- `collection.liquid` — the grid behind `/collections/all` and every collection, with pagination.
- `collections.liquid` — the collection list at `/collections`.
- `featured-products.liquid` — a product grid for the homepage. Falls back to `collections['all']`, so it fills in with no configuration.

**This store sells one product.** The catalogue pages above are kept and working, but **nothing links to them**. Navigation points at the product and at the homepage's own sections instead:

- Header and footer menus fall back to `#how-it-works`, `#reviews` and `#faq`, each prefixed with `routes.root_url` so the anchors still resolve from the product page or the cart, not only from the homepage. Those ids live on `steps`, `testimonials` and `faq`.
- The header carries a **Shop** button pointing at the featured product, so there is a way to buy from every page.
- `featured-products` is not on the homepage — a grid of one product is noise. The section still exists and can be added from the theme editor if the range ever grows.

Assigning a real menu in Shopify replaces the fallback links entirely. If a second product is ever added, relink the catalogue: put `featured-products` back on the homepage and point the nav at `routes.all_products_collection_url`.

**`/products` is not a Shopify route.** The catalogue lives at `/collections/all` (`routes.all_products_collection_url`). Linking to `/products` 404s.

### What the theme owns, and where Shopify takes over

The theme's responsibility **ends at the Checkout button**:

- **Checkout is hosted by Shopify.** There is no `layout/checkout.liquid` and there cannot be one outside Shopify Plus. Style it in Settings → Checkout (logo, colours, typography); on Plus, with Checkout UI extensions. Nothing in this repo affects it.
- **Customer accounts are hosted by Shopify too.** `sections/header.liquid` uses the `<shopify-account>` web component, which is *new* customer accounts — Shopify renders login and the account area on its own domain. That is why there is no `templates/customers/` directory and none is needed. Only if the store were switched to **classic** customer accounts would the theme need `templates/customers/*.liquid`, which do not exist here.

So the pre-checkout flow the theme does own is: product form → `/cart/add` → cart page → `POST /cart` with `name="checkout"`.

### The buy flow

`{% form 'product', product %}` in `hero-product.liquid` posts to `/cart/add`. Two details matter:

- **The variant radios sit outside that form.** They have to stay direct children of `.hero__grid` for the CSS image swap, so they associate with the form through the HTML `form="..."` attribute instead of nesting. They are `name="id"`, so variant selection posts natively with no JavaScript.
- **`{{ form | payment_button }}`** renders Shopify's accelerated checkout (Shop Pay, Google Pay, PayPal), which skips the cart. It only appears if the merchant has it enabled in payment settings, so its absence in a dev store is not a bug.

`sections/cart.liquid` posts to `/cart` via `{% form 'cart', cart %}`. Quantities are `updates[]` in line order; the script submits on change and the `<noscript>` Update button covers the rest. Remove is a plain link to `item.url_to_remove` and needs no script.

The sticky bar carries its own product form and mirrors the hero's selected variant, so it can never add a variant other than the one on screen.

### Motion

`snippets/motion.liquid` is rendered once from `layout/theme.liquid` and holds **behaviour only**. The styles live where they belong: `.reveal` in `critical.css` (a shared primitive used by a dozen sections) and the scrolled-header shadow in `header.liquid` (which owns that class). Putting them in the snippet trips `ValidScopedCSSClass` — theme check wants a class styled in the file that uses it, or in the global sheet.

**Reveals are JavaScript, not `animation-timeline: view()`.** View timelines ship in Chrome and Edge but not Safari or Firefox, so the CSS-only version animated for roughly half of visitors and did nothing for the rest.

Two rules keep it safe:

- Content is visible at rest. `.motion-ready` is added by the script only once the observer exists, so no JavaScript means finished content, not a blank page.
- The failsafe reveals anything **already on screen** after 1.8s, and is deliberately *not* cancelled by the observer firing — the observer's first callback runs immediately for off-screen targets too, so cancelling there would kill the guard before it could help. It leaves below-fold elements alone, since those are meant to wait.

What animates: hero entrance staggered on load (it is above the fold, so it does not wait for a scroll), the accent rule drawing itself, section reveals with a sibling stagger, the statement photo drifting on its own view timeline where supported, spec figures counting up on entry, the header gaining a shadow once scrolled, and product-card images lifting on hover.

The count-up keeps the final value in the markup, so with no script or reduced motion it is simply the number.

### Sticky header and buy bar

`sections/header.liquid` sets `"tag": "header"` and `"class": "site-header-section"` so the **section wrapper** is the sticky element. Sticky on `.site-header` itself does nothing — a sticky element only travels inside its own parent, and that parent is just the header block. The `sticky` setting drives it through `:has(.site-header--sticky)`.

`sections/sticky-buy-bar.liquid` is `position: fixed`, so its place in the template does not matter (keep it last). An IntersectionObserver on `.hero` reveals it once the hero leaves view, falling back to a scroll offset on templates with no hero. It starts `hidden` and JavaScript reveals it: with no JS nothing appears, which is correct, since the hero and closing sections carry their own CTA. It adds `body.has-buybar` padding so the bar never traps content.

Icons size themselves from `--icon-size`, set inline by `snippets/icon.liquid`, rather than from the `width`/`height` attributes — presentation attributes lose to any CSS rule, so an attribute-sized icon is one stray selector away from breaking.

**Liquid is not evaluated inside `{% stylesheet %}`.** Per-item dynamic CSS must therefore come from an inline `style="--token: {{ value }}"` attribute, or from a fixed set of static rules. `sections/hero-product.liquid` uses the latter: eight `:nth-of-type(n):checked` rules, matching the eight-variant limit the markup enforces.

Mapping settings to styles:
- Setting controls **one** property → inline CSS variable (`style="--gap: {{ block.settings.gap }}px"`), consumed with `var(--gap)`.
- Setting controls **several** properties → the setting's `value` *is* a CSS class name, interpolated into `class` (`band`, `media_position`, `layout_direction`).

### Interaction is CSS-first

The interactive pieces deliberately avoid JavaScript so they work before hydration and under a blocked script:
- **Hero finish swatches** — radio inputs plus `:checked ~` sibling selectors swap the product image. Two traps here, each of which silently renders an invisible product: the radios must be direct children of `.hero__grid`, because `~` only reaches *siblings* and they have to sit beside both the copy and the media column; and the shots match on `:nth-of-type`, not `:nth-child`, because the stock chip is the media column's first child. The only JS keeps the buy button's `href` on the selected variant; without it the button still links to the product.
- **Review rail** — CSS scroll-snap on a focusable `role="region"`, not a carousel library. Every review is in the DOM.
- **FAQ** — native `<details>`/`<summary>`, which brings keyboard operation, screen-reader semantics and find-in-page expansion for free.
- **Scroll reveal** — `.reveal` uses `animation-timeline: view()` behind `@supports`, so the finished state is the default. Never park content at `opacity: 0` waiting on a script.

### The wordmark is live text, not an image

`snippets/wordmark.liquid` renders it as inline SVG. It **must not** become `<img src="wordmark.svg">`: the supplied artwork sets its type in Bodoni and pulls the face with an `@import` inside the file, and browsers render `<img>`-loaded SVG in a secure static mode that blocks external CSS and fonts — the mark would silently fall back to Times. Inlined, it uses the page's own font stack, the gradient is themeable, and it can drop to `currentcolor` on bands where it has too little contrast (`gold: false`).

`assets/wordmark-source.svg` is the client's original file, kept for reference only. Nothing renders it.

### Custom sections

`hero-product`, `product-gallery`, `statement`, `marquee`, `stats`, `feature-grid`, `split-feature`, `steps`, `pull-quote`, `testimonials`, `faq`, `cta-banner`. All carry presets, so they can be added from the theme editor. `templates/index.json` composes them into the homepage.

`stats` is the spec-numeral motif: value and unit are **separate settings** so the figure stays in the display face at full size while the unit stays in the sans at label size.

`feature-grid` renders **numbered rows, not icon cards**. Four icon tiles read as a dashboard, and one icon set cannot honestly cover both "18 bar pressure" and "cleans in ten seconds". It has no icon setting; don't add one back.

`statement` is the single photographic moment — one line over a full-bleed image. It exists to break the rhythm of type on flat grounds. One per page.

`pull-quote` carries the social proof at display size; `testimonials` follows with the rest in a compact rail. A rail alone asks the reader to work for the endorsement.

### Imagery

`assets/DEMO-IMAGES.txt` lists what ships and where it came from. Two kinds:

- **`product-coffee-maker.jpg`** — a cut-out of the product on white. Shown with `mix-blend-mode: multiply`, which drops the white to whatever band sits behind it, so one asset works on bone, sand or white with no visible box.
- **`demo-*.jpg`** — Pexels-licensed context photography, wired through the `demo_asset` setting on `split-feature` and on each `steps` block. This is a **filename of a theme asset**, used only when no image is picked in the editor; a picked image always wins. It exists so a fresh install does not render empty frames. Clear it before launch.

**Photos fill their frames.** `.split__frame` (4:5) and `.steps__frame` (5:4) crop with `object-fit: cover`. An earlier version let images size themselves, which rendered a small object floating in a large empty box and made the whole page read as unfinished. Keep the frame.

### The hero leads with the product

`hero-product` is not a boxed square beside some text. The media column bleeds to the viewport edge while the copy column holds the container inset with `padding-inline-start: max(var(--page-margin), calc((100vw - var(--page-width)) / 2 + var(--page-margin)))`. That asymmetry is what lets the product be shown large.

The buy controls — price, finish picker, CTA carrying the price, rating, trust row — all sit above the fold. That grouping is deliberate; splitting it up is what made an earlier version feel like a brochure rather than a shop.

`product-gallery` exists because the page otherwise showed the product once and then only talked about it. Each tile resolves picked image → the product's image at that index → bundled demo asset.

### Sizing rules that were got wrong once

Three bugs produced a page that looked "half done". They are worth not repeating:

1. **Never put `max-width` on an element that also carries `.in`-style auto margins.** It centres the block *and* squeezes it — section headings collapsed to ~317px and wrapped to four lines. Cap the heading itself: `.section-title` sets `max-width: 20ch`.
2. **The type scale had a 7rem top end.** Display type outran its column. The scale now tops out at 4.5rem (`--text-4xl`) and 3.25rem (`--text-3xl`).
3. **Icons were repeatedly too big.** Inline icons sit at 13–16px beside text, never 22–28px. They are punctuation, not illustration. The feature section dropped icons entirely.

4. **`clamp()` and `calc()` need whitespace around `+` and `-`.** `clamp(2.75rem,2.1rem+2.6vw,4.25rem)` is invalid CSS: the browser drops the whole declaration silently and the element falls back to inherited size. Three headline sizes failed this way at once and the page looked flat for no visible reason. Grep for `rem+`, `px+` and `vw+` before blaming the design.

5. **`height: 100%` on a grid child resolves against an auto row**, and an auto row is sized by a replaced element's intrinsic height. A full-bleed image band built that way grew to 1920px and centred its caption off-screen. `statement` positions both the image and the overlay absolutely inside a band that owns its own `aspect-ratio`.

6. **`aspect-ratio` plus only `max-height` shrinks the *width*.** The statement band has an explicit `width: 100%` so the ratio drives height, not the reverse.
7. **A full-bleed scroll rail needs the container's inset, not the viewport's.** `.quotes__rail` uses `padding-inline: max(var(--page-margin), calc((100vw - var(--page-width)) / 2 + var(--page-margin)))` so its first card lines up with the heading above it.

Page width is `78rem` (the "narrow" option) with a `clamp(20px, 4vw, 48px)` gutter. `90rem`+ was too wide for this layout and left the copy stranded.

### JSON files under `templates/` and `sections/*-group.json` are generated

They carry an auto-generated banner and are rewritten by the theme editor and `shopify theme pull`. Prefer building sections, blocks and snippets; let merchants assemble templates in the editor.

## Conventions

- **All user-facing text is translated.** Storefront strings live in `locales/en.default.json` (`{{ 'cart.checkout' | t }}`). Theme-editor strings — every schema `name`, `label`, `info`, option label and preset name — live in `locales/en.default.schema.json` under `general` / `labels` / `info` / `options`, referenced with the `t:` prefix. A missing key renders as the raw `t:…` string in the editor, so add the key in the same change as the setting. English only.
- **Icons are inline SVG via `{% render 'icon', name: '…' %}`**, never emoji. Decorative by default; pass `label` only when the icon is a control's sole content. Adding an icon means a new `{% when %}` in `snippets/icon.liquid` *and* a new option in each section that offers the icon select.
- **Snippets and statically-rendered blocks get a `{% doc %}` header** with `@param` (`[brackets]` = optional) and `@example`. See `snippets/icon.liquid`, `snippets/image.liquid`.
- Blocks output `{{ block.shopify_attributes }}` on their root element for theme-editor targeting.
- Accessibility floor, applied throughout: 44px minimum touch targets, visible `:focus-visible` rings (never removed), `prefers-reduced-motion` honoured globally in `critical.css`, and one `<h1>` per page.
- `{% schema %}` JSON does not support comments or trailing commas.
- **A `range` value must land exactly on a step**, or the upload is rejected with `Setting 'x' must be a step in the range`. For `min: 10, step: 5` the legal values are 10, 15, … — 64 is not one of them. `theme check` does not catch this; it only surfaces on `shopify theme push`. The same applies to `select` values, which must match an option exactly. Validate template values against their section schema before pushing.

## Reference docs in this repo

`AGENTS.md` (~1500 lines) is the upstream Shopify agent reference: exhaustive Liquid delimiter/operator/filter/object/tag tables, schema validation rules, and worked examples per asset kind. Consult it for Liquid API details rather than guessing. `copilot-instructions.md` is a byte-identical copy.

If the Shopify AI Toolkit / `learn_shopify_api` tool is available in the session, call it once before Liquid theme work — see https://shopify.dev/docs/apps/build/ai-toolkit.
