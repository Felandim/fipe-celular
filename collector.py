#!/usr/bin/env python3
"""Coleta preços públicos de celulares recondicionados da Trocafone.
Respeita robots.txt; usa só sitemap + páginas de produto (/p). Nunca usa a API de busca (parâmetro ft), bloqueada no robots.
"""
import csv, datetime as dt, gzip, json, os, re, sys, time, urllib.request, urllib.robotparser

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, "config.json")))
BASE = "https://www.trocafone.com.br"
UA = CFG["user_agent"]

PHONE_RE = re.compile(r"^/(apple-|samsung-|usado-|motorola-)?(iphone|galaxy|moto|xiaomi|redmi|poco)")
BAD_RE = re.compile(r"pelicula|capa|cabo|carregador|kit|estojo|protetor|conjunto|fone|suporte|case|adaptador|bateria|watch|ipad|tablet|-tab-|macbook|airpods|buds|caneta|pulseira|garantia|seguro|smart-tv|tv-|galaxy-fit")
CONDITIONS = [("muito bom", "Muito Bom"), ("excelente", "Excelente"), ("outlet", "Outlet"), ("bom", "Bom"), ("lacrado", "Novo"), ("novo", "Novo")]
POPULAR_RE = re.compile(r"iphone-1[1-7]|galaxy-(s2[1-6]|a[0-9]{2})")
STORAGE_RE = re.compile(r"(\d+)\s*(gb|tb)\b", re.I)
SMALL = {"pro": "Pro", "max": "Max", "plus": "Plus", "ultra": "Ultra", "fe": "FE", "mini": "mini", "iphone": "iPhone", "se": "SE", "xr": "XR", "xs": "XS", "x": "X"}
DROP = {"apple", "samsung", "usado", "seminovo", "smartphone", "celular", "5g", "4g"}


