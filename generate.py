#!/usr/bin/env python3
"""Gera o site estático em public/ a partir de data/snapshots e data/history.csv."""
import csv, glob, html, json, os, shutil, statistics, sys, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
CONDS = ["Novo", "Excelente", "Muito Bom", "Bom", "Outlet"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def load_cfg():
    return json.load(open(os.path.join(ROOT, "config.json")))


def brl(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s


def data_br(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {y}"


def amazon_url(q, cfg):
    return "https://www.amazon.com.br/s?" + urllib.parse.urlencode({"k": q, "tag": cfg["AMAZON_TAG"]})


def ml_url(q, cfg):
    u = "https://lista.mercadolivre.com.br/" + urllib.parse.quote(q.lower().replace(" ", "-"))
    w, t = cfg.get("ml_matt_word", ""), cfg.get("ml_matt_tool", "")
    if w and t:  # formato dos links gerados pelo painel de afiliados do ML
        u += "?" + urllib.parse.urlencode({"matt_word": w, "matt_tool": t})
    return u


def latest_snapshot():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "snapshots", "*.json")))
    if not files:
        sys.exit("sem snapshot; rode collector.py antes")
    return json.load(open(files[-1]))


def load_history():
    p = os.path.join(ROOT, "data", "history.csv")
    hist = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            hist.setdefault(r["slug"], {}).setdefault(r["date"], []).append(float(r["price"]))
    return {s: [(d, statistics.median(v)) for d, v in sorted(ds.items())] for s, ds in hist.items()}


def group(offers):
    g = {}
    for o in offers:
        e = g.setdefault(o["slug"], {"model": o["model"], "storage": o["storage"], "slug": o["slug"], "prices": [], "by": {}})
        e["prices"].append(o["price"])
        e["by"].setdefault(o["condition"], []).append(o["price"])
    for e in g.values():
        e["median"] = statistics.median(e["prices"])
        e["min"], e["max"] = min(e["prices"]), max(e["prices"])
    return g


def svg_chart(points):
    """points: [(data, valor)]. SVG simples, sem dependências."""
    if len(points) < 2:
        return '<p class="muted">O histórico começa hoje. O gráfico aparece a partir do 2º dia de coleta.</p>'
    W, H, P = 640, 220, 40
    vals = [v for _, v in points]
    lo, hi = min(vals), max(vals)
    if hi == lo:
        hi = lo + 1
    xs = [P + i * (W - 2 * P) / (len(points) - 1) for i in range(len(points))]
    ys = [H - P - (v - lo) * (H - 2 * P) / (hi - lo) for v in vals]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"><title>{d}: {brl(v)}</title></circle>' for x, y, (d, v) in zip(xs, ys, points))
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Histórico da mediana de preço" class="chart">'
            f'<text x="{P}" y="20">{brl(hi)}</text><text x="{P}" y="{H - 8}">{brl(lo)}</text>'
            f'<text x="{W - P}" y="{H - 8}" text-anchor="end">{points[-1][0]}</text>'
            f'<path d="{path}" fill="none" stroke="#0a7" stroke-width="2"/>{dots}</svg>')


CSS = """body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:860px;margin:0 auto;padding:16px;color:#1b1b1b;line-height:1.5}
a{color:#06c}header a{color:inherit;text-decoration:none;font-weight:700}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:8px;text-align:left}
.big{font-size:2rem;font-weight:700;margin:.2em 0}.muted{color:#666;font-size:.9rem}.warn{background:#fff7e0;border-left:4px solid #e0a800;padding:8px 12px}
.cta{display:inline-block;margin:6px 8px 6px 0;padding:10px 16px;border-radius:6px;background:#ff9900;color:#111;text-decoration:none;font-weight:600}.cta.ml{background:#ffe600}
.chart{width:100%;height:auto;background:#fafafa}.chart text{font-size:12px;fill:#555}#q{width:100%;padding:10px;font-size:1rem;box-sizing:border-box}ul.list{columns:2;padding-left:18px}@media(max-width:600px){ul.list{columns:1}}"""


BEACON = ""  # Cloudflare Web Analytics; preenchido em build() se config.json tiver cf_beacon_token


def beacon_html(token):
    if not token:
        return ""
    return ("<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" "
            f"data-cf-beacon='{{\"token\": \"{token}\"}}'></script>")


def page(title, desc, canonical, body, jsonld=None):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{canonical}">
<style>{CSS}</style>{ld}</head><body><header><a href="/">FIPE do Celular</a> · <span class="muted">preço de celular usado, atualizado todo dia</span></header><main>{body}</main>
<footer class="muted"><hr><p>Divulgação: alguns links são de afiliado (Amazon, Mercado Livre). Se você comprar por eles, podemos receber uma comissão, sem custo extra para você.</p>
<p>Fonte dos preços: anúncios públicos de recondicionados da Trocafone, coletados automaticamente. Não temos vínculo com a loja. Não é a tabela FIPE oficial: a FIPE só publica preços de veículos.</p></footer>{BEACON}</body></html>"""


def model_page(e, hist, date, cfg):
    name = f"{e['model']} {e['storage']}"
    canonical = f"{cfg['base_url']}/{e['slug']}/"
    title = f"{name} usado: quanto vale hoje (tabela atualizada)"
    desc = f"{name} usado/recondicionado: mediana {brl(e['median'])}, faixa {brl(e['min'])} a {brl(e['max'])} por estado de conservação. Dados de {data_br(date)}."
    rows = "".join(f"<tr><td>{c}</td><td>{brl(min(e['by'][c]))}</td><td>{brl(max(e['by'][c]))}</td><td>{len(e['by'][c])}</td></tr>" for c in CONDS if c in e["by"])
    q = f"{e['model']} {e['storage']}"
    faq = [
        (f"Quanto vale um {name} usado hoje?", f"Em {data_br(date)}, o {name} recondicionado estava anunciado com mediana de {brl(e['median'])}, entre {brl(e['min'])} e {brl(e['max'])}, conforme o estado de conservação."),
        ("Esse é o preço de venda entre particulares?", "Não. É o preço de recondicionado anunciado em loja, com revisão e garantia. Entre particulares costuma ser menor, e a recompra por lojas paga menos ainda."),
        ("Existe tabela FIPE de celular?", "Não existe tabela FIPE oficial para celular; a FIPE publica preços de veículos. Esta página é uma referência independente, montada com preços públicos coletados todo dia."),
    ]
    jsonld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": a, "acceptedAnswer": {"@type": "Answer", "text": b}} for a, b in faq]}
    body = f"""<h1>{html.escape(name)} usado: quanto vale hoje</h1>
