# Casos sintéticos — v0.1

**Todos os dados abaixo são inventados para desenvolvimento, sem correspondência com cliente, conta ou tarifa real. Não homologados.** Não são PDFs e não testam OCR. Esperados calculados diretamente da SPEC §§7.4 e 8.2, sem tributos, perdas ou promessa comercial. Política demonstrativa: Decimal, arredondamento de fechamento a centavos; exemplos evitam empate de arredondamento. Não escolher política real por estes exemplos.

## S01 — conjunto estruturado de uma fatura

Perfil fictício A: dono `synthetic-owner-a`, empresa `synthetic-company-a`; autor igual ao dono. Simulação `synthetic-sim-a`, revisão 1. Unidade: distribuidora `synthetic-distributor`, UC `000001`, titular `Empresa Sintética A`, endereço `Rua Fictícia, 1, Bairro Exemplo, São Paulo, SP, 00000000` (CEP deliberadamente fictício, não cadastro operacional).

Cabeçalho: emissor `Distribuidora Sintética`, CNPJ `missing/null` (não inventar CNPJ válido), documento `SYN-001`, competência `2026-01`, ciclo `2026-01-01` a `2026-01-31`, 31 dias por convenção inclusiva **deste caso**, A4, Azul, cativo, classe industrial sintética, tensão `not_applicable/null`, total `2600.00` BRL, pagamento desconhecido, refaturamento original, layout `synthetic-v1`.

Campos declarados têm origem `user`, autor `synthetic-author`, instante `2026-11-05T12:00:00Z`, página/região/parser null e marca `source_kind=synthetic`; estado `confirmed` significa apenas entrada conferida deste exemplo, sem validação real. CNPJ missing é complemento opcional e não impede `ready` no escopo mínimo; a distribuidora sintética está identificada no cadastro. Valores derivados usam origem derived com referência à fórmula. Campo sem dado usa missing; não criar zeros para grandezas reativas ausentes.

| Posto | Contratada kW | Medida kW | Faturada kW | Energia kWh | Perdas incluídas |
| --- | --- | --- | --- | --- | --- |
| peak | 100 | 80 | 100 | missing | missing |
| off_peak | 100 | 120 | 120 | missing | missing |

| Item | Posto | Quantidade kW | Preço BRL/kW | Valor BRL |
| --- | --- | --- | --- | --- |
| regular_demand | peak | 100 | 10.00 | 1000.00 |
| regular_demand | off_peak | 120 | 10.00 | 1200.00 |
| overrun_demand | off_peak | 20 | 20.00 | 400.00 |

Itens sem tributos **por definição matemática do cenário**, não por inferência de ausência de linha. Não há energia TE/TUSD neste recorte; não representa uma conta real completa. Soma dos itens `2600.00`, residual `0.00`; isso confere a aritmética do recorte e não habilita comparação de modalidade sem energia/preços correspondentes. Demanda ociosa física peak `20` kW; não valorar com tributos desconhecidos. Esperado: recorte de demanda pode ficar conferido com distribuidora/UC e demais campos mínimos validados, sem bloqueio por CNPJ ausente; comparação de modalidade indisponível por falta de energia/preços. O recorte de demanda pode ser usado isoladamente em teste unitário sintético da fórmula, sem burlar admissão do pipeline.

## Casos isolados e respectivos esperados

Cada linha é um caso independente; valores monetários em BRL, demanda em kW. T=`10.00` BRL/kW é tarifa **sintética** sem tributos. Não anualizar estes casos.

