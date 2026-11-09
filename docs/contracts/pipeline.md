# Contratos entre etapas — v0.1

Proposta documental para Fases 1–4; não define endpoints implementados. Requisitos: SPEC §§4–7, 8.1, 8.6–8.7, 10–12. Tipos de fatura: [dicionário](invoice-data.md). Permissões: [acesso](access.md).

## Envelope comum

Objetos persistíveis/transportáveis levam `contract_version`, IDs de recurso, `revision`, `created_at` UTC e autoria. Contexto autenticado fornece ator, perfil e empresa; payload cliente não decide dono/perfil. Decimais são strings. Erro: `{code, stage, resource_id, field_path, retryable, action}`; sem PDF, texto bruto, tokens ou conteúdo sensível. Códigos propostos estáveis: `UNIT_REQUIRED`, `CAPACITY_UNAVAILABLE`, `INVALID_DOCUMENT`, `DUPLICATE`, `REVIEW_REQUIRED`, `REVISION_CONFLICT`, `QUOTA_EXCEEDED`, `MODULE_DATA_MISSING`, `RESOURCE_UNAVAILABLE`. A Fase 1 mapeará HTTP/OpenAPI sem alterar a semântica.

## Leitura → armazenamento

Entrada efêmera `ReadRequest`: simulação e revisão esperada, chave de idempotência, metadados de admissão e bytes do PDF em memória. Unidade já salva; seleção local não envia arquivo. Somente “Ler fatura” admite e processa. Aplicar limites acumulados da SPEC §5.1; reserva atômica da capacidade, OCR fora de transação. Bytes nunca entram em jobs duráveis, logs, banco ou snapshots.

Saída `ExtractionResult`: ID de processamento, revisão de admissão, SHA-256, versão do adaptador/parser, cabeçalho (incluindo nome e endereço impressos quando disponíveis), medições, itens, proveniência, validações, cobertura e conflitos. A conferência mantém separados cadastro da empresa, endereço impresso e ponto de conexão confirmado. Confirmação/correção não sobrescreve automaticamente os outros registros; diferença de rua pode ser explicada pela localização da cabine, com UC/distribuidora coincidentes. Sugestão de mercado por TE/TUSD exige cobertura e confirmação; ausência em leitura incompleta não classifica livre. Não contém PDF, imagem ou texto integral. `source_kind=synthetic` identifica fixtures; não atribuir proveniência PDF/OCR fictícia.

Persistir cabeçalho + medições + itens + proveniência atomicamente; conflito/retry não duplica fatura. Falha de persistência reverte filhos e registra estado de falha separadamente. Apenas commit permite avançar para conferência/pronto. Documento descartado antes de sair da conferência; interrupção antes de persistir exige reenvio, sem alegar retomada dos bytes.

## Armazenamento → simulação

Entrada `CalculationInput`: `simulation_id`, `owner_id`, `company_id`, `actor_id`, `dataset_revision`, snapshot da unidade, faturas estruturadas confirmadas, cobertura (ciclos, competências, lacunas, sobreposições), marcadores de escopo, tarifas com fonte/vigência/versão/base tributária, regras e política de arredondamento versionadas, cenário e hipóteses explícitas.

Admissão considera o mínimo da SPEC §7: faturamento, cliente/UC, classificação, datas e contratação. Não exigir boleto, chave fiscal, impostos separados, contadores de medidor ou investigação administrativa. Diferença informativa de total a pagar versus quadro não bloqueia módulo com base faturável consistente. Admissão exige 1–12 faturas válidas/conferidas, até 12 competências em janela máxima de 18 meses, nenhuma pendência do conjunto, envio/leitura em andamento ou erro não resolvido. Arquivos apenas selecionados devem ser lidos/removidos; como a seleção é local, a interface bloqueia o envio do cálculo e informa os selecionados pendentes; o servidor revalida todo processamento admitido e não confia em sinalizador do cliente para tornar faturas prontas. Revisão esperada impede corrida com edição/remoção. Uma conta basta para admitir cálculo, sem garantir todos os módulos.

Congelar entradas, referências/valores tarifários efetivamente usados, regras e versão do motor em `calculation_run`. Motor recebe objetos de domínio, sem ORM, rotas, OCR ou PDF. Indisponibilidade de preço efetivo cheio não se transforma em zero. Não reaplicar impostos ao preço cheio observado; para preço ausente, resolver tarifa ANEEL e formar preço cheio com parâmetros tributários aplicáveis e documentados (SPEC §8.6). Ausência/divergência de tributos separados não bloqueia preço cheio disponível. Ociosidade LEI ESTADUAL usa preço cheio da demanda contratada × 0,82, na ponta, fora de ponta e demanda única, sem segunda redução. Preservar preço/valor histórico observado e registrar divergência, sem aprovação implícita do candidato. Visões histórica e comparativa usam bases identificadas e equivalentes.

