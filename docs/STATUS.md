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

## Entrega atual — Fase 2, modelos e migrações

Primeira entrega implementada em 09/11/2026 sobre a branch fase-2, preservando o commit documental `03a08016c1c75bc30050f48340719267fcb97268` posterior ao merge da Fase 1. Nenhum merge novo solicitado.

Migração aditiva `0004_invoices`: faturas, medições por posto, itens, proveniência versionada, dependências de campos, validações e evidências de mercado. Cabeçalho/identidade/ciclo/classificação em colunas; TOTAL do quadro separado do total a pagar. Contratação, demanda medida e faturada independentes, inclusive Verde com contratação única e medições por posto. Mercado/cobertura/sugestão/evidências preservados por ciclo, sem inferir ACL por ausência parcial. Sem documentos, imagens, texto integral ou payload livre nas novas tabelas.

DecimalType preservado: quantidades/valores (30,10), preços/validações (38,18), FP (20,16), região (20,10); excedentes rejeitados sem arredondamento implícito. Ausentes são NULL e têm estado por campo na proveniência. Zero confirmado exige zero e cobertura completa; estimativa exige hipótese. Correções têm versões/ator/motivo e entradas de regras referenciam versões de campos. Limites e obrigações do futuro serviço em [DATABASE](DATABASE.md): esquema não sincroniza automaticamente coluna/proveniência nem valida sozinho prontidão.

Consulta interna require_invoice usa autorização da simulação, revisão, tombstone e vínculo. Dono/empresa continuam no pai, autoria da fatura separada. Exclusão remove itens e faturas/filhos na mesma transação que cancela tarefas, incrementa revisão e libera slot. Testes usam finish existente para gravar registros reais; falha após flush de todos os filhos não deixa órfãos, e resultado tardio após exclusão/revisão não grava. Detalhes em [TASKS](TASKS.md).

Seção 15: marcado somente o critério de criação/revisão das tabelas antes da extração integrada. Fase 2 permanece aberta. Não foram antecipados parser/OCR, cálculo, interface completa, admissão, idempotência de upload ou revisão operacional. Unique por hash não substitui resolução futura de duplicatas lógicas/refaturamento.

## Verificações reais

- **95 testes aprovados**, com ECOWATT_BROWSER_TESTS=1: 68 anteriores e 27 novos casos sintéticos, incluindo Edge, SMTP em loopback, Decimal, permissões, cota, revisões, exclusão, rollback e executor em thread.
- Migração 0004 aplicada ao SQLite local; alembic current confirma head e alembic check sem divergência. Bancos descartáveis cobrem upgrade limpo, preservação dos pais, downgrade/upgrade com filhos e PRAGMA foreign_key_check.
- compileall aprovado; uv pip check: 41 pacotes compatíveis; uv lock --check --offline aprovado. Nenhuma dependência instalada ou alterada. Execução inicial no sandbox falhou por acesso aos temporários do pytest; execução local autorizada pela revisão automática passou. Cache uv direcionado ao workspace após negativa de acesso ao cache padrão.
- Ambiente virtual existente, sem instalações globais, administrador, containers ou mudança de políticas. .env preservado e excluído do envio. Nenhum PDF/corpus real processado/publicado. PostgreSQL não validado. CI deste novo commit deve ser consultada no histórico remoto; resultado local não equivale a CI aprovada.

## Próximo passo

Segunda entrega da Fase 2: admissão condicionada à unidade salva e suporte explícito a distribuidora/layout, com contrato do coordenador/adaptador, limites acumulados e processamento fora da transação, conforme [plano](phases/phase-02-invoices.md). Integrar persistência/revisão ao protocolo TASKS e às tabelas novas antes de declarar extração pronta. Regressões de cancelamento continuam obrigatórias com o adaptador real. Não presumir homologação de layout, tarifa ou fórmula tributária.

Fase 1 segue concluída (68 testes e CI aprovada no PR #2); SMTP externo/remetente/entregabilidade, MFA/produção e retenção têm homologação/fases próprias. Ressalvas da Fase 0 intactas: desconhecido não equivale a zero; hipótese de setembro não é cobrança observada; junho não equivale a dois consumos medidos; Verde exemplificativa não é gabarito financeiro.

## Arquivos e commit

Novos: src/ecowatt/db/invoices.py, src/ecowatt/services/invoices.py, migrations/versions/0004_invoices.py, tests/test_invoices.py. Alterados: src/ecowatt/services/simulations.py, src/ecowatt/api/health.py, migrations/env.py, EcoWatt_PROJECT_SPEC.md, docs/DATABASE.md, docs/TASKS.md, docs/phases/phase-02-invoices.md, README.md e este status. Removidos: nenhum. Banco, temporários, caches, ambiente e artefatos reais fora do envio.

Commit na fase-2: feat: add invoice schema and transactional lifecycle integration. SHA e confirmação de envio na resposta/histórico remoto; este status integra o próprio commit.
