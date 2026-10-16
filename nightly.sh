#!/usr/bin/env bash
# Job noturno, seguro para rotina diária (~20-30 min):
# coleta incremental com limite de tempo -> testes -> gera -> publica -> IndexNow.
set -euo pipefail
cd /workspace/fipe-celular
python3 -u collector.py --budget-seconds "${BUDGET:-1200}" >> data/collect.log 2>&1
python3 -m unittest discover -s tests -q
python3 generate.py
./publish.sh