O snapshot comparativo registra, por componente/posto: preços candidatos elegíveis e excluídos, origem/ciclo, critério de máximo e desempate, referência temporal, classificação de mercado/marco ACL, IDs/versões das tarifas ANEEL, tarifa-base e unidade, parâmetros e fonte tributária, incidências, regra de formação e preço cheio resultante. Aplicar o máximo da série (trecho pré-migração quando houver passagem a ACL dentro do período; período inteiro quando todo ACL, apenas componentes suportados), conforme SPEC §8.6. C0 e alternativas usam referência equivalente, sem confrontar gasto histórico com alternativa reprecificada. Falta de tarifa, tributo aplicável, marco confiável ou medição por posto afeta somente os módulos dependentes; não inferir preços de energia do fornecedor ACL.

## Simulação → relatório

Saída `CalculationResult`: `run_id`, revisão de origem, versões, `modules[]`, séries por ciclo/posto, cenários C0–C3 quando calculáveis, componentes incluídos/constantes, custos atual/alternativo, diferenças brutas, economia exibível, bases percentuais, reconciliações, anualização ou motivo de bloqueio, hipóteses e limitações.

Cada módulo possui `status=complete|partial|unavailable`, `reason_codes`, entradas utilizadas e memória estruturada (quantidade, tarifa, regra, arredondamento e resultados). Observado não é potencial evitável. Não preencher etapas C1/C2 indefinidas com zero; subtotal calculável é rotulado. Preservar diferenças negativas na memória e incluir cenário atual entre as opções. Não anualizar sem ciclos comparáveis.

Entrada de relatório: execução congelada + revisão editorial, idioma/formatação e comentário técnico auditado. Saída: modelo de apresentação com os quatro eixos da SPEC §11, tabelas e séries; HTML e PDF referenciam o mesmo run. Templates formatam valores, não calculam finanças. Relatório parcial suprime conclusões/gráficos sem suporte e mostra motivos. PDF sob demanda, autenticado e sujeito à retenção, sem URL pública previsível.

## Estados e revisão

Não confundir estado de campo, processamento e módulo. Estados operacionais da SPEC §5.3:

| Estado | Significado e próximo passo |
| --- | --- |
| `uploaded` | Arquivo admitido na fila efêmera; avançar para extracting ou falha/expiração |
| `extracting` | Extração ativa; sucesso persistido leva a needs_review ou ready |
| `needs_review` | Pendências; correção/conferência válida permite ready |
| `ready` | Conjunto admitido pode iniciar calculating |
| `calculating` | Run em execução; termina completed/partial/failed |
| `completed` | Execução com módulos previstos completos |
| `partial` | Resultado útil com limitações explícitas |
| `failed` | Erro estruturado; repetir quando permitido ou remover arquivo |
| `expired` | Trabalho efêmero perdido/vencido; reenvio quando bytes necessários |

`uploaded/extracting/needs_review/ready/failed/expired` aplicam-se ao processamento do arquivo; `calculating/completed/partial` descrevem execução/conjunto, não extração. Rascunho pré-upload e exclusão são ciclo de vida próprio da simulação; nomes finais serão fixados no esquema da Fase 1. Estado agregado deve refletir todos os arquivos, não apenas o último concluído.

Edição/remoção incrementa `dataset_revision`, invalida resultado atual e preserva run anterior como histórico; não o sobrescreve. Remoção e exclusão cancelam jobs e fazem resultados tardios falharem pela revisão/tombstone. Exclusão revoga acesso imediatamente e libera vaga na mesma operação lógica. Chaves de idempotência são vinculadas ao ator, operação e payload/revisão; repetição idêntica retorna recurso original, conteúdo divergente gera conflito. Reenvio com nova chave continua sujeito a hash e duplicidade lógica.

## Cenários de aceite das fronteiras (a implementar)

- OCR falha ou commit falha: nenhuma fatura pronta e nenhum item órfão.
- Correção durante cálculo: execução da revisão antiga permanece histórica, nunca atual silenciosamente.
- Exclusão durante job: retorno tardio não recria recurso nem relatório.
- Entrada sem demanda e com reativos conferidos: diagnóstico observado disponível, otimização indisponível.
- Falta de tarifa alternativa: comparação indisponível, nunca economia calculada com tarifa zero.
- Relatório online/PDF: mesmos valores, run e versões; acesso cruzado negado.

Estes são contratos de verificação, não testes executados.

## Regra esclarecida pelo usuário em 06/11/2026

A regra de preço cheio observado e de ociosidade a 82% permanece. O esclarecimento de 09/11/2026 amplia a formação de preços ausentes via ANEEL e a seleção da referência comparativa, conforme SPEC §8.6 e o snapshot descrito acima. Não altera o gabarito mínimo aceito na Fase 0, não autoriza auditoria fiscal integral e não homologa tarifas ou fórmulas tributárias.
