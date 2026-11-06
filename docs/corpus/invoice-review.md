# Conferência inicial dos PDFs — 06/11/2026

Atualização atual: [revisão visual das 24 páginas](visual-review.md). CNPJ e rótulos de datas foram lidos nas doze contas; onze totais coincidem com cabeçalho/documento. Setembro tem conflito entre cabeçalho/boleto e quadro de itens; os antigos “12 resíduos zero” fechavam apenas os quadros. Outubro declara substituição de nota, e abril consumo estimado por média de 12 faturamentos. Achados antigos abaixo ficam como histórico, sem prevalecer sobre essa correção.

Estado: extração textual e candidato estruturado **local, não aprovado**. Não é homologação do parser da aplicação nem revisão humana do gabarito. Nenhum PDF ou texto bruto foi salvo por esta análise; os originais fornecidos pelo usuário foram preservados.

Conferência posterior nesta mesma data: [fatura representativa e ampliação da reconciliação](representative-review.md). O recorte inicial abaixo foi preservado como histórico; o novo rascunho local reconhece 135 linhas e fecha os 12 totais, sem aprovação visual/humana ou tributária.

Continuação ampliada: [conferência textual da série](series-review.md). As doze competências explícitas e 24 demandas de medição foram confrontadas com histórico/cobrança; há indício cativo por energia ativa TE nos doze ciclos. Surgiu uma pendência de continuidade entre maio/junho pelos ciclos candidatos. Resultados iniciais abaixo são históricos, sem aprovação visual presumida.

## Método e limites

O usuário autorizou exclusivamente `pypdf` para análise. Foi instalado `pypdf 7.0.0`, sem dependências adicionais, sem criar ambiente da aplicação, em `.local-tools/pypdf/`. A instalação restrita não encontrou o pacote; a execução aprovada fora da sandbox concluiu a instalação. O acesso à biblioteca também exigiu execução aprovada fora da sandbox. `openpyxl` já estava disponível. Não foi feito OCR, renderização, execução da aplicação ou instalação da stack do produto.

Lidos 12 PDFs textuais não criptografados, 24 páginas, 8.390.489 bytes no total. O identificador da unidade coincide nos 12 arquivos; no relatório foi substituído por aliases. A classificação impressa é A4 Azul, comercial. O nome ENEL Distribuição São Paulo foi identificado, mas CNPJ do emissor e mercado cativo não foram confirmados independentemente. Não inferir o mercado apenas da presença de TE.

A extração corrente localizou 109 linhas de demanda regular, energia ativa TE/TUSD, UFER e parcela ociosa, das quais 105 têm quantidade/preço e 4 são apenas monetárias. Não abrange todas as bandeiras, contribuições e ajustes; portanto **não é conciliação do total da fatura**. Uma linha ausente deste recorte não comprova ausência na conta.

Candidato estruturado: `.local-analysis/phase-00-invoices.json`. Guarda hash, arquivo de origem, página, campos normalizados, preços, quantidades, valores e resultados aritméticos; não guarda texto integral, endereço, nome do titular ou cópia do PDF. Identificador da unidade foi substituído por hash local, que continua sujeito à proteção de dados e não deve ser publicado. `review_status=pending` em todos os registros. Tarifa impressa foi separada de tarifa oficial homologada ainda não validada.

## Cobertura do candidato por arquivo

Aliases seguem a ordem dos nomes originais. Os meses abaixo são identificação dos arquivos, não substituem a confirmação da competência impressa. As datas da linha de classificação foram preservadas no candidato, sem atribuir competência automaticamente a partir do vencimento.

| Alias | Arquivo identificado por mês | Linhas localizadas | Linhas UFER faturadas | Diferenças quantidade × preço maiores que BRL 0.02 |
| --- | --- | --- | --- | --- |
| REAL-LOCAL-01 | agosto/2025 | 8 | 0 | 3 |
| REAL-LOCAL-02 | setembro/2025 | 8 | 0 | 2 |
| REAL-LOCAL-03 | outubro/2025 | 8 | 0 | 4 |
| REAL-LOCAL-04 | novembro/2025 | 8 | 0 | 4 |
| REAL-LOCAL-05 | dezembro/2025 | 10 | 2 | 3 |
| REAL-LOCAL-06 | janeiro/2026 | 10 | 2 | 4 |
| REAL-LOCAL-07 | fevereiro/2026 | 10 | 2 | 3 |
| REAL-LOCAL-08 | março/2026 | 10 | 2 | 4 |
| REAL-LOCAL-09 | abril/2026 | 10 | 2 | 5 |
| REAL-LOCAL-10 | maio/2026 | 10 | 2 | 2 |
| REAL-LOCAL-11 | junho/2026 | 9 | 1 | 3 |
| REAL-LOCAL-12 | julho/2026 | 8 | 0 | 1 |

