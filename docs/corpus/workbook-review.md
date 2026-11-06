# Conferência inicial das planilhas — 06/11/2026

Estado: análise documental e aritmética; **não é gabarito financeiro aprovado**. Originais preservados em `docs/planilhas/`, sem edição e sem envio ao GitHub. Não publicar identificador da unidade, dados pessoais ou transcrição integral das contas neste relatório.

## Evidência e método

Leitura de valores, fórmulas e caches com `openpyxl` já disponível; nenhuma instalação de biblioteca de planilhas. Recomputação independente em Decimal de demanda medida × preço, ociosidade segundo a hipótese da planilha e adicional de ultrapassagem; conferência dos produtos do quadro de reativos. Não se executou Excel, macro ou cálculo genérico de fórmulas. Caches são valores salvos pelo autor, não prova de recálculo atual.

| Arquivo | SHA-256 | Fórmulas / abas |
| --- | --- | --- |
| Analise_Faturas_Energia_Preenchida_Azul.xlsx | f4bb6f9e8565dec7f112b338ed4bc8a05374a87a6db608e8c4400208ee30498d | 769 / 5 |
| Analise_Faturas_Energia_Preenchida_Verde.xlsx | 0c4421712c43125b2fa32c8feafbb83a469849ef08d1d68a17566e924141d929 | 432 / 3 |

As 1.201 células de fórmula têm cache; não foram encontradas células com tipo de erro nas abas. Isso não aprova fontes tarifárias, tributos, medições ou conclusões.

## Divergências que impedem usar a planilha diretamente como gabarito

| ID | Evidência localizada | Implicação / encaminhamento |
| --- | --- | --- |
| P01 | Azul `Demanda_Ponta!B7:B18`, `I3`, `K3:L3`; Verde `Demanda!B7:B18`, `I3`, `K3:L3`: outubro/2025 a setembro/2026 | Não coincide integralmente com a série PDF nomeada agosto/2025 a julho/2026. Não deslocar meses para fazer coincidir; conferir ciclos e anos. |
| P02 | Azul `Demanda_Ponta!J7:J18` usa `=Glinha*2`; `J23:J34` usa `=Glinha*3` | Regra atual e simulada diferem. Pela regra geral da SPEC §8.2, o adicional usa fator 2. Nas entradas existentes nenhum ciclo aciona ultrapassagem, inclusive nos candidatos salvos; o defeito fica inativo e não pode ser detectado apenas pelo total. Manter teste sintético com ultrapassagem. |
| P03 | Coluna M, linhas 7–18 e 23–34, nas três abas de demanda: `=Glinha-(Glinha*18%)` | Redução fixa de 18% não constitui política tributária geral. Confrontar preço efetivo e parcela ociosa efetivamente faturada, incluindo demais tributos. Não transportar esse coeficiente para o motor. |
| P04 | Verde `Demanda!B7:B18`, `E7:E18`, `G7:G18` são idênticos aos da ponta da Azul; candidato em `Simul_Demanda!B28` também coincide | Não há evidência de formação independente do cenário Verde. Nos 12 pares, a demanda da Verde é inferior à demanda fora de ponta da Azul; se representam o mesmo perfil/ciclo, não atende à construção pelo máximo dos postos da SPEC §8.5. Confirmar finalidade da planilha Verde, que pode ser modelo de apresentação. |
| P05 | As abas disponibilizadas tratam demanda e reativos, sem quadro de comparação completa de energia TE/TUSD Azul versus Verde | Esses arquivos não homologam migração de modalidade. Obter tarifas, energia por posto e base temporal/tributária equivalente. |
| P06 | Quadro `Dem_ Reativas e UFER`: Azul D referencia tarifa da demanda de ponta; G/J referenciam fora de ponta. Verde D referencia sua demanda | Referências não provam as tarifas regulatórias auxiliares da SPEC §8.4. Os produtos de demanda reativa são zero nestas entradas; portanto o cache não testa a regra de preço para cobrança não nula. Não criar cobrança hipotética para preencher a lacuna. |
| P07 | Cabeçalhos UFER usam kW e R$/kW nas duas planilhas | Não usar esses rótulos para definir unidade de energia. Conferir a unidade impressa na fatura; separar energia reativa excedente faturada de medição reativa física. |
| P08 | Totais de demanda somam valores sem fechamento explícito por item; somas do quadro de reativos também preservam casas internas | Fechar por componente ou apenas no total pode produzir diferença de BRL 0.01. Documentar política antes de comparar com a conta; não ampliar tolerância silenciosamente. |

P02, P03 e P06 são divergências em relação ao contrato proposto, não uma declaração de irregularidade da distribuidora. Os arquivos originais não foram corrigidos.

## Resultados aritméticos delimitados

Os valores da ponta citados na SPEC §11.3 — custos de BRL 136632.16 e 120644.48 e diferença de BRL 15987.68 — foram reproduzidos a partir das entradas e da **hipótese de tributação da própria planilha**, arredondando somente os totais a centavos. Isso estabelece sua origem aritmética, sem validar a hipótese. Não passa a ser economia homologada.

O total BRL 1413.43 de reativos também é reproduzível pelos produtos das quantidades e preços do quadro, nas duas planilhas. A diferença máxima para caches desses produtos é inferior a BRL 0.000000000001. Ainda é necessário confrontar cada linha com as contas, incluindo os zeros.

Ao fechar separadamente H/K/N por ciclo a centavos (ROUND_HALF_UP apenas como experimento), em vez de fechar o total global, a ponta atual e simulada da Azul diferem em -BRL 0.01; a fora de ponta atual não difere e a simulada difere em -BRL 0.01. A demanda da Verde repete o comportamento da ponta. Este experimento não fixa a política real da distribuidora.

## Perguntas para fechar o gabarito

- A planilha Verde é um exemplo de layout ou uma simulação real de mudança da mesma unidade? Quais fontes de tarifas e medições foram usadas?
- A série pretendida é agosto/2025–julho/2026 ou outubro/2025–setembro/2026? Os meses finais das planilhas pertencem a qual ano?
- O fator 3 na simulação de ponta foi intencional? A implementação seguirá a regra validada, sem reproduzir esse fator por compatibilidade visual.
- Quem revisará os campos esperados e aprovará as divergências após confronto com os PDFs?

Essas respostas não bloqueiam modelos, autorização, catálogo tarifário versionado ou desenvolvimento com fixtures sintéticas.
