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

## Entrega atual — Fase 2, admissão sintética

Segunda entrega dividida em fatia coerente de infraestrutura, em 09/11/2026. Branch remota `fase-2` conferida no commit `aadd1d38dfc85bdd07d5ef42a29c198e3487cc31`, preservado como pai. Primeira entrega: esquema 0004, 95 testes e CI aprovada; Fase 1 segue integrada pelo PR #2. Nenhum merge nesta entrega.

Implementados: consulta JSON autenticada de suporte a distribuidora/layout; pré-condição de unidade salva; contrato imutável de inspeção e protocolo de adaptador; reserva de quantidade/bytes/páginas e capacidade global na mesma transação de TASKS. Catálogo não habilita parser: somente a fixture interna SYNTHETIC/synthetic-v1 é reconhecida. Todos os layouts documentais, inclusive ENEL, continuam bloqueados. Consulta informa necessidade de contato, sem criar um pedido ou canal fictício.

Migração aditiva `0005_invoice_admissions` guarda exclusivamente metadados/hash/versões, autoria e tombstone de remoção. Limites: 12 arquivos, 10 MB/10 páginas por arquivo, 60 MB/60 páginas acumulados; MB decimal. Quatro reservas ativas globais; um executor de admissão por vez, além da restrição TASKS de uma simulação por dono. Retry idêntico retorna a mesma tarefa; conflitos e capacidade recusam sem reserva parcial. Remoção revoga lease/libera orçamento e conserva chave antiga; reenvio explícito usa outra chave. Exclusão da simulação remove reservas e filhos na transação do tombstone/cancelamento.

Contratos, códigos e limitações em [ADMISSION](ADMISSION.md), [DATABASE](DATABASE.md) e [TASKS](TASKS.md). O contrato de inspeção não implementa resultado de extração. Não há bytes, texto bruto, PDFs ou imagens em reservas. O comando interno exige ação read_invoice; selecionar não cria trabalho. A consulta pública é somente GET, sem endpoint multipart de recebimento.

## Verificações reais

- **120 testes aprovados**, com ECOWATT_BROWSER_TESTS=1, incluindo Edge, loopback SMTP e 25 casos novos exclusivamente sintéticos. Versão final executada após incluir exclusão das reservas: 65,62 s.
- Cobertos limites por arquivo/acumulados e disputas concorrentes pela última vaga, retry concorrente, hash duplicado, executor global único, capacidade, autoria admin/titularidade, acesso cruzado, ator bloqueado, rollback da reserva/remoção/conclusão/exclusão, expiração e resultado tardio após remoção/exclusão/revisão.
- Suíte de migrações verifica upgrade limpo e preservação de raízes, downgrade/upgrade descartável, Alembic check e FKs. Migração local aplicada: alembic current = 0005_invoice_admissions (head); alembic check sem divergências. Nenhuma validação PostgreSQL.
- compileall aprovado. uv pip check: 41 pacotes compatíveis; uv lock --check --offline aprovado. Sem dependências novas. Cache uv direcionado ao workspace após bloqueio do cache padrão. Pytest exigiu execução local autorizada pela revisão automática por bloqueio de temporários no sandbox.
- Ambiente virtual existente; sem instalações globais, administrador, containers ou alteração de políticas. .env preservado e fora do envio. Nenhum dado/artefato real do corpus processado ou publicado.
- CI do novo commit deve ser consultada no GitHub; resultado local não equivale a CI aprovada. Estado final e SHA serão informados na resposta, pois este documento integra o próprio commit.

## Pendências e próximo passo

Implementar coordenador único/fila efêmera real e verificar integralmente §5/§12 antes de habilitar PDFs: ausência de spool no framework/proxy, isolamento sem rede, limites CPU/RAM/tempo/pixels, armazenamento RAM quando indispensável, descarte e observabilidade. Depois integrar adaptador/layout específico homologado e contrato de resultado normalizado, sincronização valores/proveniência, vínculo fatura/tarefa, remoção do grafo individual, revisão do conjunto e persistência por finish. Cabeçalho visual, seletor e pedido de contato continuam pendentes. Recuperação de queued sem bytes após reinício ainda precisa do coordenador real.

A reserva sintética não prova extração, segurança de PDF ou prontidão para cálculo. Não publicar faturas pelo callback desta reserva sem implementar vínculo e remoção atômica do grafo. Nenhum critério integral adicional da seção 15 foi marcado; anotado somente progresso parcial. Fase 2 permanece aberta.

Ressalvas da Fase 0 intactas: desconhecido não equivale a zero; hipóteses não são homologação; Verde exemplificativa não é gabarito financeiro. SMTP externo/MFA/produção/retenção permanecem nas fases próprias.

## Arquivos e commit

Novos: docs/ADMISSION.md; migrations/versions/0005_invoice_admissions.py; src/ecowatt/db/admissions.py; src/ecowatt/services/admission.py; tests/test_admission.py.

Alterados: EcoWatt_PROJECT_SPEC.md; README.md; docs/API.md; docs/DATABASE.md; docs/STATUS.md; docs/TASKS.md; docs/phases/phase-02-invoices.md; migrations/env.py; src/ecowatt/api/health.py; src/ecowatt/api/resources.py; src/ecowatt/schemas.py; src/ecowatt/services/simulations.py; src/ecowatt/services/tasks.py. Removidos: nenhum.

Commit na fase-2: feat: reserve synthetic invoice admission capacity transactionally. Envio limitado aos 18 arquivos acima, sobre a árvore remota; .env, corpus, bancos, caches, temporários e alterações locais preexistentes em docs/contracts/access.md e docs/corpus/regulatory-review.md ficam preservados e fora deste envio.
