# Revisão visual do corpus — 06/11/2026

Conferência documental por Codex das duas páginas de cada um dos doze PDFs. **Aprovação do usuário/responsável e aceite da Fase 0 permanecem pendentes.** Este relatório atualiza conclusões da extração textual; não é implementação ou homologação do parser.

## Método e proteção dos originais

Usado Windows PowerShell 5.1 e o renderizador nativo `Windows.Data.Pdf`, já disponíveis, sem instalar bibliotecas. Páginas renderizadas em streams de memória; nenhum arquivo de imagem, cópia de PDF ou texto bruto gravado. Saída de imagem transportada em blocos com verificação de comprimento antes da inspeção. Tentativas com transporte incompleto produziram artefatos visuais e foram descartadas; as 24 páginas foram depois revistas com transporte completo. Isso não valida fidelidade universal desse renderizador ou OCR.

PDFs originais e candidatos anteriores preservados. Dados normalizados e decisões ficam exclusivamente em `.local-analysis/visual-review.json`; fichas atualizadas e resumo de revisão em `.local-analysis/review-package/REVIEW-RESULT.md`. O histórico dos candidatos antigos não foi apagado.

## O que foi resolvido

- CNPJ da distribuidora lido no próprio cabeçalho das doze contas, inclusive agosto/setembro, onde não havia sido localizado pelo recorte textual. Corresponde à identificação pública da distribuidora já conferida na [fonte oficial Enel](https://www.enel.com.br/pt-saopaulo/golpes-e-fraudes/enel-pix.html). Não foi inferido pela semelhança entre contas.
- Rótulos leitura anterior, leitura atual, número de dias e próxima leitura conferidos visualmente. As datas antes candidatas têm agora sua associação ao rótulo registrada; os valores não foram alterados. Junho continua com 30 dias impressos, separados da premissa do usuário de cobertura aproximada de 60 dias e possível consumo médio.
- Nome/titular, endereço impresso e UC lidos no documento e mantidos somente no rascunho local. O endereço confirmado da cabine/ponto de conexão ainda depende do cliente; não foi preenchido automaticamente com o impresso.
- Quatro parcelas ociosas de agosto/setembro continuam somente monetárias: não há quantidade/preço legíveis preenchidos nessas linhas. A ausência foi preservada, sem reconstruir campos pela regra de 82%.
- Quadro financeiro e segunda página conferidos. Não foram identificados novos itens financeiros nas segundas páginas. Ausência de cobranças observadas de ultrapassagem e demanda reativa foi registrada com a cobertura; medições DMCR não foram convertidas em cobrança. A completude financeira de setembro permanece limitada pela divergência de totais.

## Correção importante: total do quadro não é suficiente

A extração inicial tomou a linha TOTAL do quadro como total da fatura. Os itens reconhecidos somam esse quadro em todas as contas, mas **em setembro/2025 o total a pagar do cabeçalho e o valor do documento de cobrança são maiores que o total do quadro**. A divergência é visível no próprio PDF e também está presente no texto; portanto não se resolve apenas trocando o método de extração.

Resultado atual: **onze faturas reconciliadas contra o total do cabeçalho e uma com residual monetário relevante não explicado**, em setembro. Valores exatos ficam no pacote local, sem publicação de dados financeiros reais. Nenhuma parcela foi criada por diferença e a tolerância de BRL 0.99 por item não foi aplicada para apagar o residual.

As afirmações anteriores de “12 totais com residual zero” ficam restritas ao fechamento interno dos quadros e superadas quanto à conciliação integral das faturas. Valores observados, total do quadro, total do cabeçalho/documento e diferenças são guardados separadamente. Cabeçalho/boleto coincidentes não comprovam pagamento ou autenticidade.

## Outros achados documentais

| Caso | Evidência | Tratamento |
| --- | --- | --- |
| Outubro/2025 | Aviso expresso de que a nota substitui uma anterior | Marcar `replacement` com proveniência; não confundir com “SEGUNDA VIA” e não somar original/substituta se o original vier a ser fornecido. |
| Abril/2026 | Aviso de consumo calculado pela média aritmética dos últimos 12 faturamentos | Marcar energia como estimada, preservando consumo/custo observado. Coincidência entre tabela e cobrança não comprova consumo efetivamente medido. Sem repetir a média ou inventar série horária. |
| Junho/2026 | 30 dias no campo impresso; mudança de calendário confirmada pelo usuário; premissa de aproximadamente 60 dias e possível média de dois meses | Preservar três camadas: dados impressos, confirmação da mudança e premissa de interpretação. Não confundir com o aviso documental de média de 12 meses de abril. Comparabilidade temporal/anualização condicionada. |
| Setembro/2025 | Total de cabeçalho/documento diverge do quadro/itens | `needs_review`, sem conciliação integral aprovada. Esclarecer composição ou versão do documento com o responsável. Não atribuir causa tributária, bandeira ou ajuste sem evidência. |

Continuam válidas a regra de preço cheio, ociosidade a 82% e tolerância inclusiva de BRL 0.99 por item. Os 105 produtos comparáveis e vinte parcelas ociosas quantificadas passam nessa tolerância; isso não resolve a diferença global de setembro ou a qualidade de medição de abril/junho. A Verde continua sendo apenas referência estrutural.

## Antes da Fase 1

O usuário pediu concluir o trabalho recomendado antes de iniciar a Fase 1; nenhuma instalação ou implementação foi iniciada. Para fechar o gabarito real, resolver o conflito de setembro, registrar aceitação dos desconhecidos e das limitações de abril/junho, confirmar ponto de conexão/mercado e indicar responsável/data de aprovação. Consulta sobre setembro enviada ao usuário; resposta não presumida. Autorização/procedimento de anonimização e fontes/preços por vigência necessários à homologação comercial continuam pendentes. Nenhum item composto da SPEC foi marcado.
