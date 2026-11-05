# Corpus e homologação — inventário em 05/11/2026

## Materiais efetivamente disponíveis

Materiais indicados pelo usuário para continuidade da Fase 0 e confirmados localmente:

| Local | Inventário | Conferência realizada |
| --- | --- | --- |
| `docs/faturas/` | 12 PDFs, nomes de agosto/2025 a julho/2026 | SHA-256 distintos; sem duplicatas binárias |
| `docs/planilhas/Analise_Faturas_Energia_Preenchida_Azul.xlsx` | 5 abas, 769 células com fórmulas | Estrutura XLSX inspecionada em memória; nenhum vínculo externo de workbook identificado |
| `docs/planilhas/Analise_Faturas_Energia_Preenchida_Verde.xlsx` | 3 abas, 432 células com fórmulas | Estrutura XLSX inspecionada em memória; nenhum vínculo externo de workbook identificado |

Períodos acima são inferidos **somente dos nomes**, ainda não conferidos no cabeçalho. Hashes diferentes não excluem duplicatas lógicas. Conteúdo dos PDFs, identidade da distribuidora, mercado, modalidade, unidade, competências e correspondência das planilhas ainda não foram conferidos. A presença de fórmulas não valida sua regra, resultado ou relação com a série. Não houve extração de texto bruto para arquivos nem instalação de recursos.

A indicação das pastas permite a análise local solicitada; não equivale à aprovação do gabarito nem à autorização para publicar originais ou incorporar dados pessoais a fixtures versionadas. Anonimização e condições do acervo de homologação permanecem a definir. Os originais ficam locais e fora da lista de envio manual ao GitHub.

A inspeção anterior havia encontrado somente documentação; este inventário a substitui quanto à disponibilidade desses materiais. CSV tarifário, CUSD e gabarito independente aprovado continuam não identificados. As imagens descritas na SPEC §11.3 não são resultados homologados. `debug.log` continua sendo artefato local, fora do envio.

Disponível nesta entrega: [casos sintéticos](synthetic-cases.md), definidos a partir dos contratos e da fórmula interna da SPEC §8.2. Não representam ENEL, tarifas vigentes, leitura de PDF ou evidência regulatória independente.

## Pacote necessário para homologação

| Material a obter | Evidência esperada | Uso / bloqueio atual |
| --- | --- | --- |
| Série real ENEL SP A4 Azul autorizada, idealmente 12 competências consecutivas | PDFs textuais/digitalizados com autorização e processo de anonimização separado do fluxo de clientes; CNPJ emissor, UC, mercado e layout conferidos | Homologação do primeiro adaptador pendente |
| Gabarito manual por fatura | Todos os campos do dicionário, linhas, postos, estados de ausência, unidades e proveniência; revisor/data; totais/residuais conferidos | Não há conjunto real esperado aprovado |
| Planilha original e fórmulas | Células/fórmulas e entradas estruturadas, preços, tributos e perdas por ciclo, resultados por componente | Comparação financeira com planilha pendente |
| Tarifas e atos oficiais por vigência | Fonte oficial, arquivo/versão, distribuidora/CNPJ, subgrupo, modalidade e base de preço | Nenhuma tarifa real fixada nesta fase |
| CUSD, aditivos e histórico contratual | Demandas por posto, restrições e datas de alteração, exceções e perdas | Recomendação de implantação condicionada |
| Incidências tributárias e perdas | Regra aplicável e bases verificadas nos documentos | Comparação com tributos condicionada; sem alíquota inventada |
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
| D03 | Especialista: quais tributos, perdas, tarifas e política de arredondamento por vigência? | Aritmética sem tributos rotulada, nenhuma tarifa ausente igual a zero |
| D04 | Piloto: confirmar qual planilha recebida corresponde à série e quais entradas/resultados são referência? | Relatório demonstrativo sem reproduzir resultados como aprovados |
| D05 | Piloto/distribuidora: existem dados por posto na Verde e intervalares de reativos? | Módulos parciais com motivos explícitos |
| D06 | Responsável do produto: aprovar nomes/tipos deste contrato e conjuntos reais esperados? | Implementar proposta versionada, registrar ajustes antes de migrar dados reais |
| D07 | Especialista: convenção de dias do ciclo, grandezas reativas ambíguas e agrupamentos TE/TUSD do layout? | Preservar unidade/origem; bloquear uso ambíguo |
| D08 | Responsável comercial/privacidade: confirmar retenção e tratamento de vínculos de orçamento na exclusão? | Definir autorização/cancelamento; não lançar operação comercial |

Fontes regulatórias candidatas permanecem as da SPEC §17, com a limitação de acesso já registrada ali. Não houve consulta externa nem validação de vigência nesta entrega. Fixação de atos, tarifas e redação consolidada pertence à homologação; a fórmula sintética testa somente a regra escrita da SPEC.
