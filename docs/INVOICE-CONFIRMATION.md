# Confirmação e escolha do conjunto — sexta entrega sintética da Fase 2

Somente `synthetic / invoice-v0.3`. A prontidão abaixo se refere ao conjunto estruturado; não implementa cálculo, não homologa dados comerciais nem habilita arquivos reais. Segurança PDF das seções 5/12, adaptador específico e interface de leitura continuam pendentes. Selecionar arquivo não inicia processamento; somente “Ler fatura”.

## Conferência explícita

`POST /api/v1/simulations/{id}/invoices/{invoice_id}/confirmations` exige dono/admin ativo, sessão, Origin/CSRF e Idempotency-Key. Corpo fechado:

```json
{
  "expected_revision": 1,
  "expected_dataset_revision": 2,
  "expected_invoice_revision": 1,
  "reason_code": "synthetic_review_complete",
  "billing_coverage_confirmed": true,
  "accepted_limitations": []
}
```

Consultar `GET .../invoice-readiness` antes do comando. Retorna `pending_fields` e `limitations` por fatura. A confirmação exige conhecimento de UC, titular, endereço impresso (linha/cidade/UF), competência, datas/dias do ciclo, subgrupo/modalidade/classe e TOTAL do quadro, com proveniência presente. UC/distribuidora devem coincidir com a unidade salva. Exige tipo identificado e valor dos itens e ausência de bloqueios financeiros. CPF/CNPJ completo, número fiscal, situação formal de refaturamento, código de medidor, vencimento, CEP impresso e total a pagar não são obrigatórios. Não altera endereços da empresa ou da ligação.

`billing_coverage_confirmed=true` é uma atestação humana explícita de que conferiu o quadro inteiro no original que possui, incluindo linhas apenas monetárias. É booleano estrito; não se infere cobertura por soma coincidente. A cobertura original da extração é preservada, inclusive partial, e a atestação fica em registro próprio com política/autor/data/justificativa. Não promove automaticamente a publicação inicial para ready.

Campos estimados mantêm hipótese/método e versões concretas, exigindo aceite da limitação `estimated_data`. Ausência de mercado/demandas não vira zero: `market_unconfirmed`, `contracted_demand_incomplete` e `measured_demand_incomplete` limitam os módulos dependentes, sem bloquear diagnóstico observado de reativos. Mercado livre exige `free_market_scope`; não autoriza cálculo cativo completo. Divergência entre dias impressos e intervalo fica em `cycle_days_disagreement`, sem corrigir/reconstruir a série. `accepted_limitations` deve corresponder exatamente à lista atual da fatura, sem repetição. Isso registra ciência da insuficiência; não supre parâmetros ou garante suficiência dos módulos econômicos futuros.

Financeiro usa `observed-financial-v2`: produto com tolerância inclusiva BRL 0.99, soma assinada contra TOTAL do quadro, residual não zero pendente. Desconhecidos permanecem NULL. Preço cheio observado não recebe impostos novamente. Total a pagar permanece informativo, inclusive se sua diferença exceder a precisão da memória de validação (`payable_numeric_range`/warning); não cria parcela por diferença. A v1 histórica é preservada. Não há classificação/aceite de residual não zero nesta fatia.

Na transação de escrita: revalidar ator/autorização/revisões, conferir pendências/limitações, gravar snapshot dos IDs concretos da proveniência atual e hash do conteúdo, autoria/data/justificativa/política, marcar fatura ready e avançar dataset_revision uma vez. A revisão de conteúdo da fatura não muda na confirmação; versões de confirmação são registros imutáveis próprios. Simulation.revision não muda e tarefas independentes permanecem válidas. A revisão do conjunto na confirmação fica no snapshot e na fatura.

Correção posterior muda Invoice.revision e invalida a confirmação anterior. Alteração da unidade muda Simulation.revision, invalida confirmações/escolhas e marca faturas ready como needs_review. A prontidão sempre recalcula verificações, revisões, hash e política; não confia isoladamente em status ou recibo histórico. Publicação independente exige confirmar o novo documento, sem apagar confirmações válidas dos anteriores. O GET da fatura inclui `confirmations`, com autoria, justificativas e IDs de proveniência; não guarda PDF ou texto bruto.

## Duplicidade e refaturamento

A consulta forma grupos conexos por mesma competência, ciclos sobrepostos ou mesmo número de documento/distribuidora quando presente. Ausência do número não bloqueia; hash físico já é protegido pela admissão/publicação. A combinação de UC/distribuidora é garantida na simulação. Comparação conservadora mantém possíveis duplicatas/refaturamentos para decisão explícita; não acusa fraude ou soma documentos automaticamente. Limites/cotas acumuladas permanecem até remoção explícita de cada documento.

