# Dicionário de dados faturáveis — contrato v0.1

Contrato para implementação; o aceite mínimo local da Fase 0 não equivale à homologação comercial ou de todos os campos/layouts. Fonte normativa: SPEC 3.11, §§3.1, 6, 7, 8.6 e 10. Este documento define nomes e tipos de intercâmbio; não substitui as regras da SPEC nem constitui esquema SQL implementado. Fronteiras: [pipeline](pipeline.md). Evidências e dúvidas: [corpus](../corpus/README.md).

## Escopo mínimo

Descrição do faturamento, dados do cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas; pela atualização de 09/11/2026, incluir demandas ativas medidas por posto do quadro de medição quando necessárias à comparação/otimização. Informações administrativas/fiscais, códigos de medidor e detalhamento completo da conta continuam complementares. Colunas tributárias separadas não condicionam preço cheio observado; parâmetros tributários são condicionais à formação de preço ausente via ANEEL (§8.6). Dados C são necessários somente ao módulo que os utiliza. Não solicitar ao cliente confirmação de todos os campos opcionais.

## Convenções

Implementação inicial sintética: [INVOICE-STORAGE](../INVOICE-STORAGE.md) e `src/ecowatt/invoice_result.py` definem normalized-invoice-v1 e persistência invoice-v0.3. Trata-se de subconjunto fechado deste dicionário, com origem user/derived, proveniência inicial, dependências e estado needs_review obrigatório; não equivale à revisão, aprovação financeira ou extração documental de todo o contrato planejado. A nova dataset_revision do conjunto é distinta da revisão da unidade. Não reinterpretar registros históricos invoice-v0.2 sem vínculo de publicação.

- `decimal`: string JSON decimal canônica, ponto decimal, sem separador de milhar ou notação exponencial; conversão direta para Decimal, nunca float. Preservar precisão de origem; moeda fechada a centavos por política versionada. Valores desconhecidos são `null`, nunca zero implícito.
- `date`: `YYYY-MM-DD`; competência: `YYYY-MM`; instantes: ISO 8601 UTC. IDs são strings opacas; UC e número de documento são strings para preservar zeros à esquerda.
- Obrigatoriedade: **E** = estrutura sempre exigida (valor pode ser desconhecido, com estado explícito); **C** = exigida quando aplicável/disponível ou pelo módulo; **O** = opcional. Ausência de valor E impede confirmação do cabeçalho; dados C ausentes afetam somente os módulos dependentes, salvo inconsistência crítica da fatura.
- Todo campo faturável escalar usa `Field<T>` abaixo. Arrays podem estar vazios somente com indicação explícita da cobertura da leitura; array vazio não confirma inexistência de cobrança.
- Postos: `peak`, `off_peak`, `single`; modalidade Verde não autoriza descartar medições por posto. Grandezas de postos distintos não são intercambiáveis.

## Campo e proveniência

`Field<T> = {value, unit, state, provenance, validations}`. `unit` é `null` para texto/data/enum; valores financeiros em BRL. `validations` contém código, resultado (`pass`, `warning`, `blocking`) e referência estruturada, sem texto bruto.

| Estado | Valor e interpretação |
| --- | --- |
| `confirmed` | Valor presente, validado por consistência ou conferência humana registrada |
| `zero_confirmed` | Zero explícito, inclusive ausência de cobrança confirmada por leitura suficiente; exige evidência de cobertura |
| `not_applicable` | `null`, com motivo de inaplicabilidade |
| `missing` | `null`, não localizado |
| `unreadable` | `null`, localizado mas ilegível |
| `estimated` | Valor presente, hipótese e dependências explícitas; não equivale a conferência |

A proveniência registra `origin` (`pdf_text`, `ocr`, `user`, `derived`), `page` (inteiro a partir de 1 ou null), `region` opcional (coordenadas, unidade e referencial da página), `parser_version` (obrigatório para extração, null nos demais), rótulo mínimo opcional, `actor_id` e `recorded_at` quando houver conferência/correção. Derivados referenciam campos de entrada e regra versionada; estimativas incluem hipótese. Texto e OCR divergentes em campo crítico geram pendência, sem seleção silenciosa por confiança. Confiança OCR é metadado técnico opcional, nunca aprovação financeira.

Histórico de correção: caminho do campo, valor/estado anterior e novo, ator, instante e justificativa (obrigatória para admin). Uma correção não apaga a origem anterior. Não guardar recortes, texto bruto ou documento como evidência.

