# Série de faturas — conferência textual ampliada

Análise local de 06/11/2026. **Rascunho não aprovado**; autor da análise documental: Codex. Revisor humano/data: pendentes. Esta entrega amplia cabeçalhos, medições e cruzamentos com as planilhas; não implementa a aplicação ou homologa o corpus.

## Fonte e método

Relidos em memória os 12 PDFs com pypdf 7.0.0 existente, sem OCR, renderização ou instalação. Hash de cada original confrontado com o rascunho financeiro anterior. Competência obtida do campo explícito MM/AAAA e conferida na linha atual do histórico; nome do arquivo usado somente como confronto. Datas da classificação mantidas como início/fim/próxima leitura candidatos, com associação aos rótulos ainda sujeita à conferência visual. Número de dias veio do histórico do mês, sem dedução a partir do nome do arquivo.

As quantidades da tabela de medição foram comparadas às linhas de demanda utilizada cobradas; fora de ponta usa o máximo entre as linhas CAP/INDU. Energia do histórico foi comparada às linhas de cobrança TE/TUSD, sem duplicar kWh. Não foi feita reconstrução intervalar de reativos ou análise separada de impostos.

## Cobertura por competência

| Caso | Competência explícita | Dias impressos | Diferença das datas candidatas confere | Linhas correntes TE / TUSD | Medição de demanda versus cobrança |
| --- | --- | --- | --- | --- | --- |
| REAL-LOCAL-01 | agosto/2025 | 31 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-02 | setembro/2025 | 31 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-03 | outubro/2025 | 30 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-04 | novembro/2025 | 31 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-05 | dezembro/2025 | 30 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-06 | janeiro/2026 | 31 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-07 | fevereiro/2026 | 31 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-08 | março/2026 | 28 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-09 | abril/2026 | 31 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-10 | maio/2026 | 30 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-11 | junho/2026 | 30 | sim | 2 / 2 | dois postos coincidem |
| REAL-LOCAL-12 | julho/2026 | 31 | sim | 2 / 2 | dois postos coincidem |

As doze competências são distintas e consecutivas. Os números de documento fiscal foram localizados nos doze textos; identificadores não são publicados. A UC tem o mesmo fingerprint local nas doze contas. Os contratos por posto não variam nesta série. Isso confirma consistência interna, sem confronto com cadastro real salvo ou CUSD.

Dez PDFs, de outubro/2025 a julho/2026, têm chave NF3e textual da qual se deriva o mesmo CNPJ candidato, com dígitos verificadores válidos. Agosto/setembro não tiveram chave nesse padrão localizada; não transportar o CNPJ para eles como extração confirmada. Validade do dígito não comprova por si só identidade do emissor. Nome e endereço impressos continuam separados do endereço confirmado da cabine/ponto de conexão, ainda não informado nesta conferência.

Há duas linhas correntes de energia ativa TE e duas TUSD em cada conta: **mercado sugerido cativo nos doze ciclos**, em conformidade com o indício documentado na SPEC §7.1 e com o contexto informado pelo usuário. O campo de mercado confirmado permanece desconhecido; não houve confirmação humana nova nem classificação por UFER TE ou simples ocorrência da sigla.

## Continuidade: pendência que a contagem de meses não detecta

REAL-LOCAL-10 tem datas candidatas de 01/04/2026 a 01/05/2026; REAL-LOCAL-11, de 31/05/2026 a 30/06/2026. A comparação deixa **30 dias entre fim e início candidatos**. REAL-LOCAL-12 começa em 30/06/2026 e termina em 31/07/2026. Os outros pares se encadeiam pelas datas candidatas.

Releitura dirigida em 06/11/2026 confirmou a sequência completa das datas: maio traz `01/04/2026 → 01/05/2026 → 31/05/2026`, junho traz `31/05/2026 → 30/06/2026 → 31/07/2026` e julho traz `30/06/2026 → 31/07/2026 → 31/08/2026`. A diferença de 30 dias é consequência de interpretar as duas primeiras como leitura anterior/atual, não de faltar a competência junho na lista. Os históricos de junho e julho contêm **dois registros MAI/26 com consumos diferentes**, indício de um ciclo adicional ou outra particularidade de faturamento a esclarecer. Isso não comprova documento faltante, refaturamento ou mudança de calendário. Manter a hipótese em revisão, sem substituir datas ou remover um registro histórico como duplicata.

