# Job noturno (não criado automaticamente)

Comando exato (rodar 1x por dia, ex. 03:30 PT):

    bash /workspace/fipe-celular/nightly.sh

Leva cerca de 1,5 a 2h (≈2.970 páginas a 1 req/s). Falhas nos testes interrompem a publicação.
Saída do coletor em `data/collect.log`. O histórico fica em `data/history.csv`, que deve ser commitado no repo depois de cada execução (arquivos pequenos e separados).