## Unidade e cabeçalho

| Caminho | Tipo / unidade | Obrig. | Restrição / uso |
| --- | --- | --- | --- |
| `unit.distributor_id` | ID | E | Catálogo; confrontar com emissor, não escolher tarifa apenas pelo nome ENEL |
| `unit.consumer_unit_id` | string | E | Normalizar preservando zeros; chave com distribuidora |
| `unit.holder_name` | string | E | Titular da ligação; nome extraído pode ser confirmado para a unidade sem alterar automaticamente o cadastro da empresa ou o dono da simulação |
| `unit.connection_address` | objeto de endereço | E | Endereço confirmado do ponto de conexão/cabine/subestação, inclusive em rua adjacente; campos de endereço e snapshot salvo antes do upload. Cópia do endereço da empresa exige confirmação |
| `header.issuer_name`, `header.issuer_cnpj` | string | O | Complemento opcional; distribuidora central já identificada por `unit.distributor_id`. CNPJ pode vir do catálogo, não precisa ser extraído/conferido em cada PDF |
| `header.consumer_unit_id` | string | E | Deve coincidir com unidade salva; divergência exige resolução |
| `header.competence` | competência | E | Não inferir silenciosamente de vencimento/upload |
| `header.cycle_start`, `header.cycle_end` | date | E | Ordem válida; manter convenção de contagem de dias da fonte |
| `header.cycle_days` | inteiro / dia | E | Positivo, reconciliar com datas; não fixar inclusão dos extremos sem evidência |
| `header.invoice_number` | string | O | Ajuda à duplicidade se disponível; ausência não bloqueia o mínimo |
| `header.subgroup` | enum A4/AS/outro/desconhecido | E | Outro/desconhecido não habilita fórmula geral |
| `header.modality` | enum blue/green/other/unknown | E | Preservar por ciclo |
| `header.market` | enum captive/free/unknown | E | Livre/desconhecido exige análise parcial/encaminhamento |
| `header.customer_class` | string | E | Identificar exceções; desconhecido explicitado |
| `header.voltage` | decimal / kV | O | Converter unidade explicitamente |
| `header.invoice_total` | decimal / BRL | E | TOTAL do quadro de faturamento, base financeira do diagnóstico; não é valor pago nem substitui o total a pagar do cabeçalho |
| `header.amount_payable` | decimal / BRL | O | Total a pagar do cabeçalho, apenas informação geral, separado do quadro |
| `header.supply_type` | string | O | Tipo de fornecimento quando disponível, por exemplo trifásico |
| `header.next_reading` | date | O | Próxima leitura quando disponível |
| `header.due_date` | date | O | Vencimento quando disponível; não substitui competência |
| `header.payment_status` | enum unknown/confirmed_paid | O | Pago somente com confirmação e proveniência |
| `header.rebilling_status` | enum unknown/original/replacement/complement | O | Complemento se localizado; não exigir auditoria de notas anteriores. Duplicatas/conflitos reais no conjunto ainda exigem resolução |
| `header.layout_version` | string | O | Metadado técnico do adaptador; não é confirmação exigida ao cliente |

Nome e endereço impressos na fatura usam `header.holder_name` e `header.printed_address` (`Field<string>` e `Field<Address>`, condicionais à disponibilidade). Preservar origem/página e valor extraído; não confundir endereço impresso, endereço da empresa e `unit.connection_address`. Dados coincidentes são mantidos após conferência; diferenças permitem confirmar/corrigir o campo pertinente com autoria e motivo estruturado, como `adjacent_street_connection_point`. Diferença de endereço explicada e confirmada para a mesma distribuidora/UC não bloqueia por si só a fatura. Divergência de UC/distribuidora permanece crítica. Cabeçalho incompleto pode ser persistido como `needs_review`, mas não apresentado como fatura pronta.

## Indícios de mercado e confirmação

`header.market` mantém `captive`, `free` ou `unknown`. A sugestão é separada em `header.market_assessment = {candidate, state, evidence_codes, coverage, provenance, confirmed_by, confirmed_at}`; `candidate` usa os mesmos valores, `state` usa `suggested`, `confirmed` ou `conflicting`, e cobertura é `complete`, `partial` ou `unknown`. Evidências estruturadas: `explicit_market_label`, `active_te_charge_present`, `active_te_charge_absent_with_complete_coverage`, `network_charge_present`, `user_confirmation`, `conflicting_evidence`. Página/região e origem seguem a proveniência do contrato; não guardar texto bruto.

