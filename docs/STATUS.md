# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.8.

## Entrega atual

Fase 0 em andamento; contratos documentais v0.1 e 25 casos sintéticos, sem aplicação implementada. Gabarito textual local de dezembro/2025 preparado para revisão e rascunho ampliado das doze competências, cabeçalhos e medições; reconciliação preliminar dos 12 PDFs com 135 itens financeiros e residual zero nos 12 totais. Aceite e gabarito real continuam pendentes, sem aprovação presumida.

## Decisões preservadas

- Referência principal: PDFs agosto/2025–julho/2026. Planilhas comparadas somente nos dez meses comuns, outubro/2025–julho/2026. Verde é somente referência de estrutura/apresentação para a modalidade, com demanda copiada da Azul e reconhecida pelo usuário como inadequada para um cenário Verde real. Não usar seus resultados como gabarito econômico. Migração ao mercado livre em agosto/2026 informada pelo usuário, ainda sem conferência documental de data/condições.
- Preço cheio com impostos incorporados; impostos separados fora da análise. Demanda ociosa LEI ESTADUAL: preço da demanda contratada × 0,82, na ponta, fora de ponta e demanda única.
- Tolerância monetária por item até BRL 0.99 inclusive, autorizada pelo usuário. Em Decimal, 105/105 produtos quantificados e 20/20 parcelas ociosas comparáveis passam; quatro parcelas somente monetárias não tiveram quantidade/preço inventados. Diferenças e residuais preservados. Fronteiras ±0.99/±1.00 verificadas anteriormente.
- Fator 3 de ultrapassagem na simulação de ponta da planilha continua divergente da regra proposta; não acionado nas entradas existentes. Não transportar esse fator para o motor.
- Ausência confirmada de cobrança reativa não cria cenário independente de surgimento; medição não equivale a cobrança. Efeitos futuros sem dados permanecem condicionados.

## Dados da empresa, conexão e mercado

Cadastro da empresa antes da simulação; unidade salva antes do upload, como já previsto. Nome/titular e endereço podem ser extraídos e apresentados para conferência: manter os coincidentes, confirmar/corrigir divergentes. Endereço da empresa, endereço impresso na fatura e endereço confirmado da cabine/subestação no ponto de conexão são distintos. Rua adjacente pode explicar diferença para a mesma UC/distribuidora, com confirmação registrada. Não sobrescrever cadastro, valor extraído ou snapshot automaticamente.

Mercado sugerido por identificação explícita ou indícios TE/TUSD por ciclo. Ausência de cobrança corrente de energia ativa TE com leitura completa e rede/TUSD identificada sugere livre; presença sugere cativo. Inferência documentada com fontes Enel/CPFL em `docs/corpus/regulatory-review.md`. Leitura parcial, agrupamento ambíguo ou conflito mantém desconhecido. Confirmação tem origem/ator/data; UFER TE e histórico não classificam o fornecimento. Série local agora tem sugestão cativa nos doze ciclos por duas cobranças correntes de energia ativa TE e duas TUSD em cada conta, com campo confirmado ainda desconhecido; mercado livre continua fora do cálculo cativo completo.

## Avanço desta continuação

- `docs/corpus/series-review.md`: doze competências explícitas distintas, coincidentes com os nomes dos arquivos e histórico; 12/12 contagens de dias compatíveis com as datas candidatas. Medições e demanda utilizada cobrada coincidem nos 24 postos/ciclos; TE/TUSD e energia do histórico também coincidem.
- Uma UC por fingerprint, doze números fiscais localizados. Dez chaves NF3e derivam o mesmo CNPJ candidato com dígitos válidos; agosto/setembro sem chave nesse padrão localizada. Não equivale à confirmação independente de identidade.
- Continuidade pendente: maio/2026 termina em 01/05/2026 e junho começa em 31/05/2026 nas datas candidatas. Intervalo de 30 dias exige conferência dos rótulos/ciclos; soma dos dias 365 não prova série contínua. Sem datas corrigidas ou anualização homologada.
- Nos dez meses comuns, 13 cobranças UFER por ciclo/posto coincidem em quantidade/preço nas duas planilhas, com produtos dentro de BRL 0.99 (26 confrontos presentes); sete combinações sem linha textual correspondem a zeros nas duas, sem confirmar ausência automaticamente. Verde repete a ponta em 10/10 entradas, como exemplo estrutural esclarecido pelo usuário; não é cenário real a homologar nem erro de extração. Cenário Verde futuro exige medições e preços próprios. Originais preservados.
- Novos rascunhos locais `series-review.json` e `series-review.md`, script `review_series.py`, ignorados e não aprovados; candidatos anteriores preservados. Sem texto bruto ou imagens persistidos.

