"""End-to-end check of the review round (built 24 Nov 2026) against a local Firestore emulator.

Runs the page with ?emu=127.0.0.1:8085 (honoured only on localhost) and plays several reviewers.
Locks these behaviours:
 1. Round closed (no ?emu, SEND_ENABLED false): a personal link makes no database request and says the round is not open.
 2. A personal link is removed from the address bar and opens My review with the reviewer code.
 3. Taking a section, checking rows (Correct, Suggest change) and undoing a check reach the server.
 4. A section stage held by one person is not offered to another; one person takes one stage per section.
 5. The clinical stage is offered only on sections with safety rows, and covers only those rows.
 6. Complete is available only when every row of the stage is checked; completed stages show on Progress.
 7. An invalid link is refused. No horizontal scroll on My review and Progress at 390 px.
Usage: start the emulator with the combined rules on 127.0.0.1:8085 (project demo-msp) and a static
server on :8765, then: python3 tests/round_check.py
"""
import json, os, sys, urllib.request
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'http://localhost:8765/'
EMU = '127.0.0.1:8085'
DB = f'http://{EMU}/v1/projects/demo-msp/databases/(default)/documents'
OWNER = {'Authorization': 'Bearer owner', 'Content-Type': 'application/json'}
K = {'L1': 'a' * 40, 'LT': 'b' * 40, 'C1': 'c' * 40, 'OFF': 'd' * 40}
fails = []