| ID | Entrada | Esperado independente |
| --- | --- | --- |
| S02 | Dc=100, Dm=80 | Regular 1000.00; adicional 0.00; total 1000.00; ociosidade física 20 |
| S03 | Dc=100, Dm=105 | Regular 1050.00; adicional 0.00; total 1050.00; gatilho estrito não atingido |
| S04 | Dc=100, Dm=120 | Regular 1200.00; adicional (120−100)×2×10=400.00; total 1600.00 |
| S05 | Dc=100, Dm=105.01 | Regular 1050.10; adicional 100.20; total 1150.30; não cobrar apenas excesso sobre 105 |
| S06 | Quantidade 2 MWh | Normalizar para 2000 kWh; manter unidade/origem da conversão |
| S07 | Quantidade 100 kWh, preço 0.50, valor 50.02 | Diferença 0.02, dentro da tolerância atual de 0.99; registrar verificação |
| S08 | Mesmos dados, valor 50.03 | Diferença 0.03, dentro da tolerância atual de 0.99; preservar diferença, sem pendência monetária por esse item |
| S09 | Linha crédito other, amount=-25.00 | Preservar sinal; não converter em consumo negativo |
| S10 | Quantidade/preço missing, idle_demand amount=30.00 | Guardar cobrança observada; não reconstruir quantidade ou tarifa |
| S11 | Dc missing; reativos monetários confirmed=40.00 | Otimização indisponível; observado reativo 40.00, economia evitável desconhecida |
| S12 | Reativos missing versus zero_confirmed=0.00 | Primeiro desconhecido; segundo ausência confirmada com cobertura suficiente; resultados distintos |
| S13 | TE e TUSD ligados à mesma medição de 1000 kWh | Energia 1000 kWh, não 2000; custos das duas linhas podem ser somados |
| S14 | Total 120.00, componentes conhecidos 100.00 | Residual 20.00 explicitado, sem fechar total só com itens analisados |
| S15 | Mesmo hash; ou emissor+documento iguais | Duplicidade bloqueia inclusão redundante; retry idempotente não cria cópia |
| S16 | Mesma UC/competência, documentos diferentes | Revisão para refaturamento/complemento/período; não somar automaticamente |
| S17 | Tarifa alternativa missing | Comparação indisponível; nenhum custo alternativo zero |
| S18 | Mesmo consumo/custos comparáveis atual 100.00, alternativa 110.00 | Diferença bruta -10.00 preservada; manter cenário atual, economia exibida 0.00 |
| S19 | Uma fatura conferida e nenhuma pendência | Admissão possível; cobertura insuficiente de outros módulos continua explícita |
| S20 | Uma fatura conferida e outra com erro/selecionada não lida | Simular bloqueado até resolver/remover; backend revalida admitidos e UI trata seleção local |

S02–S05 usam max(Dm,Dc)×T e adicional somente quando Dm>1.05×Dc. S07–S08 testam reconciliação aritmética, não suficiência da linha para homologação. Casos de concorrência, acesso e exclusão estão no [contrato de acesso](../contracts/access.md); ainda são esperados documentais, sem execução de aplicação.

## Forma de futura execução

Converter estes casos em fixtures tipadas quando o modelo existir, mantendo IDs e source_kind. Separar testes de normalização, validação, cálculo e integração. Acrescentar casos reais apenas com autorização e gabarito aprovado; nunca renomear synthetic como homologated. Comparar resultados por campo, ciclo e componente, não apenas total agregado.

## Casos adicionais após inspeção das planilhas — 06/11/2026

S21–S25 também são inteiramente sintéticos. Não contêm dados da unidade real nem homologam tributos.

| ID | Entrada / situação | Esperado |
| --- | --- | --- |
| S21 | Dc=100, Dm=120, T=10; conferir cenário atual e alternativo com o mesmo contrato | Ambos: regular 1200.00, adicional 400.00, total 1600.00. Um multiplicador 3 produziria adicional 600.00 e deve ser detectado mesmo que o exemplo original da planilha não acione ultrapassagem. |
| S22 | Leitura completa confirma ausência de cobrança reativa excedente | Zero confirmado para cobrança observada, sem cenário independente de surgimento; não buscar tarifa para fabricar oportunidade. Efeitos futuros de mudança contratual sem dados são limitação separada. |
| S23 | Demandas medidas ponta=80 e fora=120 kW, bases/períodos compatíveis | Para cenário Verde derivado desse perfil, demanda medida única=120 kW; não copiar apenas ponta=80. |
| S24 | Quantidade=1000, preço impresso=0.12345, valor=123.48 | Produto=123.45000, diferença=0.03; aceita pela tolerância atual de 0.99, embora a hipótese de precisão do preço (limite 0.01000) não explique a diferença. Aceite monetário não prova a origem do desvio. |
| S25 | Dois componentes sintéticos de BRL 0.014 cada | Fechar cada componente por ROUND_HALF_UP e somar=0.02; somar antes de fechar=0.03. Exigir política explícita; o experimento não fixa a política da distribuidora. |
## Fronteira da tolerância autorizada em 06/11/2026

Mesma quantidade 100 e preço 0.50: valor 50.99 tem diferença 0.99 e passa; valor 51.00 tem diferença 1.00 e gera pendência. Valor 49.01 também passa por diferença absoluta 0.99; valor 49.00 gera pendência de 1.00. Não usar tolerância por item para ocultar residual do total, criar valores ausentes ou alterar gatilho de ultrapassagem.


## S26 — Cabeçalho e quadro com totais conflitantes

Caso inteiramente sintético: cabeçalho e documento de cobrança indicam BRL 120.00; quadro TOTAL e soma dos itens indicam BRL 100.00. Esperado no escopo mínimo atual: base do diagnóstico = TOTAL do quadro BRL 100.00; itens BRL 100.00; residual faturável zero. Guardar total a pagar BRL 120.00, se disponível, com diferença informativa BRL 20.00. A diferença externa ao quadro não impõe `needs_review` ou bloqueia demanda/reativos com entradas consistentes. Não criar cobrança de BRL 20.00 nem declarar o total a pagar auditado.
