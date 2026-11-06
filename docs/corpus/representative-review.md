# Fatura representativa — roteiro e resultado da conferência

Análise de 06/11/2026, versão 0.1. **Rascunho para revisão, não aprovado.** Autor da análise documental: Codex. Revisor humano e data de aprovação: pendentes. Os dados financeiros completos permanecem locais; este documento não é fixture real anonimizada autorizada.

## Escolha e método

REAL-LOCAL-05, dezembro/2025, pertence aos dez meses comuns e reúne demanda dos dois postos, ociosidade quantificada, energia TE/TUSD, duas cobranças UFER, bandeiras e COSIP. Referência principal mantida: PDFs agosto/2025–julho/2026. A Verde continua sendo uma simulação real a conferir, sem transportar seus resultados ou tarifas para o esperado.

Leitura em memória das duas páginas com pypdf 7.0.0 já instalado, extrações normal e layout para investigar rótulos, sem OCR, renderização ou novas dependências. A página 2 tem oito linhas extraídas, de continuação de identificação/pagamento. Isso não comprova cobertura visual de imagens ou de rótulos não extraídos. A conferência integral **visual/manual continua pendente**; foi concluída a conferência documental textual do quadro financeiro reconhecido.

O quadro da representativa foi transcrito e confrontado linha a linha com o novo rascunho estruturado, sem usar totais ou fórmulas das planilhas como resultado esperado. Aritmética em Decimal, incluindo somas, subtotais, diferenças de demanda e composição da energia fora de ponta. O script é análise pontual, não implementação do adaptador da aplicação.

## Resultado por bloco

| Bloco | Evidência e decisão |
| --- | --- |
| Cabeçalho | Competência explícita dezembro/2025 e linha correspondente do histórico; classificação A4 Azul comercial. Três datas na classificação, com ciclo candidato de novembro a dezembro e 30 dias compatíveis pela diferença de datas. Associação exata aos rótulos exige conferência visual. |
| Identidade | Nome ENEL Distribuição São Paulo localizado. CNPJ candidato derivável da chave NF3e, mantido local e não confirmado independentemente. UC, titular, endereço e identificador fiscal localizados; não publicados, nem confrontados com cadastro salvo, que ainda não existe. |
| Mercado e documento | Mercado documental permanece `unknown`; contexto do usuário indica período anterior à migração informada. “SEGUNDA VIA” não prova refaturamento nem pagamento. Tensão, perdas, situação de substituição/complementação e fonte tarifária homologada continuam desconhecidas. |
| Demanda | Contratação e medidas dos dois postos identificadas. Quantidade ociosa coincide com contratado menos medido; atribuição de posto também compatível com tarifa impressa. É derivação rastreável pendente de revisão, não rótulo explícito da linha. Histórico de demanda faturada não deve substituir demanda medida. |
| Energia | Mesma quantidade nas linhas TE/TUSD de cada posto: somar custos sem duplicar kWh. Fora de ponta recomposta pelas parcelas de medição, sem reaplicar perdas desconhecidas. |
| Reativos | Duas linhas monetárias UFER identificadas. Unidade impressa do item é KWH, preservada como origem; não converter silenciosamente para kvarh. Medições reativas e DMCR são separadas de cobrança; a coluna de unidade ambígua impede uso automático de DMCR. Natureza da medição não prova natureza de toda cobrança. |
| Bandeiras e COSIP | Duas bandeiras e uma COSIP completam os dez itens do recorte anterior. Bandeiras têm zeros impressos em quantidade/preço e valor positivo: tratar como parcelas monetárias, com quantidade/preço não utilizáveis, sem confirmar consumo zero. |
| Total | Treze valores conferidos por transcrição; subtotal de faturamento, subtotal de outros e total fecham. Residual monetário zero. Tributos informados nas colunas já integram os valores: não somá-los novamente. |
| Produtos | Três exceções à tolerância inicial de BRL 0.02, em TUSD ponta, TE ponta e TUSD fora de ponta. Compatibilidade com precisão do preço impresso continua hipótese; nenhuma exceção foi aprovada ou tolerância ampliada. |
| Tributos | Base ICMS e soma dos valores ICMS dos itens coincidem com o quadro. Ociosidade tem base/ICMS zero e PIS/COFINS presente; isso não valida desconto universal de 18%. PIS/COFINS do quadro, soma dos itens e coluna TOTAL divergem entre si. Base × alíquota impressa, fechada com ROUND_HALF_UP, também não reproduz exatamente os três valores do quadro: achado documental histórico, fora da análise definida pelo usuário. Não investigar impostos separadamente como requisito do gabarito ou da simulação com preços cheios. |

Ausência de linha de ultrapassagem ou demanda reativa no quadro textual não foi promovida a `zero_confirmed`; a revisão humana deve confirmar cobertura suficiente. Residual zero não aprova extração, regra tributária, tarifa, simulação alternativa ou viabilidade contratual.

## Pacote local para o revisor

Atualização após esclarecimento do usuário: conferida a relação `preço da demanda × 0,82` em Decimal. As duas parcelas ociosas de dezembro/2025 ficam dentro da tolerância inicial de BRL 0.02 por item; diferenças nas últimas casas do preço não constituem, isoladamente, falha monetária. Na série, 17 das 20 parcelas comparáveis ficam nessa tolerância; permanecem exceções em REAL-LOCAL-03, REAL-LOCAL-06 e REAL-LOCAL-12, todas fora de ponta. As quatro parcelas somente monetárias não permitem esse teste. Isso registra a aritmética, sem aprovar leitura ou conjunto real. Tributos separados estão fora do escopo.