def fetch(url, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip", "Accept": "text/html,application/xhtml+xml", "Accept-Language": "pt-BR,pt;q=0.9"})
            with urllib.request.urlopen(req, timeout=12) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    b = gzip.decompress(b)
                return b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return None


def is_phone_url(url):
    path = url.split(".com.br", 1)[-1]
    return bool(PHONE_RE.match(path)) and not BAD_RE.search(path) and path.endswith("/p")


def sitemap_urls(text):
    return re.findall(r"<loc>([^<]+)</loc>", text or "")


def condition_of(name):
    n = (name or "").lower()
    for k, v in CONDITIONS:
        if re.search(r"\b" + k + r"\b", n):
            return v
    return None


def normalize_model(text):
    """'Samsung Galaxy S23 128 GB Verde - Bom' -> ('Galaxy S23', '128GB')."""
    ms = [m for m in STORAGE_RE.finditer(text or "") if m.group(2).lower() == "tb" or int(m.group(1)) >= 16]
    m = ms[0] if ms else None  # ignora RAM (4/6/8/12 GB)
    if not m:
        return None, None
    storage = f"{int(m.group(1))}{m.group(2).upper()}"
    before = text[: m.start()]
    before = re.sub(r"\(.*?\)", " ", before)
    before = re.sub(r"\b\d+\s*gb(\s*(de\s*)?ram)?\b|\bram\b|\bcom\b", " ", before, flags=re.I)
    toks = [t for t in re.split(r"[\s\-_/]+", before.lower()) if t and t not in DROP]
    if not toks:
        return None, None
    out = []
    for t in toks:
        if t in SMALL:
            out.append(SMALL[t])
        elif t == "galaxy":
            out.append("Galaxy")
        elif re.fullmatch(r"[a-z]\d+[a-z]*", t):  # s23, a54, g84
            out.append(t.upper())
        else:
            out.append(t.capitalize())
    return " ".join(out), storage


def slugify(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse_product_html(html, url=""):
    """Retorna lista de ofertas em estoque: dict(model, storage, slug, condition, price, spot_price, name, url)."""
    m = re.search(r'data-varname="__STATE__">\s*<script>(.*?)</script>', html or "", re.S)
    if not m:
        return []
    try:
        st = json.loads(m.group(1))
    except ValueError:
        return []
    offers = []
    for key, prod in st.items():
        if not (key.startswith("Product:") and isinstance(prod, dict) and prod.get("__typename") == "Product"):
            continue
        cats = json.dumps(prod.get("categories", ""))
        if "Smartphones" not in cats and "Celulares" not in cats:
            continue
        pname = prod.get("productName", "")
        for ref in prod.get("items") or []:
            item = st.get(ref.get("id")) or {}
            full = item.get("nameComplete") or (pname + " " + item.get("name", ""))
            model, storage = normalize_model(pname)
            if not model:
                model, storage = normalize_model(full)
            cond = condition_of(item.get("name")) or condition_of(full)
            if not model or not cond:
                continue
            for sref in item.get("sellers") or []:
                seller = st.get(sref.get("id")) or {}
                co = st.get("$" + sref.get("id") + ".commertialOffer") or {}
                if not co and isinstance(seller.get("commertialOffer"), dict):
                    co = st.get(seller["commertialOffer"].get("id"), {})
                price = co.get("Price") or 0
                if co.get("AvailableQuantity", 0) > 0 and price > 100:
                    offers.append({
                        "model": model, "storage": storage, "slug": slugify(f"{model} {storage}"),
                        "condition": cond, "price": round(float(price), 2),
                        "spot_price": round(float(co.get("spotPrice") or price), 2),
                        "name": full, "url": url,
                    })
    return offers


def arg(argv, name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default


def main(argv):
    """Modo incremental: cada execução processa um lote rotativo, com limite de tempo.
    Páginas sem oferta ficam 7 dias sem revisita; páginas com oferta são revisitadas toda noite."""
    budget = arg(argv, "--budget-seconds", 1500)
    limit = arg(argv, "--limit", 0)
    delay = float(CFG.get("delay_seconds", 1.0))
    today = dt.datetime.now().strftime("%Y-%m-%d")
    state_path = os.path.join(ROOT, "data", "state.json")
    state = json.load(open(state_path)) if os.path.exists(state_path) else {"pages": {}, "urls": [], "urls_date": ""}
    if state.get("urls_date") != today or not state.get("urls"):
        rp = urllib.robotparser.RobotFileParser()
        rp.parse((fetch(BASE + "/robots.txt") or "").splitlines())
        urls = []
        for sm in sitemap_urls(fetch(BASE + "/sitemap.xml")):
            if "/product-" in sm:
                urls += [u for u in sitemap_urls(fetch(sm)) if is_phone_url(u)]
                time.sleep(delay)
        if urls:
            state["urls"] = sorted(set(u for u in urls if rp.can_fetch(UA, u)))
            state["urls_date"] = today
    pages = state["pages"]
    def due(u):
        p = pages.get(u)
        if not p:
            return (0, u)  # nunca visitada
        if p["date"] == today:
            return None
        age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(p["date"])).days
        if p["offers"]:
            return (1, p["date"], u)
        return (2, p["date"], u) if age >= 7 else None
    queue = sorted(q for q in (due(u) for u in state["urls"]) if q)
    queue = [q[-1] for q in queue]
    # páginas-grupo (modelo+armazenamento) primeiro dentro das nunca visitadas
    queue.sort(key=lambda u: (u in pages, not POPULAR_RE.search(u), not re.search(r"\d(gb|-gb)/p$", u)))
    if limit:
        queue = queue[:limit]
    print(f"{len(state['urls'])} URLs; {len(queue)} na fila hoje", file=sys.stderr)
    t0, done = time.time(), 0
    for u in queue:
        if time.time() - t0 > budget:
            break
        html = fetch(u)
        pages[u] = {"date": today, "offers": parse_product_html(html, u) if html else []}
        done += 1
        if done % 25 == 0:
            print(f"  {done} páginas, {int(time.time() - t0)}s", file=sys.stderr)
            json.dump(state, open(state_path, "w"))
        time.sleep(delay)
    json.dump(state, open(state_path, "w"))
    save(current_offers(pages, today), today)
    left = len(queue) - done
    print(f"OK {today}: {done} páginas visitadas, {left} ficaram para depois", file=sys.stderr)


def current_offers(pages, today, max_age=7):
    out, seen = [], set()
    for u, p in pages.items():
        age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(p["date"])).days
        if age > max_age:
            continue
        for o in p["offers"]:
            k = (o["slug"], o["condition"], o["name"], o["price"])
            if k not in seen:
                seen.add(k); out.append(o)
    return out


def save(offers, day, partial=False):
    os.makedirs(os.path.join(ROOT, "data", "snapshots"), exist_ok=True)
    snap = {"date": day, "source": "trocafone.com.br", "partial": partial, "offers": offers}
    json.dump(snap, open(os.path.join(ROOT, "data", "snapshots", day + ".json"), "w"), ensure_ascii=False, indent=0)
    append_history(offers, day)


def append_history(offers, day):
    path = os.path.join(ROOT, "data", "history.csv")
    rows = []
    if os.path.exists(path):
        rows = [r for r in csv.DictReader(open(path)) if r["date"] != day]
    for o in offers:
        rows.append({"date": day, "slug": o["slug"], "model": o["model"], "storage": o["storage"], "condition": o["condition"], "price": o["price"]})
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "slug", "model", "storage", "condition", "price"])
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1:])
