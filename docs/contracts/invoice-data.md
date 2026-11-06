# Dicionário de dados faturáveis — contrato v0.1

Proposta para implementação e revisão, ainda sem aprovação do corpus real. Fonte normativa: SPEC 3.5, §§3.1, 6, 7 e 10. Este documento define nomes e tipos de intercâmbio; não substitui as regras da SPEC nem constitui esquema SQL implementado. Fronteiras: [pipeline](pipeline.md). Evidências e dúvidas: [corpus](../corpus/README.md).

## Convenções

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
| `unit.holder_name` | string | E | Titular da ligação, distinto do dono da simulação |
| `unit.connection_address` | objeto de endereço | E | Logradouro, número ou indicação sem número, complemento opcional, bairro, município, UF, CEP; snapshot salvo antes do upload |
| `header.issuer_name`, `header.issuer_cnpj` | string | E | Identificar concessionária; CNPJ normalizado como string, não inventar identificação |
| `header.consumer_unit_id` | string | E | Deve coincidir com unidade salva; divergência exige resolução |
| `header.competence` | competência | E | Não inferir silenciosamente de vencimento/upload |
| `header.cycle_start`, `header.cycle_end` | date | E | Ordem válida; manter convenção de contagem de dias da fonte |
| `header.cycle_days` | inteiro / dia | E | Positivo, reconciliar com datas; não fixar inclusão dos extremos sem evidência |
| `header.invoice_number` | string | E | Duplicidade lógica com emissor |
| `header.subgroup` | enum A4/AS/outro/desconhecido | E | Outro/desconhecido não habilita fórmula geral |
| `header.modality` | enum blue/green/other/unknown | E | Preservar por ciclo |
| `header.market` | enum captive/free/unknown | E | Livre/desconhecido exige análise parcial/encaminhamento |
| `header.customer_class` | string | E | Identificar exceções; desconhecido explicitado |
| `header.voltage` | decimal / kV | O | Converter unidade explicitamente |
| `header.invoice_total` | decimal / BRL | E | Total faturado, sem chamar de pago |
| `header.payment_status` | enum unknown/confirmed_paid | O | Pago somente com confirmação e proveniência |
| `header.rebilling_status` | enum unknown/original/replacement/complement | E | Conflitos por competência exigem escolha explícita |
| `header.layout_version` | string | E | Adaptador/layout identificado; desconhecido mantém revisão |

Nome e endereço do titular extraídos, quando presentes, também usam Field e são confrontados com o snapshot informado; não substituir automaticamente. Cabeçalho incompleto pode ser persistido como `needs_review`, mas não apresentado como fatura pronta.

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

## Itens faturados

Cada `items[]` possui `id`, `type`, `post` (null quando não se aplica), `field_state` e proveniência de classificação; seus valores usam Field. Tipos fechados da SPEC §7.3: `active_energy_te`, `active_energy_tusd`, `regular_demand`, `idle_demand`, `overrun_demand`, `reactive_energy_excess`, `reactive_demand_excess`, `flag`, `tax`, `other`, `unclassified`.

| Campo | Tipo / unidade | Obrig. | Regra |
| --- | --- | --- | --- |
| `quantity` | decimal / unidade explícita | C | Pode faltar em linha apenas monetária |
| `quantity_unit` | enum kWh/MWh/kW/kvarh/kvar/other | C | `other` exige definição, sem uso financeiro automático |
| `regulated_rate` | decimal / BRL por unidade | C | Sem tributos, fonte e vigência; não confundir com preço efetivo |
| `effective_price` | decimal / BRL por unidade | C | Base tributária explícita: with_tax/without_tax/unknown |
| `amount` | decimal / BRL | E | Sinal preservado para créditos |
| `taxes[]` | tributo, base BRL, alíquota adimensional, valor BRL, incidência, estado | C | Cada componente com proveniência; desconhecido não equivale a isento |
| `valid_from`, `valid_to`, `segment_id` | datas / ID | C | Segmentação por mudança de tarifa/contrato |
| `reactive_nature` | enum | C | Quando identificada |
| `grouped_components` | lista TE/TUSD | C | Linha agrupada explicitamente identificada; `unclassified` até decomposição validada, sem duplicar valor |
| `measurement_ref` | ID | C | TE e TUSD podem referir a mesma medição; somar custos, não duplicar kWh |

## Validação e completude

Normalizar separadores brasileiros e unidades; verificar sinal, posto, período, limites de escopo e duplicidade (§6.3). Por linha comparável, verificar quantidade × preço com tolerância inicial de BRL 0.02, preservando precisão impressa; exceção exige motivo auditável. Quantidade/preço ausentes não são inventados para fechar a linha.

Registrar `known_components_total`, `invoice_total` e `residual` (total menos componentes conhecidos). Residual precisa de explicação ou pendência; não declarar conciliação integral por tolerância sem classificação. Conflitos de identidade, duplicatas não resolvidas e campos críticos pendentes impedem `ready`. Falta de dados exclusivos de um módulo permite fatura conferida com módulo indisponível, por exemplo demanda ausente e reativos monetários observados válidos.

Unidades extras, livre, GD, rural/sazonal, reserva, faturamento excepcional e descontos especiais recebem marcadores de escopo e motivo de análise parcial. Não aplicar a fórmula geral automaticamente.

## Reativos observados — esclarecimento de 06/11/2026

A ausência confirmada de cobrança excedente permite `zero_confirmed`, com evidência de leitura suficiente, e não cria cenário independente de surgimento de reativos. Indicadores do medidor não equivalem a itens faturados. Leitura incompleta permanece `missing`/`unreadable` conforme o caso. Quantidade ou preço ausente em cobrança observada continua desconhecido; o catálogo oficial não os inventa. Efeitos de alteração de contrato/modalidade sem dados suficientes permanecem condicionados, conforme SPEC 3.6 §8.4.