Esclarecimento da continuidade: a linha de maio contém três datas (01/04, 01/05 e 31/05), e a de junho (31/05, 30/06 e 31/07). O intervalo surge ao comparar fim/início candidatos, não por ausência de uma competência na lista. Os históricos de junho e julho mostram dois registros MAI/26 com consumos diferentes; possível ciclo adicional ou particularidade de faturamento, sem comprovação de PDF faltante ou calendário alterado. Usuário apresentou a hipótese de que a Enel ajustou o calendário para fazer o mês de referência coincidir com o período de medição, em preparação à migração ao mercado livre informada para agosto/2026. Hipótese de origem `user`, ainda não confirmada documentalmente; compatível com os dois registros MAI/26 e a mudança nas datas candidatas. Seguir com a pendência, sem concluir que falta PDF, corrigir datas ou interpolar consumo.

## Evidências e ferramentas

- `docs/corpus/workbook-review.md`: oito abas, 1.201 fórmulas com cache e divergências P01–P08. Caches e reprodução aritmética não homologam hipóteses.
- `docs/corpus/invoice-review.md` e `representative-review.md`: 12 PDFs textuais, 24 páginas; representativa com 13 itens, transcrição separada e conferência Decimal. Nome ENEL SP identificado, CNPJ derivado da chave NF3e ainda candidato. Cobertura visual, rótulos do ciclo e mercado documental por conferir.
- `docs/corpus/regulatory-review.md`: REN local de 183 páginas, reprodução Leis.org; arts. 301–304 consultados, sem consolidação/vigências homologadas. Nenhum CSV tarifário importado/aprovado.
- Python e openpyxl existentes; pypdf 7.0.0 instalado anteriormente exclusivamente para análise em `.local-tools/pypdf/`, com autorização do usuário. Leitura exigiu execução aprovada fora da sandbox. Nada instalado nesta entrega.
- Originais preservados. Sem PDF, imagem ou texto bruto gravado pela análise; rascunhos estruturados e scripts locais em `.local-analysis/`, ignorados e fora do envio. Gabarito local v0.2 com preços/tolerância atualizados, sem revisor aprovado.

## Verificações desta entrega

Registrada a hipótese do usuário sobre alinhamento do calendário à medição antes da migração. Revisão documental de proveniência, preservação das datas e manutenção da pendência; links/codificação e lista explícita de dois documentos públicos conferidos. Nenhuma nova leitura de PDF, verificação financeira, consulta regulatória, instalação ou execução da aplicação; nenhum aceite alterado.

## Pendências e próximo passo

Conferir primeiro os rótulos e ciclos de maio/junho no original; revisar visualmente os cabeçalhos da série e confirmar identidade, mercado por ciclo e ponto de conexão com o responsável. Completar gabaritos, inclusive agosto/setembro com parcelas somente monetárias; usar a Verde apenas como referência estrutural; eventual cenário Verde será calculado independentemente, com medições e preços/fontes aplicáveis. Aprovação exige responsável/data; achados de impostos separados não são bloqueios. Autorização e procedimento de anonimização para fixtures públicas continuam pendentes. Fase 1 com fixtures sintéticas permanece possível quando solicitada.

## Arquivos e commit

Alterados: `docs/STATUS.md`, `docs/corpus/series-review.md`. Novos/removidos: nenhum. Materiais reais e ferramentas locais fora do envio.

Commit desta entrega: `docs: registra hipotese de ajuste do calendario antes da migracao`. Consultar histórico remoto para o SHA; este status integra o próprio commit.
