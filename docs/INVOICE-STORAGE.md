# Resultado normalizado e persistência — fatia sintética da Fase 2

Esta entrega liga tarefa e fatura, grava valores/proveniência atomicamente e permite consulta/remoção JSON. Usa somente gabarito inventado; não habilita PDFs, parser/OCR ou cálculo. A quinta entrega acrescenta [revisão JSON versionada e validações observadas](INVOICE-REVIEW.md), ainda sem confirmação integral/ready. Todos os registros novos ficam `needs_review`, com validação blocking/review_required. Campo sintético confirmed não representa homologação comercial ou conferência de documento real.

## Contrato executável

`src/ecowatt/invoice_result.py` define `normalized-invoice-v1`, sem importar ORM, rotas, PDF ou OCR. Header, medições e itens usam campos com valor/estado/unidade/origem/cobertura e códigos mínimos. Schema fechado: rejeita campos extras, IDs de dono/ator, texto bruto, origem documental e versões/layouts não habilitados. Limites: três medições e 128 itens; retorno IPC limitado adicionalmente a 262.144 bytes.

Nesta versão, `source_kind` é exclusivamente synthetic, com distribuidora SYNTHETIC e parser/layout synthetic-v1. Origem de campo é user ou derived; ator/instante são fornecidos pelo servidor a partir da tarefa. PDF/OCR, região/página de origem, classificações extras, tributos detalhados e validações financeiras arbitrárias não são aceitos por esse contrato inicial. A futura integração documental precisa de versão/validações próprias, sem fingir proveniência extraída para fixtures.

O registro fechado de campos mapeia tipos, precisão, escala, enum e unidades às colunas reais. Decimais entram como strings com ponto, sem float, NaN ou expoente, e viram Decimal sem arredondamento implícito. Quantidade/demanda negativas são recusadas; créditos monetários mantêm sinal. Datas, competência, limites do fator de potência, booleanos, unidades e referências de medição são validados. Quantidade/preço desconhecidos continuam NULL, inclusive em itens apenas monetários.

Campos omitidos geram proveniência missing/NULL. Nos enums não nullable do esquema, NULL semântico é representado pelo sentinel unknown/unclassified na coluna e por estado missing/valor NULL na proveniência; isso não confirma classificação. Para campos conhecidos, valor tipado e escalar canônico são gravados juntos. Decimais da proveniência usam string sem zeros fracionários desnecessários; colunas SQLite mantêm escala fixa. JSON financeiro continua string.

`zero_confirmed` exige valor numérico zero e cobertura completa; missing/unreadable/not_applicable exigem NULL, e inaplicabilidade exige motivo. Estimated exige hipótese e dependências; derived exige regra versionada e dependências. Referências usam chaves locais fechadas; a persistência as resolve para IDs/versões concretos da mesma fatura. Referências ausentes, autorreferência, repetição e ciclos são recusados. A ordenação topológica não usa recursão sobre o payload.

Mercado fica por ciclo, sem inferência pela ausência de TE em leitura parcial. Sugestão livre por ausência exige cobertura completa e evidência de ausência TE/rede; identificação explícita ou confirmação registrada pode fornecer indício direto. Conflitos exigem estado conflicting. Indícios não sobrescrevem automaticamente o mercado confirmado. Não se calcula conta ACL completa.

## Fluxo e atomicidade

`Coordinator.run_invoice_once()` pede ao filho apenas um resultado inventado de `synthetic_invoice.py`; `run_once()` continua no modo Receipt técnico. O filho monta JSON normalizado; o pai valida o contrato e confronta hash, bytes, páginas e versão fora da transação de persistência. Seleção continua sem processamento; somente a ação read_invoice admite uma fixture. Nenhuma nova entrada pública recebe resultados ou arquivos.

`finish_normalized(engine, task_id, lease, result)` é serviço interno para resultados já obtidos. Copia/valida a entrada antes de abrir SQL. A gravação ocorre somente pelo callback de `tasks.finish`, revalidando lease, ator, unidade/revisão, tombstone e geração quando coordenada. Header observado deve coincidir com a UC salva quando conhecido; hash/tamanho/páginas/parser/layout precisam coincidir com a reserva. Não existe fallback de distribuidora.

