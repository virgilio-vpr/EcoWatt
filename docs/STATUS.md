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

## Entrega atual — escopo de comparação Azul/Verde e tarifas

Solicitação de 09/11/2026 incorporada à SPEC §§4.2, 7.2–7.3, 8.5–8.6, 9, 15 e 16 e aos contratos/planos das Fases 2–4. Demandas medidas de ponta/fora de ponta do quadro de medição Azul e Verde serão extraídas sem confundir contratação única com ausência de medições. Preços faltantes de qualquer componente simulável serão resolvidos no catálogo ANEEL, com formação de preço cheio baseada em incidências/alíquotas aplicáveis e documentadas. Não reaplicar impostos ao preço já cheio nem inventar parâmetros.

Referência dos cenários: maior tarifa unitária elegível por componente/posto; se a migração ao ACL ocorrer dentro da série, usar o trecho anterior. Se todo o período estiver no ACL, usar o maior preço do período nos componentes suportados, sem inventar energia do fornecedor ou alegar conta cativa completa. Histórico preservado; C0 e alternativas reprecificados em base equivalente. Máximo não significa necessariamente último mês. Mercado incerto exige revisão. Fonte, recorte, exclusões e formação do preço ficam no snapshot/memória.

No cabeçalho da etapa de anexação/leitura, identificar distribuidora/layout e oferecer contato explícito para não suportados (por exemplo, CPFL, EDP, Elektro); ENEL é a família inicial, sem homologação automática de todos os layouts. Pedido de contato não envia mensagem nem retém documentos. Suporte ao catálogo tarifário não habilita parser.

Verificações desta entrega: revisão cruzada de requisitos/contratos/planos, links locais e preservação dos critérios já concluídos da seção 15. A fonte oficial ANEEL sobre limites dos preços publicados foi consultada e referenciada; nenhuma fórmula tributária ou alíquota foi homologada. As imagens anexadas foram usadas apenas como evidência estrutural de medições por posto; nenhum dado identificável foi copiado para o repositório. O acesso ao PDF de exemplo no caminho externo F: foi negado, portanto seu conteúdo/marco de migração não foi conferido. Não houve extração de PDF, execução da aplicação, instalação, migração nem novos testes do motor; alteração exclusivamente documental. Novos critérios permanecem desmarcados.

## Última implementação — encerramento da Fase 1

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

Alterados nesta entrega documental: `EcoWatt_PROJECT_SPEC.md`, `docs/contracts/invoice-data.md`, `docs/contracts/pipeline.md`, `docs/phases/phase-02-invoices.md`, `docs/phases/phase-03-calculation.md`, `docs/phases/phase-04-reports-web.md`, `docs/STATUS.md`. Novos/removidos: nenhum. `.env`, código, banco e artefatos locais fora do envio.

Commit na `fase-2`: `docs: define comparacao Azul Verde e referencias tarifarias ACL`. SHA e confirmação de envio na resposta da entrega/histórico remoto; este status integra o próprio commit. O próximo trabalho de implementação continua sendo a primeira entrega da Fase 2, agora considerando os campos/dependências atualizados, sem antecipar o motor da Fase 3.
