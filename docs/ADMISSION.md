# Admissão — contrato interno sintético da Fase 2

Esta fatia implementa reserva transacional de metadados e consulta JSON de suporte. A extensão em [COORDINATOR](COORDINATOR.md) adiciona fila em memória, liderança e subprocesso exclusivamente sintético. Não recebe documentos nem executa parser/OCR e não constitui homologação de layout. `document_upload_enabled` permanece falso, inclusive para ENEL. O único par habilitado internamente é `SYNTHETIC / synthetic-v1`, com parser `synthetic-v1`; não faz parte do seed nem representa distribuidora comercial.

## Consulta e comando

`GET /api/v1/simulations/{id}/invoice-admission?layout_version=...` exige sessão e autorização de dono/admin. Retorna unidade salva, distribuidora cadastrada, layout solicitado, suporte, motivo e necessidade de contato. Unidade não salva retorna `unit_not_saved`; catálogo sem adaptador exato retorna `layout_not_supported`. Não cria tarefas nem lê arquivos.

O cabeçalho em `/simulations/{id}/invoices` apresenta essa consulta, compartilhando `admission_context` com a API. O formulário GET aceita somente uma versão de layout (1–80 caracteres); HTMX atualiza `/simulations/{id}/invoice-admission` e, sem JavaScript, a mesma consulta recarrega a lista. Ambos exigem dono/admin e não criam reservas/tarefas nem alteram revisões. Distribuidora vem da unidade salva, sem fallback por layout informado. Mesmo `SYNTHETIC / synthetic-v1` mantém documentos reais desabilitados. Não há seletor de arquivos ou comando de leitura. O aviso de necessidade de avaliação informa que o canal de contato ainda não existe; pedido de contato continua pendente, sem canal fictício.

`admit_synthetic(engine, actor_id, simulation_id, revision, key, inspection, action="read_invoice")` é exclusivamente interno. Seleção de arquivo não chama esse comando. `Inspection` é um contrato imutável de metadados: hash SHA-256, bytes, páginas, identidade observada, layout/parser e origem. Na integração documental futura, tamanho/hash/páginas devem ser medidos pelo coordenador e pelo processo isolado, nunca aceitos como declarações do cliente. O protocolo `Adapter.inspect` não possui implementação de PDF nesta entrega.

A reserva abre `BEGIN IMMEDIATE`, recarrega ator ativo, autoriza dono/admin, confere revisão e unidade salva; confronta distribuidora e UC exatas, preservando zeros à esquerda. Não tenta outro adaptador em caso de divergência. Confere suporte e limites, reserva TASKS e grava `invoice_admissions` na mesma transação. O comando retorna ID da tarefa, sem inventar uma fatura extraída.

## Limites e capacidade

MB significa 1.000.000 bytes nesta implementação. Máximos: 10 MB e 10 páginas por arquivo; 12 arquivos, 60 MB e 60 páginas acumulados por simulação. Valores desconhecidos não são zero: metadados ausentes/inválidos são recusados. Quantidade/bytes/páginas incluem reservas concluídas, com erro, expiradas ou canceladas até remoção explícita. Não há reset por requisição nem por revisão da unidade.

Capacidade inicial interna: quatro reservas ativas globais, incluindo queued/running. A quinta retorna `admission_capacity_unavailable`/503, sem gravar tarefa nem consumir orçamento. TASKS mantém uma simulação ativa por dono, inclusive quando admin admite em nome dele. `claim` de uma admissão impede outro executor de admissão global e mantém a sequência por simulação. O limite é compartilhado pelo banco; não existem filas independentes por processo web.

São limites da infraestrutura sintética, sem benchmark de RAM, CPU ou pixels. O coordenador retém até 40 MB de fixtures, mas esse contador não inclui todas as cópias/IPC e não impõe limite físico de RAM. Timeout e deadline do lote estão descritos em [COORDINATOR](COORDINATOR.md). Não iniciar recebimento real usando apenas essas cotas.

## Repetição, cancelamento e conclusão

- Chave é armazenada como hash, única por ator; fingerprint inclui simulação, revisão e todos os metadados. Retry idêntico devolve o mesmo ID, mesmo após conclusão/expiração, sem iniciar outra leitura. Trocar conteúdo/revisão com a mesma chave causa conflito.
- Mesmo hash ativo na simulação com outra chave é duplicado. `remove_synthetic` cancela tarefa ativa, revoga lease e marca a reserva removida atomicamente, liberando orçamento. Repetir remoção é seguro; repetir a chave removida é recusado. Reenvio explícito pode usar outra chave, inclusive com o mesmo hash. Tombstone mínimo impede recriação pelo retry antigo.
- Revisar unidade cancela tarefas antigas. Excluir simulação cancela TASKS e remove reservas, faturas e filhos na mesma transação; o tombstone da simulação impede replay. Rollback restaura estados, capacidade e dados em conjunto.
- Trabalho pesado futuro ocorre fora de SQL. Usar `tasks.claim`, heartbeat e `tasks.finish` com persistência estruturada em transação nova/curta. Lease/ator/revisão/tombstone são revalidados antes do callback; falha desfaz resultado e conclusão. Remoção, revisão, bloqueio do ator, exclusão ou lease vencida impedem resultado tardio. `tasks.expire` recupera somente leases running vencidas, explicitamente.

A reserva já pode ser ligada a uma fatura sintética por invoice_publications. [INVOICE-STORAGE](INVOICE-STORAGE.md) define publicação normalizada, proveniência inicial e remoção atômica do grafo. `remove_synthetic` exige expected_dataset_revision quando houver publicação; remove grafo e vínculo, marca tombstone e libera orçamento na mesma transação. Sem publicação, mantém o cancelamento anterior. O modo Receipt técnico não publica faturas.

## Próxima fatia e barreira para PDFs

O coordenador único/fila efêmera, recuperação e resultado normalizado já existem para fixtures; não invalidam leases de tarefas ainda vivas. Próximo passo: verificar e completar as barreiras de SO/framework/proxy (§5/§12) descritas em [COORDINATOR](COORDINATOR.md), integrar adaptador homologado e completar revisão/validação/prontidão e UI de Ler fatura. Nenhum teste sintético prova descarte seguro de PDF real.

Testes usam exclusivamente metadados e dados sintéticos: limites nas fronteiras, concorrência da última vaga de orçamento/capacidade, retries, rollback, suporte exato, autorização/autoria, cancelamento, expiração, remoção e resultado tardio. Isso não demonstra segurança ou desempenho de PDF real.
