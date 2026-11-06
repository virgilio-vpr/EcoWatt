# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.10; contratos mínimos v0.2.

## Direção atual

**Fase 0 concluída**, com aceite explícito do usuário desta conversa em 06/11/2026 para os contratos e o gabarito mínimo local das doze faturas. O aceite inclui desconhecidos e ressalvas documentados, sem autorizar publicação de dados reais ou homologação comercial. Não foi informado nome civil do responsável.

Escopo aceito: concentrar somente em **faturamento, informações do cliente/UC, classificação/tipo de fornecimento, datas gerais de leitura e demandas contratadas**, conforme os quatro blocos mostrados pelo usuário. Não cadastrar exaustivamente a conta ou exigir auditoria de informações fiscais, boleto, pagamento, códigos de medidor e outros dados administrativos. A investigação ampliada anterior foi além do escopo e permanece apenas como histórico.

Fase 1 iniciada: primeira entrega da base FastAPI e configuração tipada concluída. Dependências instaladas somente em `.venv`, com pyproject e uv.lock. Modelos, migrações, autenticação e seed ainda pendentes.

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

## Entrega atual — base local da Fase 1

Ambiente: Windows, Python 3.13.14, SQLite 3.50.4 e uv 0.13.7 local. FastAPI 0.162.0, Pydantic Settings 2.16.2 e Uvicorn 0.54.0; árvore fixada com hashes no uv.lock. API JSON em `/api/v1`, factory sem escrita no import/startup e pacotes db/web reservados. Configuração lê `.env`/ambiente, sem caminhos absolutos, segredos reais ou contas. Instruções e limitações em [SETUP](SETUP.md).

Executados: lock --check, pip check, seis testes aprovados, compileall e subida real Uvicorn em loopback, health/OpenAPI HTTP conferidos, processo encerrado. Bootstrap ensurepip falhou; instalação pelo pip existente direcionada ao `.venv` resolveu. Caches/temporários exigiram execução fora do sandbox, sem administrador ou instalações globais. Nenhum container, OCR, motor ou documento real usado.

SQLAlchemy 2/Alembic, WAL/FKs, DecimalType, readiness do banco, erros de domínio, autenticação, seed e web/HTMX ainda não implementados. Não declarar a Fase 1 concluída. Regras e ressalvas da Fase 0 preservadas.

## Próximo passo

Executar a entrega 2 do [plano](phases/phase-01-backend.md): SQLAlchemy 2/Alembic, modelos raiz e migrações ordenadas, SQLite com WAL/FKs e Decimal sem float, criação limpa e upgrade. Depois autenticação/permissões e seed. Usar dados sintéticos; não reabrir auditoria ampliada como pré-requisito.

Homologação comercial, tarifas/entradas próprias para cenários alternativos e autorização/procedimento de anonimização para fixtures públicas permanecem separados. Setembro é compatível numericamente com bandeira, sem confirmação de item. Junho não equivale a dois consumos medidos. Verde exemplificativa não é gabarito financeiro.

## Arquivos e commit

Novos: `pyproject.toml`, `uv.lock`, `.python-version`, `.env`, `.env.example`, `src/ecowatt/__init__.py`, `src/ecowatt/config.py`, `src/ecowatt/main.py`, `src/ecowatt/api/__init__.py`, `src/ecowatt/api/health.py`, `src/ecowatt/db/__init__.py`, `src/ecowatt/web/__init__.py`, `tests/test_bootstrap.py` e `docs/SETUP.md`. Alterados: `.gitignore`, `README.md`, `docs/STATUS.md`. Removidos: nenhum. Dados reais e artefatos locais ignorados fora do envio. Nenhum item amplo da SPEC marcado nesta entrega parcial.

Commit desta entrega na fase-1: `feat: inicia base FastAPI e ambiente local reproduzivel`. Consultar histórico remoto para o SHA; este status integra o próprio commit. Main permanece no merge da Fase 0; integração futura por PR.
