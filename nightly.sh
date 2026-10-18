#!/usr/bin/env bash
# Job noturno, seguro para rotina diária (~20-30 min):
# coleta incremental com limite de tempo -> testes -> gera -> publica (Cloudflare Pages) -> IndexNow
# -> checa se o site responde -> registra analytics (Cloudflare Web Analytics via GraphQL).
set -euo pipefail
cd /workspace/fipe-celular
BASE=$(python3 -c "import json;print(json.load(open('config.json'))['base_url'])")
python3 -u collector.py --budget-seconds "${BUDGET:-1200}" >> data/collect.log 2>&1
python3 -m unittest discover -s tests -q
python3 generate.py
./publish.sh
# Checagem de alcance: home do site novo deve responder 200 (3 tentativas). Falha vai para data/reachability.log.
ok=0
for i in 1 2 3; do
  code=$(curl -s -o /dev/null -m 20 -w '%{http_code}' "$BASE/" || echo 000)
  [ "$code" = 200 ] && { ok=1; break; }
  sleep 20
done
if [ "$ok" = 1 ]; then
  echo "$(date '+%F %T %Z') OK 200 $BASE/" >> data/reachability.log
else
  echo "$(date '+%F %T %Z') FALHA home=$code $BASE/ (3 tentativas)" | tee -a data/reachability.log >&2
fi
# Analytics (visitas + de onde vieram); não derruba o job se a API falhar.
python3 cf_analytics.py "${BASE#https://}" 30 --log data/analytics-log.md || echo "analytics: falhou (ver acima)" >&2
