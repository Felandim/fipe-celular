#!/usr/bin/env bash
# Publica public/ no Cloudflare Pages (permanente) e avisa o IndexNow. GitHub Pages NAO e usado.
# Credenciais: /home/box/precifica-state/cloudflare.json (nunca versionar).
set -euo pipefail
cd "$(dirname "$0")"
PROJECT=$(python3 -c "import json;print(json.load(open('config.json'))['cf_pages_project'])")
BASE=$(python3 -c "import json;print(json.load(open('config.json'))['base_url'])")
KEY=$(python3 -c "import json;print(json.load(open('config.json'))['indexnow_key'])")
source /workspace/bin/cf-env.sh
(cd /workspace/.cf-work && wrangler pages deploy /workspace/fipe-celular/public --project-name="$PROJECT" --branch=main --commit-dirty=true)
sleep 5
curl -fsS -o /dev/null "$BASE/$KEY.txt"   # chave do IndexNow no ar antes de avisar
python3 indexnow.py
