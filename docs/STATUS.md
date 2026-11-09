# Estado do EcoWatt

Atualizado em 09/11/2026. Referência: SPEC versão 3.11; gabarito mínimo aceito v0.2, com extensão documental de escopo para as próximas fases.

## Direção atual

**Fase 0 concluída**, com aceite explícito do usuário desta conversa em 06/11/2026 para os contratos e o gabarito mínimo local das doze faturas. O aceite inclui desconhecidos e ressalvas documentados, sem autorizar publicação de dados reais ou homologação comercial. Não foi informado nome civil do responsável.

Escopo aceito: concentrar somente em **faturamento, informações do cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas**, conforme os quatro blocos mostrados pelo usuário. Não cadastrar exaustivamente a conta ou exigir auditoria de informações fiscais, boleto, pagamento, códigos de medidor e outros dados administrativos. A investigação ampliada anterior foi além do escopo e permanece apenas como histórico.

**Fase 1 concluída para desenvolvimento local**, conforme pedido do usuário de encerrar a fase. O último critério foi implementado com controle de tarefas, cancelamento transacional e rejeição de persistência tardia. Integração pelo [PR #2](https://github.com/virgilio-vpr/EcoWatt/pull/2). Dependências somente em `.venv`, com uv.lock; sem OCR/cálculos ou produção habilitada. SMTP desabilitado por padrão e provedor externo não homologado; não usar dados reais.

## Regras que permanecem

- Preço unitário cheio observado sem reaplicar impostos. Pela atualização de 09/11/2026, preços ausentes de cenários serão obtidos da tarifa ANEEL com formação tributária documentada, sem auditoria fiscal integral (§8.6). Ociosidade LEI ESTADUAL = preço cheio da demanda contratada × 0,82 em ponta/fora de ponta/única. Tolerância de até BRL 0.99 inclusive por item. Quatro parcelas somente monetárias mantêm quantidade/preço desconhecidos.
- Base financeira do diagnóstico = **TOTAL do quadro de faturamento**. Comparar com itens e subtotais, com residual dessa base. Total a pagar do cabeçalho, se disponível, é informação geral separada. Divergência externa ao quadro não bloqueia automaticamente demanda/reativos com dados consistentes, não cria parcela por diferença e não equivale a auditoria do valor a pagar.
- Cadastro da empresa, endereço impresso e ponto de conexão/cabine são separados. Copiar dados coincidentes com confirmação; corrigir ponto de conexão se diferente, inclusive rua adjacente. CNPJ completo do cliente não é exigido se impresso mascarado.
- Distribuidora corretamente identificada no cadastro/catálogo, UC, subgrupo/modalidade e período continuam necessários às regras aplicáveis. CNPJ emissor, nota fiscal, chave/protocolo e status formal de refaturamento são opcionais; versão do layout é metadado técnico. Duplicatas reais no lote ainda exigem resolução por hash/UC/competência/ciclo/dados.
- Demandas contratadas e itens quantificados são centrais. Demanda medida só é exigida para módulos que dela dependem; aproveitar demanda utilizada faturada quando seu significado estiver identificado. Não exigir contadores de medidor, FP ou séries impressas para diagnóstico observado.
- Mercado sugerido por energia ativa TE/TUSD e contexto, com confirmação quando necessária ao módulo. Livre permanece fora do cálculo cativo completo. Ausência de cobrança reativa confirmada não cria oportunidade hipotética nem garante ausência futura.

## Corpus no escopo mínimo

- Doze quadros faturáveis consistentes, com 135 linhas e residual zero contra TOTAL do próprio quadro. 105 produtos comparáveis e vinte parcelas ociosas quantificadas passam na tolerância. Setembro tem diferença para cabeçalho/boleto, agora **informativa**, sem bloqueio automático; não foi apagada ou classificada por hipótese.
- Doze competências, datas/rótulos e demandas contratadas conferidos; CNPJ da distribuidora foi lido nas doze contas, mas essa conferência não será requisito repetido do produto. Informação visual anterior preservada nos rascunhos, sem imagens/PDFs/texto bruto gravados.
- Abril tem aviso de consumo pela média de 12 faturamentos: conservar como estimado quando afetar cálculo. Junho mantém 30 dias impressos e premissa do usuário de cobertura aproximada de 60 dias, sem acumulação e com possível média de dois meses. Mudança de calendário antes do ML em agosto/2026 confirmada pelo usuário. Não dobrar/interpolar consumo; limitar apenas conclusões dependentes da comparabilidade temporal.
- PDFs agosto/2025–julho/2026 são referência principal; planilhas só nos dez meses comuns. Verde é referência estrutural, não cenário financeiro esperado. Fator 3 de ultrapassagem da planilha não será reproduzido.

## Gabarito atual e verificações

`.local-analysis/minimum-billing-review.json` contém a projeção mínima v0.2; `.local-analysis/review-package/MINIMUM-REVIEW.md` é o resumo atual para revisão. Arquivos de auditoria ampliada anteriores são históricos e não geram pendências administrativas obrigatórias. Aceite registrado no JSON e no resumo local em 06/11/2026, limitado ao mínimo v0.2; os candidatos ampliados anteriores não foram aprovados integralmente.

Verificados por projeção e asserções: doze bases do quadro fecham; diferença de setembro preservada como informação; quatro itens monetários sem dados inventados; consumos, datas e demandas originais preservados. S01 deixa de bloquear por CNPJ opcional; S26 distingue residual do quadro e diferença de total a pagar, sem bloqueio artificial. São 26 casos sintéticos documentais; sem testes da aplicação, nova leitura de PDF ou instalação nesta alteração. Encerramento: metadados de aceite, preservação das entradas locais, links e checklist da SPEC conferidos. Somente a Fase 0 foi marcada; nenhuma funcionalidade foi declarada implementada.



Hipótese de setembro conferida a pedido do usuário: forte compatibilidade numérica da diferença para o total a pagar com bandeira vermelha patamar 2 não discriminada. Fonte Enel para o mês e MME para BRL 78.77/MWh; memória Decimal local em `.local-analysis/september-flag-check.json`, com desvio de poucos centavos na estimativa de preço cheio por proporção da própria conta. Não adicionar item observado ou converter a hipótese em gabarito aprovado. Fontes e método em [referências do corpus](corpus/regulatory-review.md).

## Fluxo de branches

Fase 0 integrada à `main`; Fase 1 integrada pelo [PR #2](https://github.com/virgilio-vpr/EcoWatt/pull/2) no commit `75d32b01671188c263e9b054587546d190cbe40b`. A branch `fase-2` foi criada desse merge e seu estado foi conferido no GitHub nesta entrega. Novos commits seguem nela, com integração por PR; nenhum novo merge foi solicitado nesta atualização documental. Operações pela integração GitHub, sem Git local.

## Entrega atual — Fase 2, resultado normalizado e grafo sintético

Quarta entrega em 09/11/2026, sobre `d616c5c6be1b3b36d952677ffd089e796add218d` na `fase-2`, conferida remotamente e com CI anterior aprovada. Nenhum merge. Mantidos admissão, cotas por dono, autoria explícita, Decimal e protocolo TASKS.

Implementado contrato puro/fechado `normalized-invoice-v1`: campos/estados/unidades, limites de Decimal, dependências sem ciclos e evidências de mercado por ciclo. O subprocesso pode produzir exclusivamente gabarito inventado, validado por JSON limitado. `run_invoice_once` publica header, medições, itens, proveniência inicial, dependências, evidências, validação, vínculo e conclusão TASKS em uma transação. Replay é vinculado à lease original e ao mesmo conteúdo. Toda publicação fica needs_review; não há aprovação financeira, revisão operacional ou cálculo.

Migração aditiva `0007_invoice_publications`: vínculo tarefa/fatura e revisão positiva do conjunto. `Simulation.revision` continua protegendo unidade/tombstone; `dataset_revision` avança em publicação/remoção e nas mudanças da unidade, sem cancelar faturas independentes admitidas na mesma revisão. Registros novos usam invoice-v0.3; metadados históricos anteriores não foram reinterpretados.

GET paginado/lista e GET por ID retornam dados estruturados e proveniência com autorização dono/admin e Decimal string. DELETE exige confirmação, CSRF e revisões de unidade/conjunto; remove grafo/vínculo, marca admissão removida e libera orçamento atomicamente. Remoção da reserva também abrange grafo já publicado quando houver vínculo. Exclusão da simulação inclui todos os filhos; resultados tardios não recriam dados. Contratos/limitações em [INVOICE-STORAGE](INVOICE-STORAGE.md).

## Verificações reais

- **195 testes aprovados**, incluindo Edge e **43 casos novos**, na execução final (124,28 s).
- Cobertos publicação/replay concorrente, lease falsa/conteúdo alterado, rejeição de floats/NaN/escala/overflow/campos extras, ausência versus zero, estimativa/dependências/ciclos, identidade, autoria admin, acesso cruzado, JSON Decimal string, remoção concorrente e rollback de grafo/vínculo/conclusão/revisão/orçamento.
- Subprocesso publicou duas fixtures admitidas incrementalmente sem cancelar a segunda. Resultados após remoção/exclusão/revisão/bloqueio/expiração são recusados; nenhuma fixture real processada. Todas as publicações sintéticas ficam needs_review.
- Migração local aplicada: alembic current = 0007_invoice_publications (head), alembic check sem divergências. Upgrade limpo/preservação de raízes, downgrade/upgrade e FKs verificados em descartáveis; teste com publicação preenchida preserva fatura/filhos/tarefa e documenta perda intencional de vínculo/contador no downgrade.
- Primeira execução encontrou um teste antigo carregando o ORM atual contra esquema histórico sem a nova coluna; consulta ajustada para ler apenas a coluna histórica conferida. Regressão final aprovada. Esse ajuste não muda migrações antigas.
- compileall aprovado; uv pip check: 41 pacotes compatíveis; uv lock --check --offline aprovado. Nenhuma dependência instalada/alterada. Ambiente virtual existente, sem global/admin/containers ou mudança de políticas. Testes locais autorizados pela revisão automática.
- .env, corpus e alterações locais preexistentes preservados e fora do envio. Nenhum PDF, imagem ou texto bruto real recebido/publicado. PostgreSQL não validado. CI e SHA finais serão informados na resposta após consulta remota; este status integra o próprio commit.

## Pendências e próximo passo

PDFs e todos os layouts documentais continuam desabilitados. Completar/verificar §5/§12 antes de recebimento real: confinamento sem rede/privilégios, CPU/RAM/pixels, descendentes órfãos, watchdog rígido, swap/dumps, diretório RAM quando necessário e ausência de spool no framework/proxy. O spawn sintético não comprova sandbox nem descarte de PDF real.

Próxima integração de dados: revisão versionada de campos/dependentes, validações financeiras, duplicidade lógica/refaturamento e prontidão do conjunto. Depois de homologar segurança/layout, conectar adaptador específico. Cabeçalho visual/seletor, contato e fluxo completo Ler fatura seguem pendentes. Não habilitar ready/cálculo apenas pela persistência. Nenhum novo critério integral da seção 15 foi marcado; somente progresso parcial atualizado.

Ressalvas da Fase 0 intactas: desconhecido não equivale a zero, hipóteses não são homologação e Verde exemplificativa não é gabarito financeiro. SMTP externo/MFA/produção/retenção permanecem nas fases próprias.

## Arquivos e commit

Novos: docs/INVOICE-STORAGE.md; migrations/versions/0007_invoice_publications.py; src/ecowatt/invoice_result.py; src/ecowatt/synthetic_invoice.py; src/ecowatt/services/invoice_storage.py; tests/test_invoice_storage.py.

Alterados: EcoWatt_PROJECT_SPEC.md; README.md; docs/ADMISSION.md; docs/API.md; docs/COORDINATOR.md; docs/DATABASE.md; docs/STATUS.md; docs/TASKS.md; docs/contracts/invoice-data.md; docs/contracts/pipeline.md; docs/phases/phase-02-invoices.md; src/ecowatt/api/health.py; src/ecowatt/api/resources.py; src/ecowatt/db/admissions.py; src/ecowatt/db/models.py; src/ecowatt/schemas.py; src/ecowatt/services/admission.py; src/ecowatt/services/coordinator.py; src/ecowatt/services/invoices.py; src/ecowatt/services/simulations.py; src/ecowatt/services/synthetic_worker.py; src/ecowatt/services/tasks.py; tests/test_invoices.py. Removidos: nenhum.

Commit na fase-2: feat: persist normalized synthetic invoices with transactional provenance. Envio limitado aos 29 arquivos acima sobre árvore remota preservada. Alterações preexistentes em docs/contracts/access.md e docs/corpus/regulatory-review.md ficam intactas e fora do envio, assim como .env, corpus, bancos, ambientes, caches e temporários.