def req(method, path, body=None):
    r = urllib.request.Request(DB + path, method=method, headers=OWNER, data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(r) as f: return json.loads(f.read() or b'{}')
    except urllib.error.HTTPError as e:
        return {'_status': e.code}

def fv(v):
    if isinstance(v, bool): return {'booleanValue': v}
    if isinstance(v, list): return {'arrayValue': {'values': [fv(x) for x in v]}}
    return {'stringValue': str(v)}

def put(path, obj): req('PATCH', '/' + path, {'fields': {k: fv(v) for k, v in obj.items()}})

def get(path): return req('GET', '/' + path)

# reset and seed (same package rule as the production seed: clinical stage where a section has safety rows)
urllib.request.urlopen(urllib.request.Request(f'http://{EMU}/emulator/v1/projects/demo-msp/databases/(default)/documents', method='DELETE'))
site = json.load(open(os.path.join(ROOT, 'data/site.json'), encoding='utf-8'))
units = {}
for d in site['docs']:
    for u in d['units']:
        rows = json.load(open(os.path.join(ROOT, 'data/units', u + '.json'), encoding='utf-8'))['rows']
        units[u] = rows
        put(f'mspPackages/{u}', {'stages': ['language', 'technical'] + (['clinical'] if any(r['type'] == 'safety' for r in rows) else []), 'clinicalScope': 'safety'})
put(f'mspReviewers/{K["L1"]}', {'rid': 'R01', 'roles': ['language'], 'active': True})
put(f'mspReviewers/{K["LT"]}', {'rid': 'R02', 'roles': ['language', 'technical'], 'active': True})
put(f'mspReviewers/{K["C1"]}', {'rid': 'R03', 'roles': ['clinical'], 'active': True})
put(f'mspReviewers/{K["OFF"]}', {'rid': 'R04', 'roles': ['language'], 'active': False})

def expect(cond, msg):
    if not cond: fails.append(msg)

with sync_playwright() as pw:
    exe = '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None
    b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()

    def page(key, emu=True, w=1440):
        ctx = b.new_context(viewport={'width': w, 'height': 900})
        ctx.add_init_script("localStorage.setItem('msp-entry',JSON.stringify('2026-11-23'))")
        pg = ctx.new_page(); pg.errs = []; pg.dbreq = []
        pg.on('pageerror', lambda e: pg.errs.append(str(e)))
        pg.on('request', lambda r: pg.dbreq.append(r.url) if ('firestore' in r.url or EMU in r.url) else None)
        pg.route('**/firestore.googleapis.com/**', lambda r: r.abort())  # tests never reach the live database
        pg.goto(BASE + ('?emu=' + EMU if emu else '') + '#k=' + key); pg.wait_for_timeout(900)
        return pg

    def click(pg, sel, wait=700):
        pg.locator(sel).first.click(); pg.wait_for_timeout(wait)

    # 1 closed round
    p0 = page(K['L1'], emu=False)
    expect(not p0.dbreq, f'1 round closed but the page called the database: {p0.dbreq[:2]}')
    expect('has not opened yet' in p0.inner_text('#main'), '1 closed round: My review does not say the round is not open')
    expect('#k=' not in p0.url, '2 key left in the address bar (closed round)')
    p0.context.close()

    # 2-3 reviewer R01 (language)
    p1 = page(K['L1'])
    expect('#k=' not in p1.url and p1.url.endswith('#mine'), f'2 key not removed from the address bar: {p1.url}')
    expect('R01' in p1.inner_text('#main'), '2 My review does not show the reviewer code')
    click(p1, '[data-ract="claim"][data-u="SUM"][data-s="language"]', 1200)
    c = get('mspClaims/SUM__language')
    expect(c.get('fields', {}).get('rid', {}).get('stringValue') == 'R01', f'3 claim not stored: {c}')
    p1.goto(BASE + '?emu=' + EMU + '#doc/SUM/SUM'); p1.wait_for_timeout(900)
    first = [r for r in units['SUM'] if r.get('ne') and r['type'] not in ('keep', 'protected')]
    click(p1, f'tr[data-row="{first[0]["id"]}"] [data-act="ok"]', 900)
    chk = get(f'mspWork/{K["L1"]}/checks/SUM__language__{first[0]["id"]}')
    expect(chk.get('fields', {}).get('verdict', {}).get('stringValue') == 'ok', f'3 Correct not stored: {chk}')
    click(p1, f'tr[data-row="{first[1]["id"]}"] [data-act="edit"]', 300)
    p1.locator('tr.prf textarea').fill('परीक्षण पाठ'); p1.locator('tr.prf input').fill('test note')
    click(p1, 'tr.prf [data-act="send"]', 900)
    chk = get(f'mspWork/{K["L1"]}/checks/SUM__language__{first[1]["id"]}')
    expect(chk.get('fields', {}).get('text', {}).get('stringValue') == 'परीक्षण पाठ', f'3 correction not stored: {chk}')
    click(p1, f'tr[data-row="{first[0]["id"]}"] [data-act="redo"]', 900)
    chk = get(f'mspWork/{K["L1"]}/checks/SUM__language__{first[0]["id"]}')
    expect(chk.get('_status') == 404, f'3 undo did not remove the check: {chk}')

    # 4 R02 (language + technical): SUM language not offered; takes SUM technical; then not offered SUM language anywhere
    p2 = page(K['LT'])
    expect(not p2.locator('[data-ract="claim"][data-u="SUM"][data-s="language"]').count(), '4 a held stage is offered to another reviewer')
    click(p2, '[data-ract="claim"][data-u="SUM"][data-s="technical"]', 1200)
    expect('SUM' in p2.inner_text('#main') and 'Held until' in p2.inner_text('#main'), '4 technical stage not shown as held')
    click(p2, '[data-ract="release"][data-u="SUM"][data-s="technical"]', 1200)
    expect(not p2.locator('[data-ract="claim"][data-u="SUM"][data-s="language"]').count(), '4 after release, the other stage of the same section is offered to the same person')
    click(p2, '[data-ract="claim"][data-u="USE"][data-s="technical"]', 1200)
    expect(not p2.locator('[data-ract="claim"][data-u="USE"][data-s="language"]').count(), '4 a free stage of a section is offered to the person already holding its other stage')
    seat = get('mspSeats/SUM__R02')
    expect(seat.get('fields', {}).get('stage', {}).get('stringValue') == 'technical', f'4 seat not recorded: {seat}')

    # 5 clinical
    p3 = page(K['C1'])
    t = p3.inner_text('#main')
    no_safety = [u for u, rs in units.items() if not any(r['type'] == 'safety' for r in rs)]
    with_safety = [u for u, rs in units.items() if any(r['type'] == 'safety' for r in rs)]
    expect(not p3.locator(f'[data-ract="claim"][data-u="{no_safety[0]}"]').count(), f'5 clinical stage offered on {no_safety[0]} (no safety rows)')
    expect(p3.locator(f'[data-ract="claim"][data-u="{with_safety[0]}"][data-s="clinical"]').count() == 1, '5 clinical stage not offered where safety rows exist')
    click(p3, '[data-ract="claim"][data-u="SUM"][data-s="clinical"]', 1200)
    p3.goto(BASE + '?emu=' + EMU + '#doc/SUM/SUM'); p3.wait_for_timeout(900)
    nsafe = sum(1 for r in units['SUM'] if r['type'] == 'safety' and r.get('ne'))
    btns = p3.locator('[data-act="ok"]').count()
    expect(btns == nsafe, f'5 clinical stage shows {btns} checkable rows, expected {nsafe} safety rows')

    # 6 complete a small section (HELP) as R01 and see it on Progress
    p1.goto(BASE + '?emu=' + EMU + '#mine'); p1.wait_for_timeout(900)
    click(p1, '[data-ract="claim"][data-u="HELP"][data-s="language"]', 1200)
    p1.goto(BASE + '?emu=' + EMU + '#doc/HELP/HELP'); p1.wait_for_timeout(900)
    expect(p1.locator('.notice [data-ract="done"]').is_disabled(), '6 Complete enabled before all rows are checked')
    for _ in range(60):
        loc = p1.locator('[data-act="ok"]')
        if not loc.count(): break
        loc.first.click(); p1.wait_for_timeout(450)
    expect(not p1.locator('.notice [data-ract="done"]').is_disabled(), '6 Complete still disabled after every row is checked')
    click(p1, '.notice [data-ract="done"]', 1200)
    c = get('mspClaims/HELP__language')
    expect(c.get('fields', {}).get('done', {}).get('booleanValue') is True, f'6 completion not stored: {c}')
    p1.goto(BASE + '?emu=' + EMU + '#progress'); p1.wait_for_timeout(1000)
    expect('✓ R01' in p1.inner_text('#main'), '6 Progress does not show the completed stage')

    # 7 invalid link and phone layout
    p4 = page(K['OFF'])
    expect('not valid' in p4.inner_text('#main'), '7 inactive link not refused')
    for h in ('#mine', '#progress', '#doc/SUM/SUM'):
        p5 = page(K['L1'], w=390); p5.goto(BASE + '?emu=' + EMU + h); p5.wait_for_timeout(900)
        sw = p5.evaluate('document.documentElement.scrollWidth')
        expect(sw <= 391, f'7 390px {h}: horizontal scroll ({sw}px)')
        fails.extend(f'JS error {h}: {e}' for e in p5.errs); p5.context.close()
    for pg in (p1, p2, p3, p4):
        fails.extend(f'JS error: {e}' for e in pg.errs)
    b.close()

for f in fails: print('FAIL', f)
print('round_check:', 'PASSED' if not fails else f'{len(fails)} FAILED')
sys.exit(1 if fails else 0)
