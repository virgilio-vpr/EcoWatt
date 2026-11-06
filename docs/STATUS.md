# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.10; contratos mínimos v0.2.

## Direção atual

**Fase 0 concluída**, com aceite explícito do usuário desta conversa em 06/11/2026 para os contratos e o gabarito mínimo local das doze faturas. O aceite inclui desconhecidos e ressalvas documentados, sem autorizar publicação de dados reais ou homologação comercial. Não foi informado nome civil do responsável.

Escopo aceito: concentrar somente em **faturamento, informações do cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas**, conforme os quatro blocos mostrados pelo usuário. Não cadastrar exaustivamente a conta ou exigir auditoria de informações fiscais, boleto, pagamento, códigos de medidor e outros dados administrativos. A investigação ampliada anterior foi além do escopo e permanece apenas como histórico.

Base local da Fase 1 validada, incluindo revisão do contrato/cliente HTTP. Persistência, autenticação/permissões, seed, simulações/unidades e SMTP sintético disponíveis. Dependências somente em `.venv`, com uv.lock. SMTP desabilitado e provedor externo não homologado. O critério de exclusão/cancelamento integrado aos futuros jobs permanece aberto para a Fase 2; não declarar aceite integral da fase ou usar dados reais.

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

## Entrega atual — revisão HTTP e critérios locais

Ambiente Python 3.13.14/SQLite 3.50.4/uv 0.13.7; sem novas dependências, migrações, instalações globais, containers ou alterações de política. SMTP continua disabled por padrão, sem segredos ou envio externo. Playwright usa somente o Edge já instalado.

OpenAPI revisado: respostas tipadas para todas as operações JSON, enums/limites de senha/token, confirmação de exclusão boolean estrita, cookie de sessão e CSRF como requisitos conjuntos em comandos privados, Origin e X-Request-ID documentados. Header Allow preservado no 405. Índice HTML agora usa os paths do schema; a lista anterior ficava vazia com os routers incluídos do FastAPI instalado. Uso/mapeamento semântico do pipeline em [API](API.md), sem antecipar endpoints de faturas/cálculos.

Cliente HTTP local compartilhado pelos formulários: API da mesma origem, cookies/CSRF, timeout, redirects recusados, erro estruturado/correlação e 204 sem corpo. Não há retry automático de escrita; a repetição exige conferir resultado e preservar a chave. Testado no Edge com login, paginação, erro 422, replay idempotente, exclusão e falha de rede sem retry. Links/tokens e fluxo SMTP anteriores preservados, conforme [EMAIL](EMAIL.md).

Guard de simulação recarrega tombstone/revisão com populate_existing, sem confiar no cache ORM. Caso real de teste: sessão carrega rascunho, outra requisição exclui, sessão antiga tenta persistir processamento e é recusada sem reviver o registro ou ocupar slot. Futuros jobs ainda precisam abrir transação curta/nova e usar esse guard antes de persistir. Não há implementação de jobs/cancelamento nesta entrega.

Checklist oficial: contrato HTTP e critérios técnicos da base local marcados somente após verificações; o item de exclusão integrada aos jobs e a Fase 1 como um todo permanecem abertos. Catálogo é sintético, não tarifa/parser homologado. Ressalvas da Fase 0 acima permanecem; sem alterações nos materiais reais. Produção, MFA, retenção/expurgo e homologação SMTP continuam separados.

Verificações reais: **62 testes aprovados** com os dois testes de navegador habilitados. Contrato/erros/headers/paginação/204, cliente HTTP, guard com cache antigo e regressões completas de migrações/seed/Decimal/concorrência/permissões/SMTP passaram. Alembic check sem divergência, lock/pip check, compileall e wheel conferidos. CI da entrega SMTP [aprovada com navegador](https://github.com/virgilio-vpr/EcoWatt/actions/runs/42285751117); conferir o resultado do novo commit. Nenhuma homologação PostgreSQL, SMTP externo ou interface completa alegada.

## Próximo passo

Próxima implementação: primeira entrega da Fase 2, modelos/migrações de faturas/itens/medições/proveniência/estado conforme [plano](phases/phase-02-invoices.md), antes de instalar ou implementar parser/OCR. A base local está verificada; preservar o critério integrado de exclusão como pendência explícita até testar jobs reais. SMTP externo/remetente/entregabilidade exigem homologação própria; não inventar credenciais/provedor. Interface completa/visual ficam na Fase 4; produção segue em fase própria.

Na Fase 2, antes de leitura/OCR, criar tabelas de faturas/filhos, integrar guard de exclusão/revisão aos jobs e provar cancelamento/ausência de recriação tardia. Não marcar esse critério integralmente apenas porque o guard está testado. Continuar com fixtures sintéticas e sem reabrir auditoria ampliada como pré-requisito.

Homologação comercial, tarifas/entradas próprias para cenários alternativos e autorização/procedimento de anonimização para fixtures públicas permanecem separados. Setembro é compatível numericamente com bandeira, sem confirmação de item. Junho não equivale a dois consumos medidos. Verde exemplificativa não é gabarito financeiro.

## Arquivos e commit

Novos: `docs/API.md`, `src/ecowatt/api/openapi.py`, `src/ecowatt/web/static/api-client.js`, `tests/test_api_contract.py`.

Alterados: `src/ecowatt/schemas.py`, `src/ecowatt/main.py`, `src/ecowatt/api/auth.py`, `src/ecowatt/api/resources.py`, `src/ecowatt/services/simulations.py`, `src/ecowatt/web/routes.py`, `src/ecowatt/web/templates/auth/access.html`, `src/ecowatt/web/static/auth.js`, `tests/test_auth_browser.py`, `tests/test_simulations.py`, `README.md`, `docs/SETUP.md`, `docs/DATABASE.md`, `docs/STATUS.md`, `docs/phases/phase-01-backend.md`, `EcoWatt_PROJECT_SPEC.md`. Removidos: nenhum. Dados reais, banco local, ambientes, caches e wheel fora do envio.

Commit desta entrega na fase-1: `fix: revisa contrato HTTP e protecao de simulacoes excluidas`. Consultar histórico remoto para o SHA; este status integra o próprio commit. Main preservada; integração por PR conforme fluxo do projeto.