Os zeros na coluna de linhas UFER significam **nenhuma linha de cobrança UFER localizada pela inspeção textual**, e não `zero_confirmed` automático. Há grandezas reativas de medição mesmo em contas sem linha de cobrança correspondente; não convertê-las em despesa. Neste recorte não foi localizada cobrança monetária de demanda reativa excedente, o que ainda exige revisão do quadro completo.

## Confronto com as planilhas e aritmética

- Para os dez arquivos de outubro/2025 a julho/2026, as quantidades e preços efetivos de demanda dos dois postos coincidem com as dez primeiras linhas correspondentes da planilha Azul. Isso vincula parte das entradas, sem aprovar o restante dos campos.
- Referência principal confirmada pelo usuário: PDFs agosto/2025–julho/2026. Segundo ele, a unidade migrou ao mercado livre em agosto/2026; por isso os dois últimos meses das planilhas foram deliberadamente excluídos do corpus PDF. A data/condições da migração ainda não foram verificadas em contrato ou faturas. Agosto/setembro de 2025 não são substitutos dos meses finais da planilha; confrontar somente os dez meses comuns.
- As duas primeiras contas contêm quatro parcelas ociosas somente monetárias. Preservar quantidade e preço como desconhecidos, conforme SPEC §7.3; não derivá-los para fazer o cadastro parecer completo.
- Em vinte parcelas ociosas com quantidade e posto relacionáveis à demanda regular, o preço impresso não coincide com preço regular × 0.82 na precisão de cinco casas. Isso contradiz usar automaticamente o desconto fixo da planilha, sem caracterizar cobrança indevida.
- Em 38 das 105 linhas quantificadas, quantidade × preço impresso difere do valor cobrado em mais de BRL 0.02. Manter pendência de reconciliação; não declarar que as contas estão erradas nem aprová-las por tolerância ampliada silenciosamente.
- Como diagnóstico de precisão, 35 dessas 38 diferenças cabem no limite `abs(quantidade) × 0.000005 + 0.005`, caso preço arredondado a cinco casas e fechamento a centavos. Isso é hipótese verificável, não autorização para alterar a tolerância inicial.
- Três diferenças ficam fora até desse diagnóstico: REAL-LOCAL-04 demanda ponta, REAL-LOCAL-08 demanda fora de ponta e REAL-LOCAL-09 demanda fora de ponta. Rever documento visualmente, preço efetivo, precisão de origem, segmentos e regra de fechamento. Os valores exatos ficam no candidato local, sem transcrição pública.

## Campos e aprovações pendentes

Confirmar CNPJ emissor, mercado, competência/ciclo/dias pelos rótulos completos, identificador de documento, titularidade informada versus extraída, situação de refaturamento, cobertura integral dos itens e total faturado. O candidato ainda não oferece o conjunto esperado aprovado exigido pela Fase 0.

Próximo passo atualizado: revisar visualmente o gabarito local de dezembro/2025 e suas exceções de preço; conferir setembro/2025 (ociosidade somente monetária; divergências tributárias documentais ficam fora da análise); resolver as três exceções especiais de precisão e completar os demais ciclos. Aprovação exige responsável identificado. Correções não devem ser gravadas nos PDFs/planilhas originais.

## Regra esclarecida pelo usuário em 06/11/2026

A simulação utiliza preço cheio com impostos incorporados, sem auditoria ou recálculo separado dos tributos. Para a demanda ociosa LEI ESTADUAL, o usuário esclareceu: `P_ociosa = P_demanda_contratada × 0,82`, na ponta, fora de ponta e demanda única. A redução de 18% é aplicada ao preço unitário, não à quantidade contratada. Preservar o preço e o valor observados no gabarito histórico; a divergência encontrada na extração candidata continua para conferência do preço-base e da precisão, sem declarar a regra informada ou o candidato homologados. Achados das colunas tributárias ficam como histórico documental e deixam de ser bloqueio da simulação com preço cheio disponível. Continuam pendentes identidade/mercado, cobertura visual, preços/componentes necessários e aprovação do gabarito.


## Tolerância monetária atual — decisão do usuário em 06/11/2026

Diferença absoluta de até BRL 0.99 por item, inclusive, aceita na reconciliação entre cálculo e valor faturado. Reavaliação em Decimal: 105 de 105 produtos quantificados e 20 de 20 parcelas ociosas pela relação de 82% passam. As quatro parcelas ociosas somente monetárias não tiveram quantidade/preço inventados. Resultados e pendências acima relativos a BRL 0.02 são históricos e ficam superados quanto ao aceite monetário. Não há pendência de impostos separados na simulação com preços cheios. Permanecem cobertura visual, identidade/mercado, campos necessários ausentes, fontes dos cenários alternativos e aprovação do gabarito. Diferenças e valores observados são preservados; os 12 residuais do total continuam zero, sem ajuste. A tolerância não altera kW, gatilho de ultrapassagem ou validação dos campos. Fronteiras ±0.99 aceitas e ±1.00 recusadas verificadas em Decimal.
