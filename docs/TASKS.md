# Controle de tarefas da simulação — Fase 1

Extensão da Fase 2: [ADMISSION](ADMISSION.md) define reservas sintéticas associadas a TASKS. `claim` de admissão limita a execução global a uma; reserva/capacidade, remoção e exclusão são transacionais. [COORDINATOR](COORDINATOR.md) implementa liderança, fila efêmera e filho sintético, sem recebimento de PDF. `require_task` revalida também geração/validade do líder para reservas coordenadas, portanto claim, heartbeat e finish antigos são cercados após takeover. Reservas anteriores com geração NULL mantêm o protocolo base. O restante deste documento preserva o histórico da primeira entrega; suas referências a coordenador futuro não representam o estado desta extensão sintética.

Fecha o critério de exclusão/cancelamento da base local. A tabela `simulation_tasks` guarda somente IDs, revisão, estado, executor, hash de lease, validade e motivo técnico. Não contém documento, imagem, texto extraído, resultado, senha ou payload JSON. Não há endpoint público de tarefas, coordenador automático ou executor de OCR/cálculo nesta entrega.

Estados: queued → running → finished; queued/running podem virar cancelled, e leases running vencidas podem virar expired. O controle é serviço interno, compartilhável pela futura camada de processamento.

## Protocolo interno

- `reserve(db, actor, simulation_id, revision)`: dentro de transação de escrita, revalida ator, autorização, recurso e revisão. Impede operações ativas em outra simulação do mesmo dono.
- `claim(engine, task_id, executor_id, ttl)`: transação curta; apenas um executor assume a tarefa e apenas uma tarefa executa por simulação. Devolve lease aleatória; banco guarda somente hash. Validade de 1–300 segundos, padrão 60.
- `heartbeat(engine, task_id, lease, ttl)`: renova apenas lease válida, com ator/revisão/tombstone revalidados.
- `finish(engine, task_id, lease, persist)`: abre nova transação de escrita, revalida lease/ator/tombstone/revisão e só então chama a persistência estruturada. Resultado e estado finished confirmam juntos; exceção desfaz ambos. Lease é consumida, sem replay.
- `expire(engine)`: comando interno explícito que expira somente leases vencidas. Não roda no startup e não cancela uma instância viva por iniciar outra.

Extensão de persistência: finish devolve o retorno do callback depois do commit, sem mudar seu guard de lease consumida. [INVOICE-STORAGE](INVOICE-STORAGE.md) integra cabeçalho/filhos/proveniência/vínculo e revisão do conjunto ao mesmo commit. O serviço finish_normalized admite replay somente para publicação já confirmada, mesmo conteúdo e hash da lease original, com autorização/revisão revalidadas; não executa o callback outra vez. Remoção elimina o vínculo e impede recriação por replay. TASKS usa revisão da unidade, separada da nova dataset_revision, para permitir publicação incremental sem cancelar as demais tarefas independentes.

Trabalho pesado ocorre **antes** de finish, sem transação SQL aberta. O callback persist é código interno, não payload vindo da API: não faz OCR/rede, não chama commit e não recebe documentos por esta infraestrutura. A futura integração deve usar esse ponto de confirmação; gravar por fora dele viola o protocolo.

## Exclusão e revisão

`delete_simulation` marca tombstone, incrementa revisão, libera slot e cancela tarefas queued/running **na mesma transação**. Cancelamento limpa hash/validade de lease. Heartbeat, claim e finish posteriores falham. Guard da simulação também recarrega objetos ORM antigos. Salvar uma nova revisão da unidade cancela operações da revisão anterior na mesma transação.

Uma conclusão que obtém o lock de escrita antes da exclusão pode terminar; a exclusão posterior torna a simulação inacessível normalmente. Se a exclusão confirma primeiro, o callback de persistência não é chamado. Falha no commit da exclusão desfaz tombstone, liberação da vaga e cancelamento em conjunto.

O cancelamento é lógico e revoga a autorização de gravar. Não há processo de OCR para interromper nesta fase. Na Fase 2, o coordenador real deverá observar o estado cancelado, encerrar processos isolados e aplicar limites de recursos/admissão. A primeira entrega da Fase 2 já integra faturas/filhos à exclusão: itens antes das medições e cascatas dos demais dependentes, na transação do tombstone/cancelamento. Isso não implementa remoção individual de fatura ou coordenador.

## Evidência

Testes sintéticos com thread de executor bloqueada fora do banco: excluir pela API, liberar o executor, tentar finish e verificar que o callback nunca gravou. Tarefa queued também não pode ser assumida depois. Verificados ainda rollback conjunto da exclusão, resultado/estado atômicos, lease falsa/repetida, cancelamento por revisão, isolamento por dono, dois claims concorrentes e recuperação somente de lease vencida.

Migração `0003_simulation_tasks`, sem mudanças em dependências ou dados existentes. Upgrade limpo, upgrade preservando raízes, downgrade/upgrade em descartável e metadata Alembic check fazem parte da suíte. A validação executada é SQLite; PostgreSQL e operação de processos reais continuam nas fases correspondentes.

Regressão com as tabelas reais de `0004_invoices`: `finish` grava grafo sintético de cabeçalho, medições, itens, proveniência, validação e evidência; falha após flush de todos os filhos desfaz o grafo e a conclusão. Exclusão desfaz filhos/tombstone/slot/lease em conjunto se houver rollback. Executor em thread liberado depois da exclusão ou nova revisão não grava qualquer filho; leitura interna também exige autorização e revisão da simulação. Esses testes não executam parser/OCR ou cálculos.