<p class="muted">Dados de <strong>{data_br(date)}</strong> · {len(e['prices'])} anúncio(s) em estoque</p>
<p>Preço mediano</p><p class="big">{brl(e['median'])}</p><p>Faixa: {brl(e['min'])} a {brl(e['max'])}</p>
<p class="warn">Preço de <strong>recondicionado na loja</strong>, não de venda entre particulares. Vendendo o seu para uma pessoa, espere menos; numa recompra de loja, menos ainda.</p>
<h2>Preço por estado de conservação</h2><table><tr><th>Estado</th><th>Mínimo</th><th>Máximo</th><th>Anúncios</th></tr>{rows}</table>
<h2>Histórico da mediana</h2>{svg_chart(hist.get(e['slug'], []))}
<h2>Comparar preço novo e usado</h2>
<a class="cta" rel="sponsored nofollow noopener" target="_blank" href="{html.escape(amazon_url(q, cfg))}">Ver na Amazon</a>
<a class="cta ml" rel="sponsored nofollow noopener" target="_blank" href="{html.escape(ml_url(q, cfg))}">Ver no Mercado Livre</a>
<p class="muted">Links de afiliado.</p>
<h2>Perguntas frequentes</h2>{''.join(f'<h3>{html.escape(a)}</h3><p>{html.escape(b)}</p>' for a, b in faq)}
<p><a href="/">← Ver todos os modelos</a></p>"""
    return page(title, desc, canonical, body, jsonld)


def home(groups, date, cfg):
    items = sorted(groups.values(), key=lambda e: (e["model"], int(''.join(c for c in e["storage"] if c.isdigit())) * (1024 if "TB" in e["storage"] else 1)))
    lis = "".join(f'<li data-n="{html.escape((e["model"] + " " + e["storage"]).lower())}"><a href="/{e["slug"]}/">{html.escape(e["model"])} {e["storage"]}</a>: {brl(e["median"])}</li>' for e in items)
    body = f"""<h1>Tabela FIPE de celular? Quanto vale seu celular usado hoje</h1>
<p>Preço mediano de celulares recondicionados, por modelo e armazenamento, atualizado todo dia. Dados de <strong>{data_br(date)}</strong>, {len(items)} modelos.</p>
<p class="warn">Os valores são de recondicionados anunciados em loja, não de venda entre particulares.</p>
<input id="q" type="search" placeholder="Busque: iPhone 13 128GB, Galaxy S23..." aria-label="Buscar modelo">
<ul class="list" id="l">{lis}</ul>
<script>document.getElementById('q').addEventListener('input',function(){{var v=this.value.toLowerCase().trim();document.querySelectorAll('#l li').forEach(function(li){{li.style.display=li.dataset.n.indexOf(v)>-1?'':'none'}})}});</script>"""
    jsonld = {"@context": "https://schema.org", "@type": "WebSite", "name": cfg["site_name"], "url": cfg["base_url"] + "/"}
    return page("FIPE do Celular: quanto vale seu celular usado hoje (tabela atualizada)", "Tabela diária com o preço de celulares usados e recondicionados: iPhone, Galaxy, Motorola e Xiaomi, com histórico por modelo e armazenamento.", cfg["base_url"] + "/", body, jsonld)


def build(out=None):
    global BEACON
    cfg = load_cfg()
    BEACON = beacon_html(cfg.get("cf_beacon_token", ""))
    out = out or os.path.join(ROOT, "public")
    snap = latest_snapshot()
    groups = {k: v for k, v in group(snap["offers"]).items() if len(v["prices"]) >= cfg.get("min_offers_for_page", 1)}
    hist = load_history()
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    urls = [cfg["base_url"] + "/"]
    open(os.path.join(out, "index.html"), "w").write(home(groups, snap["date"], cfg))
    for e in groups.values():
        os.makedirs(os.path.join(out, e["slug"]))
        open(os.path.join(out, e["slug"], "index.html"), "w").write(model_page(e, hist, snap["date"], cfg))
        urls.append(f"{cfg['base_url']}/{e['slug']}/")
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{snap['date']}</lastmod></url>" for u in urls)
    open(os.path.join(out, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    open(os.path.join(out, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {cfg['base_url']}/sitemap.xml\n")
    if cfg.get("indexnow_key"):
        open(os.path.join(out, cfg["indexnow_key"] + ".txt"), "w").write(cfg["indexnow_key"])
    json.dump({"date": snap["date"], "models": len(groups)}, open(os.path.join(out, "data.json"), "w"))
    print(f"gerado: {len(groups)} páginas de modelo em {out}")
    return groups


if __name__ == "__main__":
    build()
