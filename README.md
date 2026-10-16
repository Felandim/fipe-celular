# FIPE do Celular

**No ar:** https://smooth-kayak-v3q2.here.now/

Preço diário de celulares usados e recondicionados no Brasil, por modelo e armazenamento, com histórico.
Não é a tabela FIPE oficial (a FIPE só publica preços de veículos).

- `collector.py`: lê o `sitemap.xml` público da Trocafone e as páginas de produto (`/p`), respeitando o robots.txt e com 1 req/s. Não usa a API de busca. Grava `data/snapshots/AAAA-MM-DD.json` e `data/history.csv`.
- `generate.py`: gera `public/` (home com busca, uma página por modelo+armazenamento, sitemap, robots, canonical, FAQ JSON-LD).
- `publish.sh`: publica no here.now e avisa o IndexNow. O GitHub Pages **não** é usado.
- `nightly.sh`: coleta → testes → gera → publica.
- `config.json`: base_url, tag Amazon, parâmetros de afiliado ML, chave IndexNow.

Testes: `python3 -m unittest discover -s tests`

Links "Ver na Amazon" e "Ver no Mercado Livre" são de afiliado (rel="sponsored").
