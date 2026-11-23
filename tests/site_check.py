"""MSP review site checks (locks the 23 Nov 2026 layout decisions).

1. data/site.json lists exactly the documents of the contract (Scope and Units.csv, phases A-C).
2. Every unit listed for a document exists in data/units/ and carries contract msp-unit/v1.
3. No JavaScript errors on the workboard, every document page and the help pages.
4. No horizontal page scroll on a phone (390 px) or tablet (768 px).
5. Running text of 120+ characters fills its container at 1440 px (no narrow measure).
Usage: python3 tests/site_check.py [base_url]   (default http://localhost:8765/)
"""
import json, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/'
EXPECTED = ['SUM','USE','PYR','FAQ','HELP','QSG-CCCM','QSG-CP','QSG-EDU','QSG-FSL','QSG-GBV','QSG-HEA','QSG-MA','QSG-NUT','QSG-PRO','QSG-SHE','QSG-WASH','MAN','FAC','SLD','WSE']
fails = []
site = json.load(open(os.path.join(ROOT, 'data/site.json'), encoding='utf-8'))
ids = [d['id'] for d in site['docs']]
if ids != EXPECTED: fails.append(f'site.json documents differ from the contract: {ids}')
for d in site['docs']:
    for u in d['units']:
        p = os.path.join(ROOT, 'data/units', u + '.json')
        if not os.path.exists(p): fails.append(f'{d["id"]}: unit file {u}.json missing'); continue
        if json.load(open(p, encoding='utf-8')).get('contract') != 'msp-unit/v1': fails.append(f'{u}: not contract msp-unit/v1')
pages = ['#board', '#how', '#glossary', '#about'] + [f'#doc/{i}' for i in ids]
NARROW = """()=>{const o=[];document.querySelectorAll('#main p').forEach(p=>{if(!p.offsetParent)return;const t=p.innerText.trim();if(t.length<120)return;
const par=p.parentElement,cs=getComputedStyle(par),a=par.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
if(a-p.getBoundingClientRect().width>40)o.push(t.slice(0,50))});return o}"""
with sync_playwright() as pw:
    exe = '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None
    b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
    for w in (390, 768, 1440):
        pg = b.new_page(viewport={'width': w, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.add_init_script("localStorage.setItem('msp-entry',JSON.stringify('2026-11-23'))")
        for h in pages:
            pg.goto(BASE + h); pg.wait_for_timeout(350)
            if w < 1000:
                sw = pg.evaluate('document.documentElement.scrollWidth')
                if sw > w + 1: fails.append(f'{w}px {h}: horizontal scroll ({sw}px)')
            else:
                for t in pg.evaluate(NARROW): fails.append(f'{h}: narrow paragraph "{t}"')
        fails += [f'{w}px JS error: {e}' for e in errs]
        pg.close()
    b.close()
for f in fails: print('FAIL', f)
print('site check:', 'FAIL' if fails else 'OK', f'({len(pages)} pages x 3 widths)')
sys.exit(1 if fails else 0)
