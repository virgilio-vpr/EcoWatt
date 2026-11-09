# Coordenador efêmero — execução sintética da Fase 2

O coordenador já executa fixtures em subprocesso e controla fila, liderança, timeout e recuperação. Não há endpoint de upload, parser PDF/OCR ou sandbox homologado. Recebe exclusivamente objetos `Sample`, que geram bytes inventados com formato fechado; bytes arbitrários são recusados. ENEL e todos os layouts documentais continuam desabilitados.

## Uso e ciclo interno

`Coordinator(engine)` adquire explicitamente liderança. Usar como context manager ou chamar `close()` em finally. A aplicação não o instancia no import/startup; não existe daemon ou comando operacional público nesta entrega. O uso interno foi verificado pelos testes de `tests/test_coordinator.py`, com o ambiente virtual existente e fixtures sintéticas.

`read_synthetic(actor_id, simulation_id, revision, key, Sample(...), action="read_invoice")` materializa uma fixture em memória, mede bytes/hash e usa a admissão existente. Continua exigindo ator ativo, titularidade, revisão, unidade salva e suporte exato. Seleção não materializa bytes nem cria tarefa. Retry retorna o ID anterior e não duplica a fila; uma tarefa terminal não é reexecutada. Reenvio após perda exige remoção e nova chave.

A inserção curta na fila ocorre dentro da transação da reserva; falha de capacidade desfaz TASKS e admissão. Falha da confirmação SQL remove também a entrada efêmera. Não existe atomicidade física entre RAM e SQLite: um encerramento abrupto nesse intervalo deixa metadados sem bytes; a recuperação os identifica e exige reenvio, sem fabricar conteúdo.

Limites existentes de arquivos/bytes/páginas continuam acumulados por simulação. A fila retém até quatro entradas e 40.000.000 bytes, incluindo a entrada em execução. Esse limite mede somente o buffer retido pelo coordenador: materialização, serialização, IPC, intérpretes e bibliotecas têm cópias/custos adicionais. Não constitui limite de RAM total ou benchmark.

`run_once(persist=None)` assume uma entrada, inicia um filho por `spawn` e aguarda fora de transação SQL. Uma trava local impede dois runners; TASKS limita execução global e por simulação. O filho não recebe engine/sessão, só a fixture e parâmetros técnicos. Faz apenas verificação sintética/hash. Não contém parser e não calcula dados faturáveis.

O modo Receipt usa `send_bytes`/`recv_bytes`, JSON de até 1.024 bytes, schema fechado e tipos estritos. Não desserializa pickle retornado pelo filho. `Receipt` contém hash, bytes, páginas e versão `synthetic-receipt-v1`. O coordenador confronta esses valores com a reserva. Receipt é recibo técnico, não extração nem prontidão. O callback opcional é interno e curto; não deve publicar faturas por esse modo técnico.

Extensão normalizada: `run_invoice_once()` transporta JSON de até 262.144 bytes no contrato normalized-invoice-v1 e publica somente o gabarito inventado fornecido pelo filho, com valores/proveniência/vínculo/estado atômicos. Sempre termina em needs_review. Não executa parser nem lê documento. Revisões do conjunto e remoção estão em [INVOICE-STORAGE](INVOICE-STORAGE.md). O ciclo de liderança, cancelamento e descarte permanece o mesmo nos dois modos.

## Liderança, fencing e recuperação

`0006_coordinator_lease` adiciona uma linha singleton com geração crescente, hash de token aleatório e expiração UTC. Cada reserva coordenada guarda sua geração; reservas anteriores continuam com NULL. A aquisição, avanço de geração e recuperação usam a mesma transação de escrita SQLite. Duas aquisições concorrentes produzem um líder e uma recusa `coordinator_unavailable`/503. Nunca há duas filas autorizadas independentes no mesmo banco.

TTL padrão de 60 s, configurável internamente entre 2 e 300 s. O ciclo renova liderança e lease da tarefa; `sweep()` mantém a liderança enquanto a fila aguarda execução. Não há renovação automática de um objeto abandonado. Liderança vencida não pode ser renovada: adquirir nova geração é operação distinta. Token em claro fica somente na instância, sem repr, payload de banco ou log.

Claim/heartbeat/finish de tarefa coordenada revalidam geração e validade do líder, além de ator, revisão, tombstone e lease da tarefa. O commit do recibo também revalida token, encerramento e deadline. Uma geração antiga não conclui nem renova trabalho depois de takeover. Encerrar a instância antiga não libera a liderança de sua sucessora.

Na aquisição de nova geração, queued coordenadas de gerações anteriores viram expired/content_lost. Running com lease ainda viva não é alterada; somente após sua própria expiração vira expired/lease_expired. Enquanto isso, bloqueia outro claim global. Reservas não coordenadas (geração NULL) ficam intactas. Sweep também reconhece queued da geração atual sem buffer após falha local. Nenhuma recuperação roda no startup da web.

Expiração libera capacidade ativa, mas não apaga os metadados nem o orçamento acumulado. Resultado perdido exige reenvio explícito; não buscar PDF em disco ou em banco. Falhas/expiração usam estados técnicos de TASKS, não um estado inventado de fatura pronta.

## Cancelamento, timeout e descarte verificados

Limites internos padrão: 180 s por arquivo e 600 s por lote ativo da simulação, incluindo espera na fila. Novas entradas do mesmo lote compartilham deadline. Não é benchmark nem promessa de tempo de PDF. Chamadas de sistema/SQLite/spawn podem acrescentar latência de interrupção; não foi demonstrado watchdog de SO para limites rígidos.

O ciclo verifica cancelamento, ator, revisão, leases, geração e tempo. Remoção, exclusão, revisão da unidade, bloqueio, shutdown ou perda de liderança impedem callback tardio. Timeout e falha sintética expiram a tarefa com código técnico. Falha do callback desfaz os dados e a conclusão antes de registrar interrupção em transação separada. Não registra texto de exceção do filho.

Em saída normal, erro, timeout e cancelamento controlado, o pai encerra/recolhe o filho, fecha pipes e sobrescreve/limpa seus buffers mutáveis. `close()` espera o runner encerrar e limpa a fila; é idempotente. Testes verificam buffers sem conteúdo retido e ausência de filhos novos vivos. Não se promete apagamento físico imediato: cópias temporárias do Python/IPC, swap e dumps não foram auditados. Morte abrupta do pai pode deixar filho órfão; a lease cerca a autorização de persistir, mas não é uma garantia de contenção de processo órfão pelo SO.

## Barreira antes de documentos reais

Ainda precisam ser implementados e verificados: confinamento sem rede e privilégios, CPU/RAM/pixels, controle de descendentes inclusive após morte abrupta do pai, watchdog rígido, swap/dumps, política de diretório RAM se necessário e ausência de spool no framework/proxy. O processo spawn sintético herda o ambiente de execução; separação de processo não prova isolamento de segurança.

Contrato normalizado/Decimal, proveniência inicial, vínculo tarefa/fatura, persistência/remoção e consulta JSON já existem somente para fixtures. Depois da verificação de segurança, integrar inspeção e adaptador específico homologado; completar revisão operacional versionada, validações financeiras, duplicidade lógica/refaturamento, prontidão e interface. Não habilitar upload com base apenas na existência deste coordenador. Critérios integrais da seção 15 permanecem abertos.
