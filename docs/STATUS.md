# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.10; contratos mínimos v0.2.

## Direção atual

**Fase 0 concluída**, com aceite explícito do usuário desta conversa em 06/11/2026 para os contratos e o gabarito mínimo local das doze faturas. O aceite inclui desconhecidos e ressalvas documentados, sem autorizar publicação de dados reais ou homologação comercial. Não foi informado nome civil do responsável.

Escopo aceito: concentrar somente em **faturamento, informações do cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas**, conforme os quatro blocos mostrados pelo usuário. Não cadastrar exaustivamente a conta ou exigir auditoria de informações fiscais, boleto, pagamento, códigos de medidor e outros dados administrativos. A investigação ampliada anterior foi além do escopo e permanece apenas como histórico.

**Fase 1 concluída para desenvolvimento local**, conforme pedido do usuário de encerrar a fase. O último critério foi implementado com controle de tarefas, cancelamento transacional e rejeição de persistência tardia. Integração pelo [PR #2](https://github.com/virgilio-vpr/EcoWatt/pull/2). Dependências somente em `.venv`, com uv.lock; sem OCR/cálculos ou produção habilitada. SMTP desabilitado por padrão e provedor externo não homologado; não usar dados reais.

## Regras que permanecem

- Preço unitário cheio com impostos incorporados; sem análise separada de PIS/COFINS/ICMS. Ociosidade LEI ESTADUAL = preço da demanda contratada × 0,82 em ponta/fora de ponta/única. Tolerância de até BRL 0.99 inclusive por item. Quatro parcelas somente monetárias mantêm quantidade/preço desconhecidos.
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

Por orientação do usuário, o encerramento é registrado na `fase-0` e integrado à `main` por merge. A branch `fase-1` deve partir da `main` após esse merge; as próximas entregas serão commitadas nela e integradas por pull request. Operações realizadas diretamente pela integração GitHub, sem Git local.

## Entrega atual — encerramento da Fase 1

Ambiente Python 3.13.14/SQLite 3.50.4/uv 0.13.7, sem novas dependências, instalações globais, containers ou alteração de políticas. Migração aditiva `0003_simulation_tasks` aplicada ao SQLite local; readiness atualizada. Configuração local do usuário não foi alterada nem incluída nesta entrega. Nenhum e-mail externo enviado ou documento real processado.

Novo [controle de tarefas](TASKS.md): reserva vinculada à simulação/revisão/ator, claim exclusivo com executor e lease aleatória protegida por hash, heartbeat, validade e expiração explícita. Tabela armazena só metadados, sem payloads/documentos/texto/resultados. Uma simulação ativa por dono no protocolo e uma tarefa em execução por simulação; nenhuma fila automática iniciada no startup.

Exclusão pela API cancela tarefas queued/running, revoga leases, incrementa revisão e libera slot na mesma transação. Nova revisão da unidade também cancela operações antigas. Finish abre transação de escrita nova/curta, revalida ator/revisão/tombstone/lease e somente então chama persistência estruturada; resultado e conclusão são atômicos. Trabalho pesado não ocorre dentro dessa transação. Expiração afeta apenas leases vencidas, nunca tarefas vivas no startup.

Garantia verificada com executor sintético concorrente: termina depois da exclusão e recebe recusa antes do callback gravar; tarefa em fila não pode ser assumida após cancelar, heartbeat antigo é recusado e a vaga já está disponível. Rollback da exclusão restaura slot/estado/lease em conjunto. Resultado que confirma antes da exclusão fica sujeito à revogação normal de acesso quando ela ocorre. Não há executor real de OCR/cálculo nem endpoint público de tarefas nesta fase.

Seção 15 da SPEC: último critério e Fase 1 marcados após implementação e testes, sem reclassificar pendência como atendida por documentação. Regras anteriores — HTTP/CSRF, tokens revogáveis, cota, Decimal, titularidade e seed — preservadas. Ressalvas da Fase 0 permanecem intactas. Catálogo é sintético; SMTP externo, produção/MFA, retenção/expurgo e homologação comercial continuam nas fases correspondentes.

Verificações reais: **68 testes aprovados** com os dois testes de navegador habilitados; incluem seis casos novos de ciclo/cancelamento, executor tardio em thread, rollback, disputa de claim, revisão, autorização e expiração. Regressões completas de HTTP/Edge, SMTP sintético, migrações/seed/Decimal/cota/permissões passaram. Migração local aplicada, Alembic check sem divergência, lock/pip check, compileall e wheel conferidos. A integração do PR exige CI do commit de fechamento aprovada; resultado remoto disponível no PR/histórico. Não houve validação PostgreSQL, SMTP externo ou interface completa.

## Próximo passo

Primeira entrega da Fase 2: modelos/migrações de faturas/itens/medições/proveniência/estado conforme [plano](phases/phase-02-invoices.md), antes de parser/OCR. Ao criar o coordenador real, usar o protocolo TASKS existente, observar cancelamento para encerrar processos e integrar os novos filhos à exclusão. SMTP externo/remetente/entregabilidade exigem homologação própria; não inventar credenciais/provedor. Interface completa/visual ficam na Fase 4; produção segue em fase própria.

Reexecutar os testes de cancelamento/resultado tardio com os adaptadores e tabelas reais de cada fase; isso é regressão da garantia implementada, não pendência de conclusão da Fase 1. Limites de admissão, isolamento/encerramento de processos e política de temporários pertencem ao processamento da Fase 2. Continuar com fixtures sintéticas e sem reabrir auditoria ampliada como pré-requisito.

Homologação comercial, tarifas/entradas próprias para cenários alternativos e autorização/procedimento de anonimização para fixtures públicas permanecem separados. Setembro é compatível numericamente com bandeira, sem confirmação de item. Junho não equivale a dois consumos medidos. Verde exemplificativa não é gabarito financeiro.

## Arquivos e commit

Novos: `migrations/versions/0003_simulation_tasks.py`, `src/ecowatt/services/tasks.py`, `tests/test_task_lifecycle.py`, `docs/TASKS.md`.

Alterados: `src/ecowatt/db/models.py`, `src/ecowatt/services/simulations.py`, `src/ecowatt/api/health.py`, `README.md`, `docs/SETUP.md`, `docs/DATABASE.md`, `docs/API.md`, `docs/STATUS.md`, `docs/phases/phase-01-backend.md`, `EcoWatt_PROJECT_SPEC.md`. Removidos: nenhum. `.env` local, dados reais, banco, ambientes, caches e wheel fora do envio.

Commit de encerramento na fase-1: `feat: conclui fase 1 com cancelamento transacional de tarefas`. Integração pelo PR #2 após CI aprovada; SHA do commit/merge no histórico remoto e na resposta da entrega. Este status integra o próprio commit.
