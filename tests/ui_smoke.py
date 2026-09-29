import json,sys,re
from pathlib import Path
from playwright.sync_api import sync_playwright
r=Path(__file__).resolve().parents[1];data=json.loads((r/'editions.json').read_text());urls=['index.html']+[f'editions/{e["end"]}/index.html' for e in data]
base=sys.argv[1] if len(sys.argv)>1 else r.as_uri()+'/'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in [390,1440]:
  page=b.new_page(viewport={'width':width,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  for path in urls:
   page.goto(base+path,wait_until='networkidle');assert page.locator('article').count()==5;assert page.locator('nav a').count()==5
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),path
   assert not errors,errors
   for a in page.locator('article a').all():assert re.fullmatch(r'https://www\.morningbrew\.com/issues/[a-z0-9-]+',a.get_attribute('href'))
  page.screenshot(path=str(r/f'test-results-{width}.png'),full_page=True)
 b.close()
for f in [r/'index.html',r/'editions.json',*r.glob('editions/*/index.html')]:
 text=f.read_text();assert not re.search(r'@|Label_\d+|mbuuid|mbcid|utm_|/home/',text),f
assert sum(e['sourceCount'] for e in data)==9
print('PASS: root and all 5 archives; 390/1440px; 25 cards; source counts; clean links; privacy; no page errors or overflow')
