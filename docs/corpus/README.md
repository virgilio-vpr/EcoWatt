# Corpus e homologação — inventário e conferência em 06/11/2026

**Escopo atual — decisão do usuário em 06/11/2026:** somente faturamento, cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas (SPEC 3.10; contrato mínimo v0.2). Não exigir cadastro completo ou auditoria fiscal/bancária. Para o diagnóstico, conciliar itens com TOTAL do quadro; diferença para cabeçalho/boleto é informativa e não bloqueia os módulos com entradas suficientes. A investigação ampla abaixo fica como histórico. Dados atuais do mínimo em `.local-analysis/minimum-billing-review.json` e resumo em `.local-analysis/review-package/MINIMUM-REVIEW.md`; nenhum dado real é enviado.

Atualização atual: [revisão visual das 24 páginas](visual-review.md). CNPJ e rótulos de datas foram lidos nas doze contas; onze totais coincidem com cabeçalho/documento. Setembro tem conflito entre cabeçalho/boleto e quadro de itens; os antigos “12 resíduos zero” fechavam apenas os quadros. Outubro declara substituição de nota, e abril consumo estimado por média de 12 faturamentos. Achados antigos abaixo ficam como histórico, sem prevalecer sobre essa correção.

## Materiais efetivamente disponíveis

Materiais indicados pelo usuário para continuidade da Fase 0 e confirmados localmente:

| Local | Inventário | Conferência realizada |
| --- | --- | --- |
| `docs/faturas/` | 12 PDFs, nomes de agosto/2025 a julho/2026 | SHA-256 distintos; sem duplicatas binárias |
| `docs/planilhas/Analise_Faturas_Energia_Preenchida_Azul.xlsx` | 5 abas, 769 células com fórmulas | Estrutura XLSX inspecionada em memória; nenhum vínculo externo de workbook identificado |
| `docs/planilhas/Analise_Faturas_Energia_Preenchida_Verde.xlsx` | 3 abas, 432 células com fórmulas | Estrutura XLSX inspecionada em memória; nenhum vínculo externo de workbook identificado |

As doze competências foram agora conferidas no campo explícito e no histórico de cada fatura, coincidindo com os nomes dos arquivos; datas do ciclo continuam candidatas por associação dos rótulos pendente de conferência visual. Ver [conferência ampliada da série](series-review.md). Hashes diferentes não excluem duplicatas lógicas. Conferência textual inicial realizada em 06/11/2026: unidade coincidente, classificação A4 Azul e nome ENEL Distribuição São Paulo identificados. Mercado, CNPJ emissor, competência pelos rótulos completos e gabarito integral ainda pendentes. Demanda e preço efetivo dos dois postos coincidem nos dez meses sobrepostos com a planilha Azul. A presença de fórmulas não valida sua regra, resultado ou relação com a série. Não houve gravação de texto bruto. Em 06/11/2026 o usuário autorizou somente pypdf para análise; versão 7.0.0 instalada em pasta local de ferramentas, sem ambiente da aplicação.

A indicação das pastas permite a análise local solicitada; não equivale à aprovação do gabarito nem à autorização para publicar originais ou incorporar dados pessoais a fixtures versionadas. Anonimização e condições do acervo de homologação permanecem a definir. Os originais ficam locais e fora da lista de envio manual ao GitHub.

A inspeção anterior havia encontrado somente documentação; este inventário a substitui quanto à disponibilidade desses materiais. CSV tarifário, CUSD e gabarito independente aprovado continuam não identificados. As imagens descritas na SPEC §11.3 não são resultados homologados. `debug.log` continua sendo artefato local, fora do envio.

Disponível nesta entrega: [casos sintéticos](synthetic-cases.md), definidos a partir dos contratos e da fórmula interna da SPEC §8.2. Não representam ENEL, tarifas vigentes, leitura de PDF ou evidência regulatória independente.


Referência regulatória recebida: `docs/ANEEL/REN 1000.pdf`, 3.919.570 bytes, SHA-256 `482B1BC8E1CD199629BF6F85C52B0CC41536A142FBAB61A22DA29C3371126BA3`. Presença, tamanho e hash conferidos em 05/11/2026. Em 06/11/2026 foi feita leitura dirigida: 183 páginas, metadados de reprodução Leis.org e redações alteradas. Origem oficial, consolidação e aplicabilidade por ciclo ainda não aprovadas. O nome do arquivo não comprova versão vigente. Manter como material local nesta entrega; nenhuma regra ou tarifa foi homologada a partir dele.

## Pacote necessário para homologação

