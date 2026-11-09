# Admissão — contrato interno sintético da Fase 2

Esta fatia implementa reserva transacional de metadados e consulta JSON de suporte. Não recebe arquivos, não executa parser/OCR e não constitui homologação de layout. Nenhum documento real pode ser recebido; `document_upload_enabled` permanece falso, inclusive para ENEL. O único par habilitado internamente é `SYNTHETIC / synthetic-v1`, com parser `synthetic-v1`; não faz parte do seed nem representa distribuidora comercial.

## Consulta e comando

`GET /api/v1/simulations/{id}/invoice-admission?layout_version=...` exige sessão e autorização de dono/admin. Retorna unidade salva, distribuidora cadastrada, layout solicitado, suporte, motivo e necessidade de contato. Unidade não salva retorna `unit_not_saved`; catálogo sem adaptador exato retorna `layout_not_supported`. Não cria tarefas nem lê arquivos. O formulário/cabeçalho visual e o pedido de contato ainda serão implementados; nenhum canal fictício foi criado.

`admit_synthetic(engine, actor_id, simulation_id, revision, key, inspection, action="read_invoice")` é exclusivamente interno. Seleção de arquivo não chama esse comando. `Inspection` é um contrato imutável de metadados: hash SHA-256, bytes, páginas, identidade observada, layout/parser e origem. Na integração documental futura, tamanho/hash/páginas devem ser medidos pelo coordenador e pelo processo isolado, nunca aceitos como declarações do cliente. O protocolo `Adapter.inspect` não possui implementação de PDF nesta entrega.

A reserva abre `BEGIN IMMEDIATE`, recarrega ator ativo, autoriza dono/admin, confere revisão e unidade salva; confronta distribuidora e UC exatas, preservando zeros à esquerda. Não tenta outro adaptador em caso de divergência. Confere suporte e limites, reserva TASKS e grava `invoice_admissions` na mesma transação. O comando retorna ID da tarefa, sem inventar uma fatura extraída.

## Limites e capacidade

MB significa 1.000.000 bytes nesta implementação. Máximos: 10 MB e 10 páginas por arquivo; 12 arquivos, 60 MB e 60 páginas acumulados por simulação. Valores desconhecidos não são zero: metadados ausentes/inválidos são recusados. Quantidade/bytes/páginas incluem reservas concluídas, com erro, expiradas ou canceladas até remoção explícita. Não há reset por requisição nem por revisão da unidade.

Capacidade inicial interna: quatro reservas ativas globais, incluindo queued/running. A quinta retorna `admission_capacity_unavailable`/503, sem gravar tarefa nem consumir orçamento. TASKS mantém uma simulação ativa por dono, inclusive quando admin admite em nome dele. `claim` de uma admissão impede outro executor de admissão global e mantém a sequência por simulação. O limite é compartilhado pelo banco; não existem filas independentes por processo web.

São limites da infraestrutura sintética, sem benchmark de RAM, CPU, pixels ou duração de lote. A fila efêmera de bytes e a reserva física de memória não estão implementadas. Não iniciar recebimento real usando apenas essas cotas.

## Repetição, cancelamento e conclusão

- Chave é armazenada como hash, única por ator; fingerprint inclui simulação, revisão e todos os metadados. Retry idêntico devolve o mesmo ID, mesmo após conclusão/expiração, sem iniciar outra leitura. Trocar conteúdo/revisão com a mesma chave causa conflito.
- Mesmo hash ativo na simulação com outra chave é duplicado. `remove_synthetic` cancela tarefa ativa, revoga lease e marca a reserva removida atomicamente, liberando orçamento. Repetir remoção é seguro; repetir a chave removida é recusado. Reenvio explícito pode usar outra chave, inclusive com o mesmo hash. Tombstone mínimo impede recriação pelo retry antigo.
- Revisar unidade cancela tarefas antigas. Excluir simulação cancela TASKS e remove reservas, faturas e filhos na mesma transação; o tombstone da simulação impede replay. Rollback restaura estados, capacidade e dados em conjunto.
- Trabalho pesado futuro ocorre fora de SQL. Usar `tasks.claim`, heartbeat e `tasks.finish` com persistência estruturada em transação nova/curta. Lease/ator/revisão/tombstone são revalidados antes do callback; falha desfaz resultado e conclusão. Remoção, revisão, bloqueio do ator, exclusão ou lease vencida impedem resultado tardio. `tasks.expire` recupera somente leases running vencidas, explicitamente.

A remoção aqui trata a **reserva sintética**, não uma extração faturável publicada. Vincular tarefa/fatura, persistir resultado tipado com proveniência sincronizada, remover grafo individual e controlar revisão do conjunto são a próxima integração. Não chamar um callback que publique faturas usando esta reserva sem implementar esse vínculo e sua remoção atômica.

## Próxima fatia e barreira para PDFs

Implementar coordenador único com fila efêmera limitada e protocolo versionado de resultado normalizado; verificar ausência de spool no framework/proxy, diretório RAM quando indispensável, isolamento sem rede, CPU/RAM/tempo/pixels, descarte em sucesso/erro/cancelamento/reinício e ausência de conteúdo na observabilidade (§5/§12). Definir recuperação de reservas queued cujo conteúdo efêmero foi perdido, sem invalidar executores vivos. Depois integrar adaptador específico homologado, extração/proveniência, revisão e UI de Ler fatura. O protocolo de inspeção sozinho não cobre extração ou prova descarte.

Testes usam exclusivamente metadados e dados sintéticos: limites nas fronteiras, concorrência da última vaga de orçamento/capacidade, retries, rollback, suporte exato, autorização/autoria, cancelamento, expiração, remoção e resultado tardio. Isso não demonstra segurança ou desempenho de PDF real.