Cobrança corrente de energia ativa TE sugere cativo. Ausência dessa cobrança com leitura completa e cobrança de rede/TUSD identificada sugere livre. Antes de tratar como ausência, verificar sinônimos e agrupamentos TE/TUSD do layout. UFER TE, ajustes e histórico não equivalem ao item corrente de energia ativa. Ausência em extração parcial não sugere livre: manter `unknown`. Indício isolado não confirma `header.market`; identificação explícita validada ou confirmação do cliente registra ator/data e origem. Conflito exige resolução. Registrar por ciclo, sem estender automaticamente a classificação a toda a série ou liberar cálculo cativo para mercado livre.

## Medições e contratação

`measurements[]` contém `id`, `post` e os campos abaixo; identificador e posto são obrigatórios. Cobrança monetária não substitui medição.

| Campo | Tipo / unidade | Obrig. | Dependência |
| --- | --- | --- | --- |
| `contracted_demand` | decimal / kW | C | Otimização do posto |
| `measured_active_demand` | decimal / kW | C | Otimização e comparação |
| `billed_active_demand` | decimal / kW | C | Reconciliação com faturamento |
| `active_energy` | decimal / kWh | C | Comparação de modalidade; MWh convertido com origem preservada |
| `reactive_energy` | decimal / kvarh | C | Somente quando presente, com natureza e sem inferência por FP mensal |
| `reactive_demand` | decimal / kvar ou kW | C | Preservar grandeza/unidade identificada; bloquear uso se ambígua |
| `power_factor` | decimal / adimensional | C | Quando presente; não reconstrói série horária |
| `loss_adjustment_included` | boolean | C | Estado desconhecido explícito; impedir reaplicação de perdas |
| `reactive_nature` | enum inductive/capacitive/unknown | C | Não inferir natureza ausente |

Grandezas não negativas; créditos são tratados nos itens financeiros, não convertidos em consumo negativo sem classificação. Medições reativas adicionais exigem código de grandeza e unidade explícitos antes de uso pelo motor.

Na Azul e na Verde, procurar `measured_active_demand` de `peak` e `off_peak` no quadro de medição do próprio ciclo, preservando a proveniência, a unidade e a base de perdas. Na Verde, `contracted_demand` pode existir somente em `single`, enquanto as medições existem por posto; não copiar a contratação única para os dois postos nem derivar medições a partir dela. Não somar máximos de linhas fora de ponta capacitiva/indutiva ou mapear contadores sem regra validada do layout. Ausência/ambiguidade bloqueia somente o uso dependente, com estados explícitos.

## Itens faturados

Cada `items[]` possui `id`, `type`, `post` (null quando não se aplica), `field_state` e proveniência de classificação; seus valores usam Field. Tipos fechados da SPEC §7.3: `active_energy_te`, `active_energy_tusd`, `regular_demand`, `idle_demand`, `overrun_demand`, `reactive_energy_excess`, `reactive_demand_excess`, `flag`, `tax`, `other`, `unclassified`.

| Campo | Tipo / unidade | Obrig. | Regra |
| --- | --- | --- | --- |
| `quantity` | decimal / unidade explícita | C | Pode faltar em linha apenas monetária |
| `quantity_unit` | enum kWh/MWh/kW/kvarh/kvar/other | C | `other` exige definição, sem uso financeiro automático |
| `regulated_rate` | decimal / BRL por unidade | O | Tarifa sem tributos, quando disponível; não confundir com preço cheio nem exigir para diagnóstico observado |
| `effective_price` | decimal / BRL por unidade | C | Preço cheio observado `with_tax`, sem reaplicar impostos. Preço alternativo formado via ANEEL fica no snapshot de cálculo, não substitui o item histórico; `without_tax`/`unknown` não equivalem a preço cheio |
| `amount` | decimal / BRL | E | Sinal preservado para créditos |
| `taxes[]` | tributo, base BRL, alíquota adimensional, valor BRL, incidência, estado | O | Informação documental com proveniência; pode fundamentar parâmetros de formação de preço somente se aplicável ao componente/modalidade/período e validada. Ausência/divergência não bloqueia preço cheio observado nem equivale a isenção |
| `valid_from`, `valid_to`, `segment_id` | datas / ID | C | Segmentação por mudança de tarifa/contrato |
| `reactive_nature` | enum | C | Quando identificada |
| `grouped_components` | lista TE/TUSD | C | Linha agrupada explicitamente identificada; `unclassified` até decomposição validada, sem duplicar valor |
| `measurement_ref` | ID | C | TE e TUSD podem referir a mesma medição; somar custos, não duplicar kWh |