| Material a obter | Evidência esperada | Uso / bloqueio atual |
| --- | --- | --- |
| Série real ENEL SP A4 Azul autorizada, idealmente 12 competências consecutivas | PDFs textuais/digitalizados com autorização e processo de anonimização separado do fluxo de clientes; CNPJ emissor, UC, mercado e layout conferidos | Homologação do primeiro adaptador pendente |
| Gabarito manual por fatura | Todos os campos do dicionário, linhas, postos, estados de ausência, unidades e proveniência; revisor/data; totais/residuais conferidos | Não há conjunto real esperado aprovado |
| Planilha original e fórmulas | Células/fórmulas e entradas estruturadas, preços, tributos e perdas por ciclo, resultados por componente | Comparação financeira com planilha pendente |
| Tarifas e atos oficiais por vigência | Fonte oficial, arquivo/versão, distribuidora/CNPJ, subgrupo, modalidade e base de preço | Nenhuma tarifa real fixada nesta fase |
| CUSD, aditivos e histórico contratual | Demandas por posto, restrições e datas de alteração, exceções e perdas | Recomendação de implantação condicionada |
| Preços cheios e perdas | Preços efetivos próprios por componente e vigência; perdas quando necessárias | Impostos separados fora da análise; falta de preço cheio bloqueia somente o cálculo dependente |
| Verde/AS e novos layouts | Fixtures próprias e tarifas correspondentes; demandas por posto quando necessárias | Estar no escopo não homologa esses adaptadores |
| Reativos intervalares | Medição/arquivo da distribuidora e regra aplicável | Não inferir correção completa de FP mensal |
| Dados comerciais/privacidade/hospedagem | Responsável, canal, finalidades, retenção, provedor e isolamento | Publicação e operação comercial pendentes |

O corpus autorizado de homologação é um acervo separado, com acesso e retenção definidos, fora da ingestão do cliente. Autorização para processar uma conta no produto não autoriza incorporá-la ao corpus. Não incluir originais ou dados pessoais reais neste repositório por padrão.

## Registro de evidência futura

Cada caso real deverá ter ID, origem/autorização, procedimento de anonimização, concessionária/CNPJ confirmado, mercado, layout, ciclo, versão do gabarito, autor/revisor e data. Manter entrada normalizada e esperado independente por campo/módulo, tolerância justificada, divergências por competência/componente e decisão de aprovação. Separar extração correta, cálculo correto e viabilidade contratual; aprovação de um eixo não aprova os demais.

Fluxo de homologação: receber autorização → anonimizar em processo controlado → conferir manualmente os campos → fixar fontes/regras → conferir resultados independentes → executar comparação do parser/motor → registrar divergências → aprovação explícita pelo responsável. Não marcar aceite por existência de fixture.

## Dúvidas e dependências abertas

| ID | Pergunta / responsável esperado | Trabalho independente permitido |
| --- | --- | --- |
| D01 | Cliente-piloto: confirmar condições de uso/anonimização da série recebida e indicar quem aprova o gabarito? | Modelos e pipeline com casos sintéticos |
| D02 | Especialista/piloto: qual CNPJ/layout real e quais exceções contratuais? | Adaptadores com interface definida, sem selo de homologação |
| D03 | Especialista: quais preços cheios por componente, perdas e política de arredondamento por vigência? Impostos separados fora da análise por decisão do usuário. | Nenhum preço ausente igual a zero; ociosidade = preço da demanda contratada × 0,82, conforme regra informada pelo usuário |
| D04 | Finalidade/período esclarecidos: Verde é referência de estrutura/apresentação, com demanda copiada da Azul e sem valor de gabarito econômico; referência principal PDF agosto/2025–julho/2026, anterior à migração ao mercado livre informada para agosto/2026. Para um cenário Verde calculado, obter entradas e preços próprios; não homologar os números exemplificativos dessa planilha. | Relatório demonstrativo sem reproduzir resultados como aprovados |
| D05 | Piloto/distribuidora: existem dados por posto na Verde e intervalares de reativos? | Módulos parciais com motivos explícitos |
| D06 | Responsável do produto: aprovar nomes/tipos deste contrato e conjuntos reais esperados? | Implementar proposta versionada, registrar ajustes antes de migrar dados reais |
| D07 | Especialista: convenção de dias do ciclo, grandezas reativas ambíguas e agrupamentos TE/TUSD do layout? | Preservar unidade/origem; bloquear uso ambíguo |
| D08 | Responsável comercial/privacidade: confirmar retenção e tratamento de vínculos de orçamento na exclusão? | Definir autorização/cancelamento; não lançar operação comercial |

Em 06/11/2026 foram consultados o catálogo oficial e referências indexadas da REN; o texto compilado continuou retornando 403. Nenhum preço tarifário foi importado ou aprovado. Ver [conferência regulatória](regulatory-review.md). A vigência aplicável por ciclo continua pendente.

## Evidências da continuação da Fase 0

