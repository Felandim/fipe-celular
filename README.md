# FIPE do Celular

**No ar:** https://fipe-do-celular.pages.dev/ (Cloudflare Pages; o endereço antigo do here.now só redireciona)

Preço diário de celulares usados e recondicionados no Brasil, por modelo e armazenamento, com histórico.
Não é a tabela FIPE oficial (a FIPE só publica preços de veículos).

- `collector.py`: lê o `sitemap.xml` público da Trocafone e as páginas de produto (`/p`), respeitando o robots.txt e com 1 req/s. Não usa a API de busca. Grava `data/snapshots/AAAA-MM-DD.json` e `data/history.csv`.
- `generate.py`: gera `public/` (home com busca, uma página por modelo+armazenamento, sitemap, robots, canonical, FAQ JSON-LD).
- `publish.sh`: publica no Cloudflare Pages (projeto `fipe-do-celular`, via wrangler) e avisa o IndexNow. O GitHub Pages **não** é usado.
- `nightly.sh`: coleta → testes → gera → publica → checa se a home responde 200 (`data/reachability.log`) → registra analytics do Cloudflare (`cf_analytics.py` → `data/analytics-log.md`).
- `config.json`: base_url, tag Amazon, parâmetros de afiliado ML, chave IndexNow.

Testes: `python3 -m unittest discover -s tests`

Links "Ver na Amazon" e "Ver no Mercado Livre" são de afiliado (rel="sponsored").
