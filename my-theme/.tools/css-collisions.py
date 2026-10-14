"""Find class selectors defined in more than one file.

Shopify concatenates every {% stylesheet %} block into one global sheet, so a
class name used by two components is a real collision, not a style question.
"""
import io, re, glob, os, collections


THEME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Shared primitives live in critical.css on purpose; sections are expected to use them.
SHARED = {
    'band', 'band--page', 'band--surface', 'band--brand-1', 'band--brand-2', 'band--brand-3',
    'band--ink', 'band-pad', 'band-pad--tight', 'display', 'section-title', 'eyebrow', 'lede',
    'measure', 'btn', 'btn--primary', 'btn--secondary', 'btn--accent', 'card', 'reveal',
    'visually-hidden', 'skip-link', 'shopify-section', 'full-width', 'icon',
    'wordmark',  # header only references it via :has(), it does not restyle it
}

owners = collections.defaultdict(set)

def classes_in(css):
    """Classes a file OWNS — the first class in each selector.

    Only the leftmost class counts. `.hero__actions .qty` adjusts a component
    from the outside and is safely scoped; it does not make that file an owner
    of `.qty`. Counting every class token reports those as collisions and the
    real ones get lost in the noise.
    """
    body = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    sels = re.sub(r'\{[^{}]*\}', '', body)
    owned = set()
    for chunk in sels.split('}'):
        for sel in chunk.split(','):
            sel = sel.strip()
            if not sel or sel.startswith('@'):
                continue
            m = re.search(r'\.(-?[_a-zA-Z][\w-]*)', sel)
            if m:
                owned.add(m.group(1))
    return owned

crit = os.path.join(THEME, 'assets', 'critical.css')
for c in classes_in(io.open(crit, encoding='utf-8').read()):
    owners[c].add('critical.css')

for f in sorted(glob.glob(os.path.join(THEME, 'sections', '*.liquid'))
                + glob.glob(os.path.join(THEME, 'snippets', '*.liquid'))
                + glob.glob(os.path.join(THEME, 'blocks', '*.liquid'))):
    src = io.open(f, encoding='utf-8').read()
    for m in re.finditer(r'\{%\s*stylesheet\s*%\}(.*?)\{%\s*endstylesheet\s*%\}', src, re.S):
        for c in classes_in(m.group(1)):
            owners[c].add(os.path.basename(f))

clashes = {c: sorted(o) for c, o in owners.items() if len(o) > 1 and c not in SHARED}
if clashes:
    print('CLASS COLLISIONS (same name styled in multiple files):')
    for c, o in sorted(clashes.items()):
        print('  .%-24s %s' % (c, ', '.join(o)))
else:
    print('no class collisions')

# Any section styling a bare element selector leaks site-wide too.
print()
leaks = []
for f in sorted(glob.glob(os.path.join(THEME, 'sections', '*.liquid'))
                + glob.glob(os.path.join(THEME, 'snippets', '*.liquid'))
                + glob.glob(os.path.join(THEME, 'blocks', '*.liquid'))):
    src = io.open(f, encoding='utf-8').read()
    for m in re.finditer(r'\{%\s*stylesheet\s*%\}(.*?)\{%\s*endstylesheet\s*%\}', src, re.S):
        body = re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
        for sel in re.findall(r'(^|\})\s*([^{}@]+)\{', body):
            for part in sel[1].split(','):
                part = part.strip()
                if part and not part.startswith(('.', '#', '@', ':', '*', '%', 'from', 'to')) \
                   and re.match(r'^[a-z][a-z0-9]*(\s|$|:|>)', part):
                    leaks.append('%s: %s' % (os.path.basename(f), part))
if leaks:
    print('BARE ELEMENT SELECTORS (apply site-wide):')
    for l in sorted(set(leaks)):
        print('  ' + l)
else:
    print('no bare element selectors in section stylesheets')
