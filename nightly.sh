#!/usr/bin/env bash
# Job noturno: coleta -> testes -> gera -> publica -> IndexNow.
set -euo pipefail
cd /workspace/fipe-celular
python3 -u collector.py >> data/collect.log 2>&1
python3 -m unittest discover -s tests -q
python3 generate.py
./publish.sh
