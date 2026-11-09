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

## Entrega atual — Fase 2, coordenador efêmero sintético

Terceira entrega em 09/11/2026, sobre `03ff3a4c3a7a256002637d268d7d1c557beef036` na branch `fase-2`, conferida remotamente. Esse commit anterior tem CI aprovada. Mantidos esquema 0004, admissão 0005 e todos os contratos de titularidade/autoria, Decimal, revisão e cancelamento. Nenhum merge solicitado.

Implementados: liderança única com token protegido e geração crescente; fila RAM limitada; execução sequencial por subprocesso spawn; heartbeat, timeout de arquivo/lote; interrupção controlada, limpeza de buffers/pipes e recolhimento do filho; recuperação de queued sem conteúdo e running com lease vencida. Claim/heartbeat/finish revalidam a geração do coordenador. Aquisição concorrente admite um líder; takeover não encerra prematuramente tarefas com lease ainda viva e impede gravação pela geração antiga.

Migração `0006_coordinator_lease`: singleton de liderança e geração nullable nas reservas. Reservas anteriores com geração NULL são preservadas. Entrada na fila e reserva SQL desfazem juntas em falha controlada; falha abrupta entre RAM/commit exige reenvio, com motivo content_lost. Retry nunca repõe silenciosamente bytes de tarefa terminal. Limites: quatro entradas/40 MB retidos, 180 s por arquivo e 600 s por lote ativo, além das cotas acumuladas anteriores.

A entrada aceita exclusivamente Sample, que produz bytes inventados; não aceita PDF nem bytes arbitrários. O filho devolve JSON de até 1.024 bytes, schema fechado e tipos estritos, sem desserializar pickle de retorno. Receipt é recibo técnico versionado, não extração faturável. O coordenador não é iniciado automaticamente pela web, não é endpoint público e não publica faturas. Contratos completos e barreiras em [COORDINATOR](COORDINATOR.md), [ADMISSION](ADMISSION.md), [TASKS](TASKS.md) e [DATABASE](DATABASE.md).

## Verificações reais

- **152 casos locais aprovados**: suíte completa com 150 testes, incluindo Edge (88,81 s), e dois casos adicionais aprovados separadamente após sua inclusão (rollback da eleição e downgrade/upgrade com reserva preenchida). São 32 casos novos do coordenador.
- Subprocessos reais com fixtures inventadas: sucesso, erro, timeout, falha de criação do filho, rollback do callback, cancelamento por remoção/exclusão/revisão/bloqueio, shutdown, takeover, limpeza de buffers e ausência de filhos novos vivos após conclusão controlada. Testadas eleição concorrente, token/geração, retry, capacidade/rollback RAM+SQL, fencing e recuperação seletiva.
- Escrita SQLite independente confirmou enquanto o filho trabalhava, verificando que a espera não mantém transação aberta. IPC rejeita campos extras, versões/tipos inválidos e não recebe texto bruto.
- Migração local aplicada; alembic current = 0006_coordinator_lease (head), alembic check sem divergências. Suíte cobre upgrade limpo/preservação de raízes, downgrade/upgrade descartável e FKs; teste adicional preserva reservas na ida a 0005 e volta, com geração restaurada como NULL.
- compileall aprovado; uv pip check: 41 pacotes compatíveis; uv lock --check --offline aprovado. Sem instalação ou mudança de dependências. Testes com subprocessos/temporários rodaram localmente, autorizados pela revisão automática, no ambiente virtual existente.
- .env preservado; sem administrador, containers ou contorno de políticas. Nenhum PDF, imagem, texto bruto de fatura ou artefato real do corpus recebido/processado/publicado. PostgreSQL não validado.
- CI e SHA desta entrega serão informados na resposta após consulta remota. Este status integra o próprio commit; resultado local não é substituto da CI.

## Pendências e próximo passo

PDFs reais continuam desabilitados e nenhum layout documental está homologado. Completar/verificar barreiras §5/§12: confinamento sem rede/privilégios, CPU/RAM/pixels, watchdog rígido, contenção de descendentes após morte abrupta do pai, swap/dumps, diretório RAM se necessário e ausência de spool no framework/proxy. Processo separado não é sandbox; o spawn sintético herda o ambiente. A lease impede persistência antiga, mas não garante conter um filho órfão pelo SO. O limite de 40 MB conta buffers retidos, não RAM total, serialização ou cópias de IPC.

Depois, integrar inspeção e adaptador específico homologado, resultado normalizado com Decimal/proveniência sincronizada, vínculo fatura/tarefa, persistência/remoção do grafo e revisão do conjunto. Cabeçalho visual/seletor, contato e fluxo de Ler fatura seguem pendentes. Não publicar faturas no callback de Receipt.

Nenhum novo critério integral da seção 15 foi marcado; atualizado somente progresso parcial. Fase 2 permanece aberta. Ressalvas da Fase 0 intactas: desconhecido não equivale a zero, hipóteses não são homologação e Verde exemplificativa não é gabarito financeiro. SMTP externo/MFA/produção/retenção seguem nas fases próprias.

## Arquivos e commit

Novos: docs/COORDINATOR.md; migrations/versions/0006_coordinator_lease.py; src/ecowatt/db/coordinator.py; src/ecowatt/services/leadership.py; src/ecowatt/services/coordinator.py; src/ecowatt/services/synthetic_worker.py; tests/test_coordinator.py.

Alterados: EcoWatt_PROJECT_SPEC.md; README.md; docs/ADMISSION.md; docs/DATABASE.md; docs/STATUS.md; docs/TASKS.md; docs/phases/phase-02-invoices.md; migrations/env.py; src/ecowatt/api/health.py; src/ecowatt/db/admissions.py; src/ecowatt/services/admission.py; src/ecowatt/services/tasks.py. Removidos: nenhum.

Commit na fase-2: feat: coordinate ephemeral synthetic jobs with leader fencing. Envio somente dos 19 arquivos desta entrega, sobre árvore remota preservada. Alterações locais preexistentes em docs/contracts/access.md e docs/corpus/regulatory-review.md ficam intactas e fora do envio, assim como .env, corpus, bancos, ambientes, caches e temporários.
