#!/usr/bin/env bash
# Publica public/ no here.now (slug fixo) e avisa o IndexNow.
set -euo pipefail
cd "$(dirname "$0")"
SLUG=$(python3 -c "import json;print(json.load(open('config.json'))['herenow_slug'])")
/workspace/bin/herenow-publish.sh public --client cursor --slug "$SLUG"
python3 indexnow.py
