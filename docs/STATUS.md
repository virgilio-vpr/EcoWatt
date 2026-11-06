# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.10; contratos mínimos v0.2.

## Direção atual

**Fase 0 concluída**, com aceite explícito do usuário desta conversa em 06/11/2026 para os contratos e o gabarito mínimo local das doze faturas. O aceite inclui desconhecidos e ressalvas documentados, sem autorizar publicação de dados reais ou homologação comercial. Não foi informado nome civil do responsável.

Escopo aceito: concentrar somente em **faturamento, informações do cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas**, conforme os quatro blocos mostrados pelo usuário. Não cadastrar exaustivamente a conta ou exigir auditoria de informações fiscais, boleto, pagamento, códigos de medidor e outros dados administrativos. A investigação ampliada anterior foi além do escopo e permanece apenas como histórico.

Fase 1 em andamento: persistência, autenticação/permissões, seed, simulações/unidades, adaptador SMTP e páginas mínimas de acesso implementados. Dependências somente em `.venv`, com uv.lock. SMTP desabilitado por padrão; provedor externo não homologado. Revisão final dos critérios ainda pendente; não iniciar uso com dados reais.

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

## Entrega atual — SMTP e consumo dos links

Ambiente Python 3.13.14/SQLite 3.50.4/uv 0.13.7 confirmado. SMTP usa biblioteca padrão, com STARTTLS/SSL e verificação normal de certificado; sem TLS só em loopback numérico e sem credenciais. Configuração tipada, timeout limitado e diagnósticos sanitizados. `.env` permanece disabled e sem segredos. Nenhuma mensagem externa enviada. Playwright 1.64.1 instalado apenas no `.venv` dev, usando Edge já instalado, sem download de navegador, instalação global ou alteração de políticas.

Persistência/constraints anteriores preservadas, sem nova migração: SQLite FKs/WAL, DecimalType, transações/cota/idempotência e seed sintético. Cadastro/reenvio fazem commit antes de agendar entrega como tarefa da resposta HTTP. SMTP não mantém lock SQLite nem retarda a resposta pela latência do provedor. Falha/aceitação incerta invalida apenas o token daquele envio; conta pendente permite reenvio e 202 continua neutro. Não há fila persistente: interrupção pode exigir reenvio. Ver [EMAIL](EMAIL.md) e [DATABASE](DATABASE.md).

Formulários mínimos `/auth/register`, `/auth/login`, `/auth/forgot-password`, `/auth/resend-activation`, `/auth/activation` e `/auth/reset` chamam a API JSON existente. Tokens de link são lidos do fragmento, retirados da URL/histórico corrente e mantidos só em memória; GET não consome. Reabertura na mesma página tratada. Não há inbox pública, tokens em HTML/localStorage/logs ou consumo automático. Senhas com política/dupla confirmação e mostrar/ocultar; sem antecipar interface completa.

Autorização JSON/HTML/HTMX, CSRF/origem, expiração/rotação/revogação de sessões e proteção dos tokens anteriores continuam válidos. Admin/cliente sintéticos permanecem provisionados por seed explícito. Cota continua duas vagas por dono; UC/distribuidora não se tornam outra unidade dentro da mesma simulação. Não há OCR, cálculos, jobs ou relatórios implementados.

Limites preservados: banco e artefatos locais não enviados; nenhuma mudança nos dados reais/contratos da Fase 0. Adaptador SMTP implementado não comprova entregabilidade com provedor externo; produção, MFA, rate limit de borda e retenção/expurgo continuam em fase própria.

Verificações reais: **54 testes aprovados** com navegador explicitamente habilitado, incluindo servidor SMTP de loopback sem encaminhamento, falha neutra/reenvio, rede fora da transação e HTTP 202 antes de terminar entrega. TLS/SSL/autenticação/recusa de downgrade testados com doubles. Edge headless + Uvicorn: cadastro→SMTP sintético→ativação→uso repetido recusado→login→recuperação→troca→revogação→novo login; sem erros JS ou tokens em URLs de requests. Regressões SQLite/Decimal/cota/permissões passaram. Lock/pip check, Alembic check sem divergência e compileall conferidos. CI anterior [aprovada](https://github.com/virgilio-vpr/EcoWatt/actions/runs/42282129451); workflow atualizado com teste explícito de navegador, resultado do novo commit a conferir.

## Próximo passo

Próxima entrega: revisão final do contrato OpenAPI/cliente HTTP, dos critérios da seção 15 e da CI para fechar a Fase 1 local. SMTP externo/remetente/entregabilidade precisam de configuração e homologação próprias antes de uso real; não inventar provedor ou credenciais. Interface completa/visual ficam na Fase 4. Produção exige provisionamento real, MFA, rate limit de borda e retenção/expurgo; runtime continua sem modo de produção.

Na Fase 2, antes de leitura/OCR, criar tabelas de faturas/filhos, integrar guard de exclusão/revisão aos jobs e provar cancelamento/ausência de recriação tardia. Não marcar esse critério integralmente apenas porque o guard está testado. Continuar com fixtures sintéticas e sem reabrir auditoria ampliada como pré-requisito.

Homologação comercial, tarifas/entradas próprias para cenários alternativos e autorização/procedimento de anonimização para fixtures públicas permanecem separados. Setembro é compatível numericamente com bandeira, sem confirmação de item. Junho não equivale a dois consumos medidos. Verde exemplificativa não é gabarito financeiro.

## Arquivos e commit

Novos: `docs/EMAIL.md`, `src/ecowatt/web/templates/auth/access.html`, `src/ecowatt/web/static/auth.js`, `tests/test_mail_delivery.py`, `tests/test_auth_browser.py`.

Alterados: `.env`, `.env.example`, `pyproject.toml`, `uv.lock`, `.github/workflows/backend.yml`, `src/ecowatt/config.py`, `src/ecowatt/main.py`, `src/ecowatt/api/auth.py`, `src/ecowatt/services/auth.py`, `src/ecowatt/services/mail.py`, `src/ecowatt/web/routes.py`, `src/ecowatt/web/templates/layouts/base.html`, `src/ecowatt/web/static/base.css`, `README.md`, `docs/SETUP.md`, `docs/STATUS.md`, `docs/phases/phase-01-backend.md` e `EcoWatt_PROJECT_SPEC.md`. Removidos: nenhum. Dados reais, banco local, ambientes, caches e wheel fora do envio.

Commit desta entrega na fase-1: `feat: integra SMTP e consumo seguro de links de acesso`. Consultar histórico remoto para o SHA; este status integra o próprio commit. Main preservada; integração por PR após revisão/fechamento da fase.
