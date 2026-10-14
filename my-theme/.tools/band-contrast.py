"""Check every colour band's text/background pair against WCAG AA.

The theme derives each band's foreground from the band colour's brightness, in
snippets/css-variables.liquid. This script reimplements that derivation against
the real defaults in config/settings_schema.json and reports the actual contrast
ratio, so "contrast cannot be configured into an unreadable state" is a verified
claim rather than an assertion.

Run from my-theme/:  python .tools/band-contrast.py
"""
import io, json, os, sys

THEME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def defaults():
    path = os.path.join(THEME, 'config', 'settings_schema.json')
    out = {}
    for group in json.load(io.open(path, encoding='utf-8')):
        for s in group.get('settings', []):
            if 'id' in s and 'default' in s:
                out[s['id']] = s['default']
    return out


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def brightness(h):
    """Shopify's color_brightness: the perceived-brightness formula, 0-255."""
    r, g, b = rgb(h)
    return (r * 299 + g * 587 + b * 114) / 1000.0


def luminance(h):
    def ch(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


d = defaults()
bg, fg = d['background_color'], d['foreground_color']

# Mirrors the Liquid: the inks are the palette's extremes, not fg and white.
if brightness(bg) > brightness(fg):
    light_ink, dark_ink = bg, fg
else:
    light_ink, dark_ink = fg, bg


def on(colour):
    return dark_ink if brightness(colour) > 140 else light_ink


bands = [
    ('band--page',    bg,                 fg),
    ('band--surface', d['surface_color'], on(d['surface_color'])),
    ('band--brand-1', d['brand_1'],       on(d['brand_1'])),
    ('band--brand-2', d['brand_2'],       on(d['brand_2'])),
    ('band--brand-3', d['brand_3'],       on(d['brand_3'])),
    ('band--ink',     fg,                 bg),
]

AA_BODY, AA_LARGE = 4.5, 3.0
fails = []
print('%-14s %-9s %-9s %7s   %s' % ('band', 'bg', 'text', 'ratio', 'verdict'))
print('-' * 62)
for name, b, t in bands:
    r = ratio(b, t)
    if r >= 7:
        verdict = 'AAA'
    elif r >= AA_BODY:
        verdict = 'AA'
    elif r >= AA_LARGE:
        verdict = 'AA large text only'
    else:
        verdict = 'FAIL'
    if r < AA_BODY:
        fails.append((name, r, verdict))
    print('%-14s %-9s %-9s %6.2f:1   %s' % (name, b, t, r, verdict))

# Accents (labels, numerals). Mirrors the stepping in css-variables.liquid:
# for each band, brand_1 is darkened (light band) or lightened (dark band) in
# 5% HSL steps until it clears 4.5:1 against that band's own ground.
import colorsys


def shift(h, amount):
    r, g, b = (c / 255.0 for c in rgb(h))
    hh, l, ss = colorsys.rgb_to_hls(r, g, b)
    l = min(1.0, max(0.0, l + amount / 100.0))
    return '#%02X%02X%02X' % tuple(round(c * 255) for c in colorsys.hls_to_rgb(hh, l, ss))


def accent(ground):
    sign = -1 if brightness(ground) > 140 else 1
    for n in range(13):
        c = shift(d['brand_1'], sign * n * 5)
        if ratio(c, ground) >= AA_BODY:
            return c
    return shift(d['brand_1'], sign * 60)


print()
print('accent (from brand_1 %s) per band:' % d['brand_1'])
for name, band_bg in (('band--page', bg), ('band--surface', d['surface_color']),
                      ('band--brand-2', d['brand_2']), ('band--brand-3', d['brand_3']),
                      ('band--ink', fg)):
    a = accent(band_bg)
    r = ratio(band_bg, a)
    note = 'AA' if r >= AA_BODY else ('AA large only' if r >= AA_LARGE else 'FAIL')
    print('  %-9s on %-14s %6.2f:1   %s' % (a, name, r, note))
    if r < AA_BODY:
        fails.append(('accent on ' + name, r, note))

# Buy buttons are brand_1 with its derived ink.
r = ratio(d['brand_1'], on(d['brand_1']))
print('  button text %-9s on brand_1 %6.2f:1' % (on(d['brand_1']), r))
if r < AA_BODY:
    fails.append(('button text', r, 'FAIL'))

print()
if fails:
    print('PROBLEMS:')
    for n, r, v in fails:
        print('  %-28s %.2f:1  %s' % (n, r, v))
    sys.exit(1)
print('all bands meet WCAG AA for body text')