Hipótese informada pelo usuário em 06/11/2026: a Enel pode ter ajustado o período de faturamento para alinhar mês de referência e período de medição, em preparação à migração ao mercado livre informada para agosto/2026. Registrar origem `user` e estado `estimated`, sem tratar a motivação, a mudança de calendário ou a eventual existência de conta adicional como fato comprovado. A hipótese é compatível com os dois registros MAI/26 e a transição das datas candidatas, mas precisa de documento ou confirmação da distribuidora para encerrar a questão. Não alterar competência, datas ou consumo com base nessa hipótese; o trabalho independente pode continuar com a limitação explícita.

Os dias impressos somam 365, mas essa soma não demonstra continuidade do intervalo coberto. Conferir os rótulos e a natureza desses ciclos nos originais, sem concluir que falta uma fatura ou que existe erro de cobrança apenas por esse diagnóstico. Não corrigir datas pelo nome do arquivo, interpolar consumo ou apresentar anualização como série contínua conferida enquanto a questão estiver aberta.

## UFER e referência estrutural Verde nos dez meses comuns

Os dez meses comuns fornecem vinte combinações de ciclo/posto. Treze têm cobrança UFER textual; nas duas planilhas, as treze quantidades e preços correspondentes coincidem com a fatura, e quantidade × preço cabe na tolerância autorizada de BRL 0.99. São 26 confrontos de linha presentes, treze em cada planilha. Nas sete combinações sem linha UFER localizada, ambas as planilhas têm quantidade/preço zero: catorze confrontos de ausência textual versus zero da planilha. Isso não promove ausência textual a `zero_confirmed` sem conferência de cobertura.

Na Verde, a demanda de entrada coincide com a ponta da Azul nos dez meses comuns e difere do máximo medido dos dois postos em todos eles. A medição e a demanda utilizada faturada coincidem nesta série; portanto a divergência não decorre apenas da escolha entre essas duas colunas. A regra da SPEC §8.5 exige o máximo dos postos com bases compatíveis para formar a demanda única. O usuário esclareceu que a cópia foi usada apenas para exemplificar a estrutura de uma planilha Verde, reconhecendo que a demanda não é correta para um cenário real. A coincidência numérica é esperada nessa referência e não constitui falha de extração ou bloqueio a resolver no original. Preservar a planilha e usar somente sua estrutura/apresentação; eventual cenário Verde deve ser formado independentemente, com medições e preços adequados. Não homologar os números copiados nem economia de migração.

## Artefatos locais e próximo passo

- `.local-analysis/series-review.json`: doze rascunhos por fatura com hashes, cabeçalhos, itens, medições, sugestão de mercado, continuidade e comparações das planilhas. Dados normalizados, sem texto bruto.
- `.local-analysis/series-review.md`: tabela local de datas e roteiro de revisão; não é aprovação.
- `.local-analysis/review_series.py`: script pontual da análise, com asserções de consistência e saída resumida sem identificadores.

Todos ficam locais e ignorados. Rascunhos anteriores e originais foram preservados. Permanecem as regras de preço cheio, ociosidade a 82% e tolerância inclusiva de BRL 0.99 por item. Conferências monetárias anteriores não foram substituídas ou reinterpretadas como revisão visual. Nenhum arquivo real foi publicado.

Próximo passo: conferir os rótulos/ciclos de maio e junho, a identidade e o ponto de conexão com o responsável; completar os campos/estados do gabarito e usar a Verde como referência estrutural, preparando eventual cenário Verde de forma independente com demanda única e preços próprios por vigência. Ainda faltam aprovação identificada e autorização/procedimento de anonimização para fixture pública. Nenhum checkbox da Fase 0 foi marcado.