Na mesma transação: cabeçalho, medições, itens, proveniência v1 de cada campo suportado, dependências, evidências, validação blocking, vínculo `invoice_publications`, auditoria, incremento da revisão do conjunto e TASKS finished. Flush respeita pais/filhos; falha desfaz todo o grafo e a conclusão. O serviço interno direto conserva a lease running em rollback para retry; o coordenador registra interrupção técnica separadamente e descarta seus bytes.

O vínculo tem uma tarefa por fatura, fingerprint do resultado e hash da lease de conclusão. Repetição idêntica, inclusive concorrente, retorna o mesmo ID somente com a lease original e autorização/ator/revisão ainda válidos. Resultado alterado gera idempotency_conflict; lease falsa é recusada. Publicação removida não é recriada por replay. O hash do resultado usa o JSON tipado com chaves ordenadas; mudar a representação original do resultado também é mudança de conteúdo para esse contrato.

Esses serviços continuam limitados à publicação inicial e seu replay, sem sobrescrever revisões posteriores. Correções usam exclusivamente o comando de [INVOICE-REVIEW](INVOICE-REVIEW.md): versões/proveniência/dependentes atômicos, conferência financeira observada e consulta das pendências. Não há PATCH/ready ou homologação comercial do gabarito sintético.

## Duas revisões

- `Simulation.revision` continua sendo a revisão da unidade/tombstone, usada por TASKS e pelos comandos existentes. Salvar unidade cancela tarefas antigas; excluir simulação preserva o contrato anterior de confirmação/revisão e exclusão de todo o conjunto.
- `Simulation.dataset_revision` começa em 1 e avança na publicação inicial, remoção de grafo, alteração de unidade e exclusão. Publicar uma fatura independente não cancela as outras já admitidas na mesma revisão da unidade. Não altera as duas vagas por dono.

Novas faturas usam `contract_version=invoice-v0.3`; seu dataset_revision é a revisão do conjunto na publicação e, após revisão operacional, na última alteração dessa fatura. Registros anteriores sem vínculo preservam sua versão e valor histórico, que antes representava revisão de admissão/unidade; não reinterpretar silenciosamente esse metadado. Não há cálculo antigo a migrar ou liberar automaticamente.

## API e remoção

`GET /api/v1/simulations/{id}/invoices` é paginado e ordena por ciclo início/fim, competência e ID, com datas desconhecidas depois das conhecidas. Não substitui competência por upload/vencimento. Retorna a revisão atual do conjunto. `GET .../invoices/{invoice_id}` retorna colunas tipadas e proveniência, com decimais como strings. Ambas exigem sessão e dono/admin, inclusive vínculo à simulação correta.

`DELETE .../invoices/{invoice_id}` exige Origin/CSRF, confirm boolean true, expected_revision da unidade e expected_dataset_revision atual. Remove itens antes da fatura e usa CASCADE para demais filhos/vínculo; marca a admissão removida, libera orçamento, incrementa revisão do conjunto e registra autoria na mesma transação. Conflito de conjunto retorna 409/dataset_revision_conflict. DELETE repetido do ID removido retorna 404; nunca recria dados.

`remove_synthetic` também remove um grafo já publicado, exigindo expected_dataset_revision quando houver vínculo. Para tarefa ainda sem publicação, continua cancelando/revogando lease atomicamente. Repetição da remoção da reserva é idempotente. Exclusão da simulação remove reservas, vínculos e todos os filhos junto de tombstone/slot/cancelamento; resultado tardio falha antes de criar filhos.

## Migração e restante

`0007_invoice_publications` cria o vínculo e adiciona contador positivo de conjunto às simulações existentes com default 1. Mantém dados anteriores e não inventa proveniência retroativa. Downgrade de teste perde vínculos e revisão do conjunto, preservando grafo/tarefas; novo upgrade restaura contador 1. Somente descartáveis: nunca usar esse downgrade em operação. PostgreSQL não foi validado.

As barreiras de PDF das seções 5/12 permanecem em [COORDINATOR](COORDINATOR.md): confinamento de SO, rede, CPU/RAM/pixels, descendentes órfãos, watchdog, swap/dumps e ausência de spool no framework/proxy. Depois da homologação, integrar adaptador específico e evidências do layout; em paralelo, completar revisão versionada, reconciliação, duplicidade lógica/refaturamento e prontidão. Não declarar extração real ou cálculo liberado com base nesta entrega.