- `.local-analysis/representative-review.md`: quadro dos treze itens, quantidades/preços disponíveis, tributos, subtotais, diferenças exatas e roteiro de decisão.
- `.local-analysis/full-invoice-review.json`: rascunho estruturado v0.1, proveniência de página, hash dos originais, colunas tributárias e resumo da cobertura; representativa com cabeçalho, medições e estados de aprovação. Não é ainda fixture completa no formato `Field<T>`.
- `.local-analysis/reconcile_full.py`: análise pontual reproduzível com as ferramentas existentes. Não instala pacotes nem altera originais.

Todos permanecem excluídos do versionamento. O candidato anterior foi preservado. Nenhum texto bruto, imagem ou nova cópia de PDF foi gravado. O revisor deve consultar o original local, preencher responsável/data e decidir separadamente extração, cálculo e viabilidade. Aprovação e autorização de anonimização/publicação não são presumidas.

## Ampliação preliminar à série

Depois de conferir o quadro representativo, a mesma contagem e reconciliação monetária foi ampliada aos 12 PDFs: **135 linhas financeiras reconhecidas e residual zero nos 12 totais**. Foram incluídos dois padrões de rótulo de bandeira; a ausência de um padrão no primeiro passe gerava resíduos, resolvidos ao identificar o outro rótulo no documento, sem criar valores por diferença.

| Alias | Mês do arquivo | Itens financeiros reconhecidos | Residual do total |
| --- | --- | --- | --- |
| REAL-LOCAL-01 | agosto/2025 | 11 | zero |
| REAL-LOCAL-02 | setembro/2025 | 9 | zero |
| REAL-LOCAL-03 | outubro/2025 | 11 | zero |
| REAL-LOCAL-04 | novembro/2025 | 11 | zero |
| REAL-LOCAL-05 | dezembro/2025 | 13 | zero |
| REAL-LOCAL-06 | janeiro/2026 | 13 | zero |
| REAL-LOCAL-07 | fevereiro/2026 | 11 | zero |
| REAL-LOCAL-08 | março/2026 | 11 | zero |
| REAL-LOCAL-09 | abril/2026 | 11 | zero |
| REAL-LOCAL-10 | maio/2026 | 13 | zero |
| REAL-LOCAL-11 | junho/2026 | 12 | zero |
| REAL-LOCAL-12 | julho/2026 | 11 | zero |

Em setembro/2025, quadro tributário versus soma dos itens apresenta diferenças relevantes de PIS/COFINS e ICMS, inclusive na base ICMS. Não reconciliar usando o total do cabeçalho como substituto dos itens. Nas demais contas, ICMS do quadro coincide com a soma dos itens; PIS/COFINS do quadro difere da soma das linhas por centavos. A coluna TOTAL de PIS/COFINS difere da soma das linhas em todos os arquivos. Valores exatos e sinais permanecem no rascunho local; essas diferenças ficam registradas como achados documentais, fora do escopo da simulação e sem bloqueio por si só. Não foi atribuída cobrança indevida à distribuidora.

Esta ampliação é preliminar: somente a representativa recebeu o roteiro detalhado de cabeçalho/medições nesta entrega. Não afirma conferência integral das demais competências, ausência de itens fora do texto ou aprovação de seus campos. Próxima conta sugerida: setembro/2025, para conferir a ociosidade somente monetária; a divergência tributária não é bloqueio da simulação. Em seguida, revisar as três exceções especiais de preço já identificadas em novembro/2025, março/2026 e abril/2026, e completar cada gabarito antes de aprovar o conjunto.

## Regra esclarecida pelo usuário em 06/11/2026

A simulação utiliza preço cheio com impostos incorporados, sem auditoria ou recálculo separado dos tributos. Para a demanda ociosa LEI ESTADUAL, o usuário esclareceu: `P_ociosa = P_demanda_contratada × 0,82`, na ponta, fora de ponta e demanda única. A redução de 18% é aplicada ao preço unitário, não à quantidade contratada. Preservar o preço e o valor observados no gabarito histórico; a divergência encontrada na extração candidata continua para conferência do preço-base e da precisão, sem declarar a regra informada ou o candidato homologados. Achados das colunas tributárias ficam como histórico documental e deixam de ser bloqueio da simulação com preço cheio disponível. Continuam pendentes identidade/mercado, cobertura visual, preços/componentes necessários e aprovação do gabarito.


## Tolerância monetária atual — decisão do usuário em 06/11/2026

Diferença absoluta de até BRL 0.99 por item, inclusive, aceita na reconciliação entre cálculo e valor faturado. Reavaliação em Decimal: 105 de 105 produtos quantificados e 20 de 20 parcelas ociosas pela relação de 82% passam. As quatro parcelas ociosas somente monetárias não tiveram quantidade/preço inventados. Resultados e pendências acima relativos a BRL 0.02 são históricos e ficam superados quanto ao aceite monetário. Não há pendência de impostos separados na simulação com preços cheios. Permanecem cobertura visual, identidade/mercado, campos necessários ausentes, fontes dos cenários alternativos e aprovação do gabarito. Diferenças e valores observados são preservados; os 12 residuais do total continuam zero, sem ajuste. A tolerância não altera kW, gatilho de ultrapassagem ou validação dos campos. Fronteiras ±0.99 aceitas e ±1.00 recusadas verificadas em Decimal.
