# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.9.

## Entrega atual

Fase 0 em revisão, com contratos documentais v0.1 e 26 casos sintéticos. Usuário pediu seguir a revisão recomendada antes da Fase 1; nenhuma instalação ou aplicação iniciada. As 24 páginas do corpus foram conferidas visualmente por Codex; aprovação do responsável e aceite continuam pendentes.

**Correção de reconciliação:** onze faturas fecham contra cabeçalho/documento; setembro/2025 tem diferença relevante entre total a pagar e quadro de itens. A conclusão anterior de doze resíduos zero fechava apenas os quadros e fica superada quanto à conciliação integral. Valores exatos e diferenças ficam no pacote local, sem parcela inventada ou tolerância global aplicada.

## Decisões preservadas

- Referência principal: PDFs agosto/2025–julho/2026. Planilhas comparadas somente nos dez meses comuns, outubro/2025–julho/2026. Verde é referência de estrutura, com demanda copiada da Azul, sem gabarito financeiro.
- Preço cheio com impostos incorporados; sem auditoria separada de impostos. Ociosidade LEI ESTADUAL = preço da demanda contratada × 0,82, para ponta/fora de ponta/única. Até BRL 0.99 inclusive por item: 105 produtos e 20 parcelas ociosas quantificadas passam. Quatro parcelas ociosas de agosto/setembro continuam somente monetárias.
- Não transportar fator 3 de ultrapassagem da planilha. Ausência observada de cobrança reativa não cria cenário independente de surgimento ou garante ausência futura.
- Cadastro da empresa, endereço impresso e ponto de conexão/cabine são distintos; dados coincidentes podem ser mantidos, divergentes confirmados/corrigidos com proveniência. Não sobrescrever cadastro automaticamente.
- Mercado é sugerido cativo pelos itens correntes TE/TUSD da série e pelo contexto informado; não confirmado automaticamente. Livre permanece fora do cálculo cativo completo.

## Revisão visual e achados

- `docs/corpus/visual-review.md`: CNPJ da distribuidora lido em cada um dos doze cabeçalhos, inclusive agosto/setembro. Correspondência oficial Enel conferida anteriormente; não comprova autenticidade dos PDFs. Nome/endereço impressos e UC conferidos, mantidos somente no rascunho local; ponto de conexão depende do cliente.
- Rótulos de leitura anterior/atual, dias e próxima leitura conferidos: deixam de ser associação meramente candidata, sem alteração das datas. Cobertura do quadro de cobrança e página 2 revista; sem novos itens financeiros na página 2. Ausências observadas registradas com cobertura, separadas de medição DMCR.
- Setembro: cabeçalho e documento coincidem entre si, mas diferem do quadro e dos componentes. Pergunta ao usuário enviada, sem resposta presumida; `needs_review` mantido.
- Outubro declara substituição de nota anterior; marcar `replacement`, evitar dupla contagem se original for fornecido. SEGUNDA VIA isoladamente não determina refaturamento.
- Abril declara consumo pela média aritmética dos últimos 12 faturamentos. Preservar observado como estimado; igualdade entre tabela/cobrança não prova medição real.
- Mudança de calendário antes da migração ao ML em agosto/2026 confirmada pelo usuário que acompanhou a transição. Junho mantém 30 dias impressos, separadamente da premissa de ~60 dias e possível média de dois meses informada pelo usuário. Dois registros MAI/26 no histórico preservados. Sem consumo dobrado, interpolado ou anualização medida contínua homologada.

## Evidências locais e verificações

`.local-analysis/visual-review.json` é o rascunho atual para total/residual, leitura de CNPJ/datas e exceções. Candidatos anteriores preservados como histórico. Doze fichas atualizadas em `.local-analysis/review-package/`, com `REVIEW-RESULT.md`, manifesto e aprovação do usuário pendente. Arquivos reais, ferramentas e dados pessoais fora do envio.

Renderização nativa Windows.Data.Pdf por PowerShell 5.1, em streams de memória; sem nova dependência, imagem em disco ou texto bruto persistido. Transporte em blocos e comprimento conferido antes de inspecionar; tentativas incompletas descartadas. Releitura em memória com pypdf existente dos totais nos doze PDFs; asserções de onze reconciliações e um conflito, CNPJ por documento, preservação dos quatro itens monetários e 30 dias impressos de junho. Nenhum teste de aplicação ou OCR.

SPEC §7 e dicionário reforçados para distinguir totais de cabeçalho/documento/quadro/soma, e consumo estimado versus medição; caso sintético S26. Links, codificação e lista explícita de dez documentos públicos conferidos antes do commit. Nenhum aceite marcado. Tarifas oficiais, vigências e regra regulatória consolidada continuam sem homologação comercial.

## Próximo passo antes da Fase 1

Esclarecer o conflito de setembro; revisar/aceitar desconhecidos e limitações de abril/junho, confirmar ponto de conexão e mercado, registrar responsável/data de aprovação. Autorização/procedimento de anonimização de fixtures reais e fontes/preços necessários aos cenários continuam pendentes. Não iniciar Fase 1 nesta entrega.

## Arquivos e commit

Novo: `docs/corpus/visual-review.md`. Alterados: `EcoWatt_PROJECT_SPEC.md`, `docs/STATUS.md`, `docs/contracts/invoice-data.md`, `docs/corpus/README.md`, `docs/corpus/series-review.md`, `docs/corpus/invoice-review.md`, `docs/corpus/representative-review.md`, `docs/corpus/regulatory-review.md`, `docs/corpus/synthetic-cases.md`. Removidos: nenhum. Materiais reais e scripts locais excluídos.

Commit: `docs: revisa visualmente corpus e corrige conciliacao dos totais`. Consultar histórico remoto para o SHA; este status integra o próprio commit.
