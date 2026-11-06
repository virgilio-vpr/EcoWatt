# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.10; contratos mínimos v0.2.

## Direção atual

**Fase 0 concluída**, com aceite explícito do usuário desta conversa em 06/11/2026 para os contratos e o gabarito mínimo local das doze faturas. O aceite inclui desconhecidos e ressalvas documentados, sem autorizar publicação de dados reais ou homologação comercial. Não foi informado nome civil do responsável.

Escopo aceito: concentrar somente em **faturamento, informações do cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas**, conforme os quatro blocos mostrados pelo usuário. Não cadastrar exaustivamente a conta ou exigir auditoria de informações fiscais, boleto, pagamento, códigos de medidor e outros dados administrativos. A investigação ampliada anterior foi além do escopo e permanece apenas como histórico.

Fase 1 em andamento: base FastAPI, persistência SQLAlchemy/Alembic, serviços de autenticação/permissões, seed sintético e simulações/unidades implementados. Dependências somente em `.venv`, com uv.lock. Envio de e-mail e fechamento dos critérios restantes ainda pendentes; não iniciar uso com dados reais.

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

## Entrega atual — persistência e serviços da Fase 1

Ambiente confirmado: Python 3.13.14, SQLite 3.50.4, uv 0.13.7 local; adicionados SQLAlchemy 2.0.57, Alembic 1.20.1, Argon2, validação de e-mail e Jinja2, com dependências/hashes no uv.lock. Nenhuma instalação global, container ou mudança de política. Bootstrap/caches continuam conforme [SETUP](SETUP.md).

Duas migrações estáticas encadeadas: raízes empresa/distribuidora/usuário e dependentes de autenticação/simulação/auditoria. SQLite com FKs/WAL/timeout e transações explícitas; import/startup não criam esquema/contas. DecimalType usa texto em SQLite e Numeric(p,s) no dialeto PostgreSQL, rejeitando float/perda de escala. PostgreSQL não foi executado. Modelo, constraints e políticas em [DATABASE](DATABASE.md).

Cadastro/ativação/recuperação testados com adaptador de e-mail em memória; runtime desabilitado responde 503 uniforme sem fingir envio. Senhas Argon2id; sessão opaca protegida no banco, expiração absoluta/inatividade, rotação, CSRF/origem, logout/revogação e bloqueio administrativo. Admin provisionado somente por seed local explícito, sem signup privilegiado. Seed cria duas empresas/contas sintéticas e distribuidora sintética, sem tarifas/parser, preservando dados existentes.

API paginada e erros padronizados, empresa/perfil próprios, admin com dono explicitamente selecionado; simulações com dono/empresa/autores, FK composta, duas vagas únicas por dono e BEGIN IMMEDIATE. Idempotência inclui retries concorrentes. Unidade salva com revisão e endereço separado; UC/distribuidora não mudam para outra unidade. Exclusão confirmada libera vaga e impede retry/consulta/guard tardio; ainda não há jobs/faturas/relatórios para integrar ou cancelar.

Web de inspeção usa os mesmos serviços: layout, macro, parcial HTMX e CSS local mínimo, sem interface completa. HTMX 2.0.11 local com SRI conferido e licença; CSP sem eval/scripts inline. Índice local de operações substitui Swagger/CDN. Autorização também nos fragmentos.

Verificações reais: **40 testes aprovados**, Alembic check sem divergência, criação limpa, upgrade preservando empresa, downgrade/upgrade descartável, rollback/FKs, Decimal de 30 dígitos/dez casas, seed repetido, tokens/expiração/revogação, acesso cruzado JSON/HTML/HTMX, concorrência de vaga e retry. Migrações e seed executados no SQLite local ignorado; Uvicorn HTTP real com readiness, login admin/cliente, account/perfil/docs e logout, processo encerrado. Lock/pip check, compileall e wheel com templates conferidos. Workflow Windows/SQLite adicionado; aguardar resultado remoto. Sem teste visual de navegador ou e-mail real. Argon2id 64 MiB/t3/p4: mediana local hash+verificação 85,3ms (três amostras), recalibrar no host.

## Próximo passo

Fechar a Fase 1: definir/implementar meio de entrega de e-mail e consumo dos links, revisar o contrato OpenAPI/cliente HTTP e conferir os critérios ainda abertos da seção 15. Login local já funciona pela API com seed; formulários completos/visual permanecem na Fase 4. Produção exige provisionamento real, MFA, rate limit de borda, retenção/expurgo e operação; não há modo de produção nesta base.

Na Fase 2, antes de leitura/OCR, criar tabelas de faturas/filhos, integrar guard de exclusão/revisão aos jobs e provar cancelamento/ausência de recriação tardia. Não marcar esse critério integralmente apenas porque o guard está testado. Continuar com fixtures sintéticas e sem reabrir auditoria ampliada como pré-requisito.

Homologação comercial, tarifas/entradas próprias para cenários alternativos e autorização/procedimento de anonimização para fixtures públicas permanecem separados. Setembro é compatível numericamente com bandeira, sem confirmação de item. Junho não equivale a dois consumos medidos. Verde exemplificativa não é gabarito financeiro.

## Arquivos e commit

Novos: `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_roots.py`, `migrations/versions/0002_access_simulations.py`, `docs/DATABASE.md`, `.github/workflows/backend.yml`; `src/ecowatt/errors.py`, `src/ecowatt/schemas.py`, `src/ecowatt/seed.py`; `src/ecowatt/db/{base,models,session,types}.py`; `src/ecowatt/security/{__init__,passwords,tokens}.py`; `src/ecowatt/services/{__init__,auth,mail,simulations}.py`; `src/ecowatt/api/{auth,dependencies,resources}.py`; `src/ecowatt/web/routes.py`, templates de layouts/components/partials/account/simulation/docs, `static/base.css`, vendor HTMX/licença/README; `tests/{conftest,test_auth,test_database,test_simulations}.py`.

Alterados: `.env`, `.env.example`, `pyproject.toml`, `uv.lock`, `src/ecowatt/config.py`, `src/ecowatt/main.py`, `src/ecowatt/api/health.py`, `src/ecowatt/db/__init__.py`, `src/ecowatt/web/__init__.py`, `tests/test_bootstrap.py`, `README.md`, `docs/SETUP.md`, `docs/STATUS.md`, `docs/phases/phase-01-backend.md` e `EcoWatt_PROJECT_SPEC.md`. Removidos: nenhum. Dados reais, banco local, ambientes, caches e wheel fora do envio.

Commit desta entrega na fase-1: `feat: adiciona persistencia autenticacao e simulacoes locais`. Consultar histórico remoto para o SHA; este status integra o próprio commit. Main preservada; integração por PR após revisão/fechamento da fase.
