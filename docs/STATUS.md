# Estado do EcoWatt

Atualizado em 10/11/2026. Referência: SPEC versão 3.11; gabarito mínimo aceito v0.2, com extensão documental de escopo para as próximas fases.

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

## Entrega atual — Fase 2, confirmação e escolha do conjunto

Sexta entrega em 09/11/2026 sobre `51abba5c23afb87a3422008c8ec94b8c57225caf`, remoto fase-2 conferido. A quinta entrega teve 230 testes/CI aprovados ([execução 42650424221](https://github.com/virgilio-vpr/EcoWatt/actions/runs/42650424221)). Nenhum merge. Admissão, coordenador e publicação permanecem exclusivamente sintéticos, com os contratos de [ADMISSION](ADMISSION.md), [COORDINATOR](COORDINATOR.md), [TASKS](TASKS.md), [INVOICE-STORAGE](INVOICE-STORAGE.md) e [INVOICE-REVIEW](INVOICE-REVIEW.md).

Implementados POST de confirmação por fatura, POST de escolha do conjunto e GET paginado do histórico de escolhas; GET da fatura inclui confirmações e autoria. Confirmar exige mínimo crítico, identidade/proveniência, financeiro consistente, atestação humana explícita de cobertura do quadro e ciência exata das limitações atuais. Guarda IDs concretos de proveniência, hash do conteúdo, revisões, autor/data/justificativa, sem alterar a cobertura original da extração ou inventar ausentes. Invoice.revision é de conteúdo; confirmações têm registros imutáveis próprios e avançam dataset_revision uma vez.

## Entrega complementar: interface mínima de remoção e acompanhamento

Foi adicionado um slice autenticado de apresentação para remoção e acompanhamento do estado do conjunto, usando apenas os serviços e rotas existentes: a página de detalhe expõe o estado geral do conjunto (`invoice-readiness`), o formulário de remoção usa `DELETE /api/v1/simulations/{id}/invoices/{invoice_id}` com confirmação explícita e CSRF, e o acompanhamento informa a prontidão e bloqueios do dataset sem inventar processamento real. Nenhuma nova fila, parser, upload ou cálculo foi habilitado; a ação de leitura real continua bloqueada até a homologação de §5/§12, com layout/documento e ENEL desabilitados.

Verificações locais desta fatia: 4 testes focados da interface web aprovados, incluindo a UI autenticada de remoção e acompanhamento, em 2,48 s. A suíte de leitura/confirmação/seleção do fluxo web segue com 1 caso Edge omitido por configuração local. A CI remota do commit base `9390d53` está concluída com sucesso em [42876453208](https://github.com/virgilio-vpr/EcoWatt/actions/runs/42876453208). O commit desta entrega será enviado diretamente na branch `fase-2` sem merge.

## Pendências e próximo passo

Próxima fatia coerente: interface autenticada para remoção e acompanhamento somente onde os serviços existentes permitem, sem inventar progresso de processamento. A ação de remoção usa `DELETE /api/v1/simulations/{id}/invoices/{invoice_id}` com CSRF e confirmação explícita, e o acompanhamento repassa o estado atual do conjunto via `invoice-readiness`; não se criam filas nem processamento real sem os serviços compatíveis. Ação de leitura/upload real continua bloqueada até as garantias de §5/§12 e homologação de adaptador; seleção local nunca inicia processamento. Complementos que precisem de consolidação/segmentação financeira permanecem pendentes, sem soma automática. O futuro motor da Fase 3 deverá consumir a revisão atual e somente os IDs incluídos pelo guard.

PDFs/layouts documentais permanecem desabilitados, inclusive ENEL. Antes de recebimento real: verificar integralmente §5/§12 — confinamento sem rede/privilégios, CPU/RAM/pixels, descendentes órfãos, watchdog rígido, swap/dumps, diretório RAM quando necessário e ausência de spool no framework/proxy — e homologar adaptador específico. Spawn sintético não é sandbox homologado; catálogo tarifário não habilita parser ou fallback ENEL. Não antecipar motor econômico ou declarar Fase 2 concluída por esta fatia.

Ressalvas da Fase 0 intactas: desconhecido não equivale a zero, hipóteses não são homologação e Verde exemplificativa não é gabarito financeiro. SMTP externo/MFA/produção/retenção continuam nas fases próprias.

## Arquivos e commit

Alterados: `docs/STATUS.md`; `src/ecowatt/web/templates/invoice_detail_fragment.html`; `src/ecowatt/web/static/invoice-review.js`; `tests/test_invoice_web.py`.

Commit enviado na branch `fase-2` pela integração GitHub, sem merge com `main`. Arquivos locais, `.env`, corpus, bancos, ambientes e caches ficam fora do envio.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