## Validação e completude

Normalizar separadores brasileiros e unidades; verificar sinal, posto, período, limites de escopo e duplicidade (§6.3). Por linha comparável, verificar quantidade × preço: diferença absoluta de até BRL 0.99, inclusive, aceita para reconciliação monetária por autorização do usuário em 06/11/2026. Preservar precisão, produto, valor observado, diferença e versão da política; acima do limite gera pendência. Não usar a tolerância para preencher ausentes, validar identidade ou alterar limites em kW. Quantidade/preço ausentes não são inventados para fechar a linha; residual do total continua registrado separadamente.

Registrar `known_components_total`, `invoice_total` e `residual` (TOTAL do quadro menos componentes conhecidos). Residual dessa base precisa de explicação ou pendência; não declarar conciliação do quadro por tolerância sem classificação. Conflitos de identidade, duplicatas não resolvidas e campos críticos pendentes impedem `ready`. Falta de dados exclusivos de um módulo permite fatura conferida com módulo indisponível, por exemplo demanda ausente e reativos monetários observados válidos.

`header.invoice_total` representa o TOTAL do quadro de faturamento no contrato v0.2. `reconciliation.financial_table_total`, `known_components_total` e `residual` conciliam essa base. `header.amount_payable`/`reconciliation.header_total` são opcionais, separados; `payment_document_total` fica fora do mínimo. Diferença externa ao quadro é informativa e não impõe `needs_review` quando os itens e dados necessários ao módulo estão consistentes. Preservar valores e bases, sem criar parcela por diferença ou declarar o total a pagar auditado. Registros anteriores que usavam `invoice_total` como cabeçalho precisam manter sua versão de origem, sem reinterpretar silenciosamente o valor.

Aviso de consumo calculado por média exige `estimated` e regra/proveniência da estimativa, preservando quantidade/preço/valor observados. Igualdade numérica entre medição impressa e cobrança não prova medição efetiva. Premissa do usuário de cobertura de um ciclo de transição fica separada das datas/dias impressos; não reconstruir consumo, médias ou série horária automaticamente.

Unidades extras, livre, GD, rural/sazonal, reserva, faturamento excepcional e descontos especiais recebem marcadores de escopo e motivo de análise parcial. Não aplicar a fórmula geral automaticamente.

## Reativos observados — esclarecimento de 06/11/2026

A ausência confirmada de cobrança excedente permite `zero_confirmed`, com evidência de leitura suficiente, e não cria cenário independente de surgimento de reativos. Indicadores do medidor não equivalem a itens faturados. Leitura incompleta permanece `missing`/`unreadable` conforme o caso. Quantidade ou preço ausente em cobrança observada continua desconhecido; o catálogo oficial não os inventa. Efeitos de alteração de contrato/modalidade sem dados suficientes permanecem condicionados, conforme SPEC 3.6 §8.4.

## Regra esclarecida pelo usuário em 06/11/2026

A regra de 06/11/2026 preserva o preço cheio observado, sem auditoria fiscal, e `P_ociosa = P_demanda_contratada × 0,82` na ponta, fora de ponta e demanda única. A redução é aplicada ao preço, não aos kW. Atualização de 09/11/2026: preço ausente pode ser formado a partir da tarifa ANEEL com bases/incidências/alíquotas documentadas, conforme SPEC §8.6, sem alterar os itens históricos ou o aceite mínimo da Fase 0. Achados tributários continuam sem bloquear preço cheio já disponível; parâmetros faltantes bloqueiam apenas a formação dependente.

## Referência tarifária para cenários — 09/11/2026

Mercado permanece confirmado por ciclo; a execução deriva o marco de migração ACL das evidências estruturadas existentes, sem guardar texto bruto ou supor data pela simples ausência de TE. Preservar períodos e incertezas para selecionar o maior preço unitário elegível por componente: série inteira, trecho pré-ACL quando a migração ocorrer dentro dela, ou série inteira ACL para os componentes suportados. A seleção, preços ANEEL, parâmetros tributários e memória de formação pertencem ao snapshot da execução ([pipeline](pipeline.md)), não a correções das faturas. Não registrar tarifa alternativa como cobrança observada nem ampliar o escopo para energia de fornecedor ACL ausente.