- [Planilhas: fórmulas, caches e divergências](workbook-review.md).
- [Faturas: cobertura e pendências do candidato local](invoice-review.md).
- [Série: competências, medições, continuidade e cruzamento com Verde](series-review.md).
- [Regulamentação e limites das fontes](regulatory-review.md).

O candidato com dados reais normalizados fica exclusivamente em `.local-analysis/phase-00-invoices.json`, com revisão pendente; não é fixture pública nem gabarito aprovado. Esclarecimento atual do usuário: Verde é somente referência de estrutura para a modalidade; a demanda foi copiada da Azul e não representa entrada válida de um cenário Verde real. PDFs agosto/2025–julho/2026 continuam como referência principal. A diferença é intencional para excluir agosto/setembro de 2026 após a migração ao mercado livre informada pelo usuário; essa migração ainda não foi conferida documentalmente. Comparar com as planilhas apenas outubro/2025–julho/2026; não misturar regimes ou deslocar meses. Detalhes em workbook-review.md. D01/D02/D03/D04/D06/D07 continuam parcialmente abertas apesar do avanço de leitura. Nenhum item composto da Fase 0 foi marcado.
## Avanço do gabarito em 06/11/2026

Dezembro/2025 recebeu conferência textual do quadro completo e rascunho local para revisão. A ampliação preliminar reconheceu 135 linhas financeiras, incluindo bandeiras e COSIP, com residual monetário zero nos 12 totais. Divergências tributárias e de precisão continuam abertas; setembro/2025 tem diferenças relevantes entre quadro tributário e itens. Gabarito detalhado e JSON ficam em `.local-analysis/`, sem publicação. Não houve revisão visual, aprovação humana, fixture real autorizada ou homologação da Verde. Ver [fatura representativa](representative-review.md) para limites e próximo passo. A competência de dezembro/2025 foi conferida pelo campo explícito e histórico; as demais ainda exigem confirmação individual do cabeçalho, atualizando o limite do inventário inicial acima.

## Regra esclarecida pelo usuário em 06/11/2026

A simulação utiliza preço cheio com impostos incorporados, sem auditoria ou recálculo separado dos tributos. Para a demanda ociosa LEI ESTADUAL, o usuário esclareceu: `P_ociosa = P_demanda_contratada × 0,82`, na ponta, fora de ponta e demanda única. A redução de 18% é aplicada ao preço unitário, não à quantidade contratada. Preservar o preço e o valor observados no gabarito histórico; a divergência encontrada na extração candidata continua para conferência do preço-base e da precisão, sem declarar a regra informada ou o candidato homologados. Achados das colunas tributárias ficam como histórico documental e deixam de ser bloqueio da simulação com preço cheio disponível. Continuam pendentes identidade/mercado, cobertura visual, preços/componentes necessários e aprovação do gabarito.


## Tolerância monetária atual — decisão do usuário em 06/11/2026

Diferença absoluta de até BRL 0.99 por item, inclusive, aceita na reconciliação entre cálculo e valor faturado. Reavaliação em Decimal: 105 de 105 produtos quantificados e 20 de 20 parcelas ociosas pela relação de 82% passam. As quatro parcelas ociosas somente monetárias não tiveram quantidade/preço inventados. Resultados e pendências acima relativos a BRL 0.02 são históricos e ficam superados quanto ao aceite monetário. Não há pendência de impostos separados na simulação com preços cheios. Permanecem cobertura visual, identidade/mercado, campos necessários ausentes, fontes dos cenários alternativos e aprovação do gabarito. Diferenças e valores observados são preservados; os 12 residuais do total continuam zero, sem ajuste. A tolerância não altera kW, gatilho de ultrapassagem ou validação dos campos. Fronteiras ±0.99 aceitas e ±1.00 recusadas verificadas em Decimal.

## Pacote local para revisão por fatura

Consolidadas doze fichas em `.local-analysis/review-package/` (índice e manifesto locais), sem envio de dados reais. Incluem medições, itens, totais, diferenças e decisões pendentes. Correspondência cadastral entre nome Enel SP e CNPJ derivado de dez chaves conferida na fonte oficial da distribuidora; agosto/setembro seguem sem CNPJ extraído. A confirmação da identidade cadastral não aprova as faturas nem preenche campos ausentes. Junho mantém separados os 30 dias impressos e a premissa de transição aproximada de 60 dias. Detalhes no [relatório da série](series-review.md).

Hipótese de setembro conferida a pedido do usuário: forte compatibilidade numérica da diferença para o total a pagar com bandeira vermelha patamar 2 não discriminada. Fonte Enel para o mês e MME para BRL 78.77/MWh; memória Decimal local em `.local-analysis/september-flag-check.json`, com desvio de poucos centavos na estimativa de preço cheio por proporção da própria conta. Não adicionar item observado ou converter a hipótese em gabarito aprovado. Fontes e método em [referências do corpus](regulatory-review.md).
