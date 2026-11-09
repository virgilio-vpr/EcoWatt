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

## Entrega atual — Fase 2, revisão versionada e conferência observada

Quinta entrega em 09/11/2026 sobre `9cc9e031de68e0af4ff1fd44b7afdba5dd91c7d9`, remoto fase-2 conferido e CI anterior aprovada ([execução 42646480531](https://github.com/virgilio-vpr/EcoWatt/actions/runs/42646480531)). Nenhum merge. Publicação normalizada, admissão e coordenador anteriores permanecem exclusivamente sintéticos; detalhes em [INVOICE-STORAGE](INVOICE-STORAGE.md), [ADMISSION](ADMISSION.md), [COORDINATOR](COORDINATOR.md) e [TASKS](TASKS.md).

POST autenticado `.../invoices/{invoice_id}/reviews`: campos existentes, lote fechado, justificativa/autoria, controle de revisão de unidade/conjunto/fatura/campo e recibo idempotente por ator/fatura. Atualiza coluna e proveniência atomicamente; conserva valores, datas e entradas concretas anteriores; invalida transitivamente derivados/estimativas, sem recalcular silenciosamente. Nova dependência exige versão atual da mesma fatura, fora dos caminhos alterados/invalidados no comando. Fonte corrigida exige novo comando para derivação. Revisão da fatura e do conjunto avançam uma vez; revisão da unidade/TASKS não muda, permitindo publicações independentes já admitidas. Replay original da publicação não sobrescreve uma correção.

Conferência observada: produto com preço cheio sem reaplicar impostos, tolerância inclusiva BRL 0.99 por item, soma assinada contra TOTAL do quadro e residual pendente quando não zero. Total a pagar permanece informação separada. Itens apenas monetários mantêm quantidade/preço desconhecidos. Memória financeira por revisão é append-only, sem perda de precisão silenciosa; valores além do tipo da memória ficam com pendência explícita. Contrato e exemplos em [INVOICE-REVIEW](INVOICE-REVIEW.md).

GET `.../invoice-readiness` consulta finanças/pendências com Decimal string, revisões atuais e autorização dono/admin. Identifica tarefas ativas e admissões não removidas sem publicação, inclusive expiradas/falhas/canceladas. `ready_for_calculation=false` e faturas needs_review: confirmação integral e duplicidade/refaturamento ainda não implementados. Não há cálculo, parser/OCR, PDFs reais ou interface completa. Migração não mudou: 0007_invoice_publications.

## Verificações reais

- Regressão final: **230 testes aprovados, incluindo Edge** (143,57 s), com **35 casos novos**. Regressões intermediárias de 226 e 228 testes e execução focada de 34 casos também passaram. A versão final inclui lote de datas sem flush intermediário inválido e rejeição de dependências duplicadas antes da gravação.
- Casos cobrem histórico e invalidação transitiva, referências obsoletas/estrangeiras/autorreferência/ciclos, concorrência de retry e edição/remoção, rollback de valores/proveniência/validações/contadores/recibo, autorização/CSRF/admin, versão/identidade, limites Decimal, tolerância inclusiva e residual separado do total a pagar.
- Alembic current = 0007_invoice_publications (head); Alembic check sem novas operações. Sem migração ou dependência nova. compileall aprovado; uv pip check: 41 pacotes compatíveis; uv lock --check --offline aprovado com cache local.
- Primeira tentativa pytest na sandbox falhou por acesso ao diretório temporário, sem validar testes; execução autorizada fora da sandbox passou. uv inicialmente tentou cache fora do projeto, recusado; repetido com --cache-dir .uv-cache passou. Nenhum contorno de política, instalação global, administrador ou container.
- .env e alterações locais preexistentes em docs/contracts/access.md e docs/corpus/regulatory-review.md preservados e fora do envio. Nenhum dado/artefato real de corpus publicado. Edge verifica regressão de acesso web; não comprova segurança PDF, correção financeira comercial ou produção. PostgreSQL não validado.
- Envio preparado pela integração GitHub sobre árvore remota preservada, somente os 14 arquivos desta entrega. CI e SHA finais serão informados na resposta após consulta remota; este status integra o próprio commit. Nenhum critério integral adicional da seção 15 foi marcado.

## Pendências e próximo passo

Implementar confirmação versionada do mínimo crítico, duplicidade lógica/refaturamento com escolha explícita e prontidão efetiva do conjunto, inclusive mudança da unidade e admissões problemáticas. Não criar bloqueios administrativos fora do mínimo aceito nem exigir doze faturas. Depois, completar interface de leitura/conferência sem iniciar processamento pela seleção: somente “Ler fatura”. Motor econômico permanece na Fase 3.

PDFs e layouts documentais continuam desabilitados. Completar/verificar §5/§12 antes de recebimento real: confinamento sem rede/privilégios, CPU/RAM/pixels, descendentes órfãos, watchdog rígido, swap/dumps, diretório RAM quando necessário e ausência de spool no framework/proxy. Spawn sintético não comprova sandbox ou descarte seguro. Catálogo tarifário não habilita parser nem fallback ENEL.

Ressalvas da Fase 0 intactas: desconhecido não equivale a zero, hipóteses não são homologação e Verde exemplificativa não é gabarito financeiro. SMTP externo/MFA/produção/retenção continuam nas fases próprias.

## Arquivos e commit

Novos: docs/INVOICE-REVIEW.md; src/ecowatt/invoice_review.py; src/ecowatt/services/invoice_review.py; src/ecowatt/services/invoice_validation.py; tests/test_invoice_review.py.

Alterados: EcoWatt_PROJECT_SPEC.md; README.md; docs/API.md; docs/DATABASE.md; docs/INVOICE-STORAGE.md; docs/STATUS.md; docs/phases/phase-02-invoices.md; src/ecowatt/api/resources.py; src/ecowatt/schemas.py. Removidos: nenhum.

Commit desta entrega na fase-2: feat: add versioned synthetic invoice review and financial checks. SHA/CI finais informados na resposta após o envio. Nenhum merge. Arquivos locais auxiliares, .env, corpus, bancos, ambientes e caches ficam fora do envio.
