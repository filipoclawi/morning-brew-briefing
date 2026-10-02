import json,sys,re
from pathlib import Path
from playwright.sync_api import sync_playwright
r=Path(__file__).resolve().parents[1]
data=json.loads((r/'editions.json').read_text())
paths={'index.html':data[-1],**{f'editions/{e["end"]}/index.html':e for e in data}}
base=sys.argv[1] if len(sys.argv)>1 else r.as_uri()+'/'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in [390,1440]:
  page=b.new_page(viewport={'width':width,'height':900});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  for path,e in paths.items():
   response=page.goto(base+path,wait_until='networkidle')
   if base.startswith('https:'):assert response.status==200
   assert page.locator('article').count()==len(e['cards'])
   assert page.locator('nav a').count()==len(data)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),path
   assert not errors,errors
   for a in page.locator('article a').all():assert re.fullmatch(r'https://www\.morningbrew\.com/issues/[a-z0-9-]+',a.get_attribute('href'))
   if base.startswith('https:'):
    page.locator('nav a[aria-current="page"]').click();page.wait_for_load_state('networkidle')
   else:
    page.goto(page.locator('nav a[aria-current="page"]').evaluate('(a)=>a.href')+'index.html')
   assert page.locator('article').count()==len(e['cards'])
   if e==data[-1]:page.screenshot(path=str(r/f'test-results-{width}.png'),full_page=True)
 b.close()
for f in [r/'index.html',r/'editions.json',r/'styles.css',r/'README.md',*r.glob('editions/*/index.html')]:
 text=f.read_text();assert not re.search(r'@|Label_\d+|mbuuid|mbcid|utm_|/home/|kid=|ce0ae909|Armin|Hermes',text,re.I),f
assert sum(e['sourceCount'] for e in data)==12
assert len(data)==6 and sum(len(e['cards']) for e in data)==30
print('PASS: root and 6 archives; 390/1440px; 30 unique cards; 12 source issues; navigation, links, privacy; no errors or overflow')
