# Job noturno (não criado automaticamente)

Comando exato (1x por dia, ex. 03:30 PT):

    bash /workspace/fipe-celular/nightly.sh

Duração: ~20 a 25 min (coleta limitada a 1200 s via `BUDGET`, mais ~1 min de geração e publicação).
A coleta é incremental (`data/state.json`). Páginas com oferta são revisitadas toda noite. Páginas sem oferta só voltam depois de 7 dias. As nunca visitadas entram por ordem de prioridade (iPhone 11–17, Galaxy S21–S26 e linha A primeiro).
O site mostra ofertas vistas nos últimos 7 dias. Falha nos testes interrompe a publicação.
Depois de cada execução, commitar `data/history.csv` no repo.