`POST /api/v1/simulations/{id}/invoice-selections` exige as mesmas credenciais/CSRF/Idempotency-Key. Corpo:

```json
{
  "expected_revision": 1,
  "expected_dataset_revision": 4,
  "reason_code": "synthetic_replacement_choice",
  "relationship": "replacement",
  "member_versions": {"<uuid-da-fatura-antiga>": 1, "<uuid-da-fatura-vigente>": 1},
  "included_ids": ["<uuid-da-fatura-vigente>"]
}
```

Copiar o grupo/revisões do GET atual, substituindo os UUIDs do exemplo por IDs existentes. Até doze membros, sem IDs repetidos ou de outra simulação. O pedido deve corresponder ao grupo completo atual, não a um subconjunto que omita um conflito.

- `duplicate` ou `replacement`: escolher exatamente uma versão válida. As demais permanecem consultáveis com histórico; não são incluídas no guard de cálculo. Não é necessário confirmar um documento explicitamente descartado. Exclusão da análise não libera automaticamente orçamento nem remove dados.
- `distinct_periods`: incluir todos, com datas conhecidas/positivas e sem sobreposição nem mesmo número de documento/distribuidora. Períodos que se tocam na data de leitura não são sobreposição. A mesma competência pode então conter períodos distintos confirmados, preservados separadamente.
- `complement`: registra a classificação e inclui o grupo na consulta, mas **bloqueia prontidão** com `complement_consolidation_required`. Consolidação/segmentação financeira ainda não implementada; não somar duas versões do mesmo ciclo nem inventar uma base combinada.

Escolhas guardam mapa de versões, IDs incluídos, revisão da unidade/conjunto, autor/data/justificativa e recibo. Nova fatura no grupo, correção de membro ou mudança da unidade exige escolha atualizada. Histórico de escolhas mantém associação entre sobreviventes mesmo após remoção ou separação de ciclos: remover o preferido não inclui silenciosamente uma alternativa antiga. A consulta pode apresentar grupo de um sobrevivente para reconfirmação explícita. `GET .../invoice-selections?page=1&page_size=20` retorna histórico paginado com autorização, autoria e revisões.

## Prontidão, retries e exclusão

`GET .../invoice-readiness` retorna revisões atuais, verificações financeiras em Decimal string, confirmações válidas, campos pendentes/limitações, grupos/escolhas, `included` por fatura e lacunas de competências informativas. `ready_for_calculation=true` exige unidade salva, ao menos uma fatura incluída válida/confirmada, escolhas atuais para os conflitos e nenhuma admissão queued/running ou não removida sem publicação (incluindo falha/expiração/cancelamento). Uma conta basta; lacunas e menos de doze contas não bloqueiam. Arquivos apenas selecionados localmente ainda dependem da futura interface e devem ser lidos/removidos antes do cálculo.

O serviço interno `require_ready_dataset` exige revisões de unidade/conjunto e retorna somente IDs incluídos após revalidar tudo na transação de escrita. É o ponto de integração do futuro cálculo, que também deverá conferir parâmetros/limitações de cada módulo. Nenhuma rota de cálculo ou motor foi criada nesta entrega.

Recibos de confirmação/escolha são idempotentes por ator/recurso/operação. Mesma chave/conteúdo devolve o recibo original sem reaplicar nem restaurar prontidão antiga; conteúdo diferente gera idempotency_conflict. Revisão obsoleta causa conflito, sem sobrescrita. Remoção/tombstone/ator bloqueado/acesso cruzado impedem replay pertinente. Guards não aceitam recibo como prova de prontidão atual.

Confirmação, escolha, contador, status e auditoria confirmam/desfazem juntos. Exclusão da fatura remove confirmações por CASCADE; histórico de escolhas conserva apenas IDs/revisões mínimos, sem os valores da fatura excluída, e exige reescolha dos sobreviventes. Excluir simulação remove também ambos os novos registros na transação do tombstone/cancelamento. Resultados tardios continuam cercados por TASKS, unidade e leases.

Migração aditiva `0008_invoice_confirmation`: invoice_confirmations → invoice_selections, após os pais; sem confirmação retroativa de dados existentes. Head exigido pela readiness operacional `/api/v1/ready`. Downgrade descartável perde os snapshots/escolhas e volta faturas confirmadas para needs_review; preserva faturas/filhos/publicações. Nunca usar downgrade como backup ou em operação. SQLite verificado; PostgreSQL não validado. Não instalar dependências globais ou iniciar containers.
