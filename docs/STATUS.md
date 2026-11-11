# Estado do EcoWatt

Atualizado em 11/11/2026. Referência: SPEC versão 3.11; gabarito mínimo aceito v0.2.

## Entrega corrente — backend experimental de isolamento Windows

Base `fase-2` conferida em `8bc11324ed87803a49570efab11b684403f2909f`.
Implementação publicada em [`00b2daa1aebcbbf5f80be90a246b591a2b2fe187`](https://github.com/virgilio-vpr/EcoWatt/commit/00b2daa1aebcbbf5f80be90a246b591a2b2fe187),
com escrita e head remoto confirmados. Consulta pós-envio pela integração
não retornou execução de CI para esse SHA; sem aprovação remota atribuída.
Os seis arquivos existentes desta entrega coincidiam com os blobs remotos,
normalizando CRLF. Integração GitHub acessível, sem nova autenticação; envio
limitado aos arquivos abaixo, preservando árvore remota e alterações locais
anteriores, inclusive contratos/corpus e `.env`. Sem Git local, branch nova
ou merge; `main` não é alvo desta entrega.

Implementado `windows_isolation.py`: AppContainer sem capacidades, criação
suspensa, conferência do token efetivo antes de executar, ambiente mínimo e
handles não herdados. Job Object atribuído atomicamente na criação limita memória comprometida/CPU/processos,
nega breakaway e encerra árvore ao perder o pai. Watchdog de thread independe
do polling, mas falta supervisor externo para host suspenso/GIL travado.
O backend não está conectado ao coordenador e não recebe bytes documentais.
RasterBudget anterior permanece preservado e sem renderer integrado.

Verificação autorizada no Windows 11/Python 3.13.14: **26 testes nativos
aprovados em 50,48 s**, após atribuição atômica do Job. Rede local TCP/UDP IPv4/IPv6 com controles positivos e
receptores sem entrega; token sem capacidades/elevação, canário/memória do pai
negados, CPU/memória, prazo, quota/breakaway, falha de configuração sem resume
e morte abrupta do pai com handles da árvore. Não foram testados Internet,
DNS, LAN externa ou IPC/COM/brokers. **Suíte geral: 356 aprovados e 15 omitidos
em 122,05 s**: quatro omissões anteriores e onze probes Win32 habilitados
separadamente pelo runner. Compilação de src/tests aprovada. Sem alteração de
esquema, dependências, rotas ou interface; migrações/Edge não repetidos nesta
fatia. CI recebe etapa própria de probes; consulta pós-envio ainda sem execução.

Python Store introduziu capacidade implícita de pacote nos primeiros probes;
backend agora a rejeita antes de executar. Runner usa perfil criado diretamente
no PowerShell nativo e cópias locais do Python/bibliotecas já instalados, sem
downloads/instalação ou alteração das ACLs originais/ExecutionPolicy/firewall.
Tentativas iniciais falharam antes da execução final aprovada; perfis sintéticos
remanescentes foram removidos pela API e ausência conferida. Artefatos locais
sintéticos ficam ignorados em `.local-analysis/`, fora do envio.
**WSL e containers estão fora deste ambiente por decisão/restrição do usuário.**

Upload/leitura real continuam bloqueados, inclusive ENEL. Nenhum documento,
corpus, imagem ou texto bruto real foi acessado/processado/publicado. Falta
integração ao coordenador, revisão ampliada de superfícies, supervisor externo,
swap/dumps, temporários RAM, ingresso sem spool e adaptador homologado.
Alcance em [DOCUMENT-SECURITY](DOCUMENT-SECURITY.md). Nenhum item integral de
§15 foi marcado. Fase 2 permanece aberta, sem antecipar Fase 3.

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

## Implementação preservada da Fase 2

Admissão sintética com limites acumulados/capacidade; coordenador com liderança,
fencing, fila RAM, subprocesso sintético, cancelamento/timeout e recuperação;
publicação estruturada atômica; revisão versionada e validação financeira;
confirmação humana, seleção explícita de duplicatas/refaturamentos e prontidão
estrutural; interface de consulta/correção/confirmação/seleção/remoção e suporte
ao layout via HTMX ou GET sem JavaScript. O encerramento do servidor nos testes
Windows tem keep-alive=1 e graceful shutdown=3, preservando a asserção de thread
encerrada; não altera configuração de produção.

Contratos de referência: [ADMISSION](ADMISSION.md), [COORDINATOR](COORDINATOR.md),
[TASKS](TASKS.md), [INVOICE-STORAGE](INVOICE-STORAGE.md),
[INVOICE-REVIEW](INVOICE-REVIEW.md) e [INVOICE-CONFIRMATION](INVOICE-CONFIRMATION.md).
`normalized-invoice-v1` continua exclusivamente sintético. Publicação inicial
fica needs_review; prontidão exige confirmação e escolhas atuais. Uma conta
pode bastar estruturalmente; não garante suficiência econômica. Complementos
permanecem em `complement_consolidation_required`; `distinct_periods` exige
períodos conhecidos sem sobreposição. Remover o preferido não inclui alternativa
descartada silenciosamente. Correção/unidade/conjunto invalidam confirmações
e escolhas pertinentes; retry histórico não restaura prontidão antiga.

## Pendências e próximo passo

Completar supervisor externo, revisão ampliada de superfícies, swap/dumps,
temporários RAM e ingresso sem spool; integrar backend Windows/IPC limitado
ao coordenador. WSL/containers não fazem parte deste ambiente. Depois das
garantias integrais de §5/§12, integrar renderer ao orçamento e proveniência
documental versionada, com homologação específica do layout. As provas
sintéticas desta entrega não liberam upload/leitura real.

Depois das garantias, completar adaptador textual/OCR seletivo e validações
críticas, cadastro visual da unidade, seleção local, ação “Ler fatura”, envio
incremental/progresso, recuperação/reenvio e contato. Aceite integrado requer
documentos sintéticos textuais/digitalizados/híbridos/protegidos/inválidos e lote
misto, com descarte verificado. Não continuar apenas com melhorias pequenas de
interface enquanto processamento e segurança estiverem pendentes.

## Arquivos desta entrega

Novos: `src/ecowatt/windows_isolation.py`, `tests/test_windows_isolation.py`,
`tests/windows_profile.ps1`, `tests/run_windows_isolation.ps1`.
Alterados: `.github/workflows/backend.yml`, `README.md`,
`docs/DOCUMENT-SECURITY.md`, `docs/COORDINATOR.md`, `docs/STATUS.md`,
`docs/phases/phase-02-invoices.md`.
Removidos: nenhum. Envio restrito a esses dez arquivos, sobre a árvore remota
preservada e com proteção de head esperado. `.env`, contratos/corpus locais,
bancos, caches, temporários e scripts auxiliares ficam fora. SHA e CI finais
serão informados após consulta remota; nenhum merge.
