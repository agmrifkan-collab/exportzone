"""Per-weight font subsetting from the text each weight actually renders. fonts_subset.py <site dir>"""
import http.server,threading,functools,socketserver,sys,glob,os,json
from playwright.sync_api import sync_playwright
from fontTools import subset
d=sys.argv[1]
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(("127.0.0.1",0),functools.partial(Q,directory=d));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
pages=sorted(os.path.basename(f) for f in glob.glob(d+"/*.html") if not os.path.basename(f).startswith(("google","index_1")))
JS=r"""() => {
  const S={M:new Set(),B:new Set(),H:new Set(),P:new Set()};
  const bk=w=>w<=500?'M':(w<=700?'B':'H');
  const put=(cs,txt)=>{ if(!txt) return; const fam=cs.fontFamily||'', w=parseInt(cs.fontWeight)||400, maru=fam.includes('MaruFoPro'), pan=fam.includes('Panton');
    for(const ch of txt){ if(pan) S.P.add(ch); if(maru) S[bk(w)].add(ch); } };
  const all=txt=>{ for(const ch of txt){ S.M.add(ch);S.B.add(ch);S.H.add(ch);S.P.add(ch);} };
  const tw=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let n;
  while(n=tw.nextNode()){ const el=n.parentElement; if(!el) continue; const t=el.tagName; if(t==='SCRIPT'||t==='STYLE'||t==='NOSCRIPT') continue;
    if(!n.nodeValue.trim()) continue; put(getComputedStyle(el),n.nodeValue); }
  for(const el of document.body.querySelectorAll('*')){
    for(const ps of ['::before','::after']){ const cs=getComputedStyle(el,ps), c=cs.content; if(c&&c!=='none'&&c!=='normal'&&/["']/.test(c)) put(cs,c.replace(/["']/g,'')); }
    for(const a of el.attributes) if(a.name.startsWith('data-')&&!/src|href/.test(a.name)||a.name==='placeholder') all(a.value);
  }
  for(const sc of document.scripts){ if(sc.src||/json/.test(sc.type)) continue; for(const t of (sc.textContent.match(/["'`][^"'`\n]*[^\x00-\x7f][^"'`\n]*["'`]/g)||[])) all(t); }
  return Object.fromEntries(Object.entries(S).map(([k,v])=>[k,[...v].join('')]));
}"""
S={k:set() for k in "MBHP"}
with sync_playwright() as p:
    b=p.chromium.launch()
    for page in pages:
        for w in (1440,1024,390):
            pg=b.new_page(viewport={"width":w,"height":900}); pg.route("**/*",lambda r:r.continue_() if "127.0.0.1" in r.request.url else r.abort())
            pg.goto(f"http://127.0.0.1:{port}/{page}",wait_until="domcontentloaded"); pg.wait_for_timeout(250)
            r=pg.evaluate(JS); [S[k].update(r[k]) for k in S]; pg.close()
    b.close()
safe=set("0123456789 .,:;/%+-()!?&'\"・、。「」（）〜ー…")
for k in "MBH": S[k]|=safe
S["P"]|=set(chr(c) for c in range(0x20,0x7f))   # full ASCII: count-up digits, future labels
json.dump({k:"".join(sorted(v)) for k,v in S.items()},open(d+"/fonts/subset-chars.json","w"),ensure_ascii=False)
def make(src,dst,chars,feats):
    o=subset.Options(); o.flavor="woff2"; o.layout_features=feats; o.notdef_outline=True
    f=subset.load_font(src,o); sub=subset.Subsetter(o); sub.populate(unicodes=[ord(c) for c in chars]); sub.subset(f); subset.save_font(f,dst,o)
    return os.path.getsize(src),os.path.getsize(dst),len(f.getBestCmap())
tot=[0,0]
for name,key,feats in [("MaruFoPro-Medium","M",["palt","liga"]),("MaruFoPro-Bold","B",["palt","liga"]),("MaruFoPro-Heavy","H",["palt","liga"]),
                       ("Panton-Bold","P",["kern","liga","locl"]),("Panton-ExtraBold","P",["kern","liga","locl"]),("Panton-Black","P",["kern","liga","locl"])]:
    a,bz,n=make(f"{d}/fonts/{name}.woff2",f"{d}/fonts/{name}.s.woff2",S[key],feats); tot[0]+=a; tot[1]+=bz
    print(f"{name}: {a//1024}KB -> {bz//1024}KB  ({len(S[key])} chars wanted, {n} in font)")
print("total",tot[0]//1024,"->",tot[1]//1024,"KB")
names=["MaruFoPro-Medium","MaruFoPro-Bold","MaruFoPro-Heavy","Panton-Bold","Panton-ExtraBold","Panton-Black"]
for f in [d+"/"+x for x in pages]+glob.glob(d+"/*.css"):
    s=open(f,encoding="utf-8").read(); t=s
    for nm in names: t=t.replace(nm+".woff2",nm+".s.woff2")
    if t!=s: open(f,"w",encoding="utf-8").write(t)
print("pages",len(pages))
