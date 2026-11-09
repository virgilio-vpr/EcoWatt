# Contrato HTTP local — API v1

Fonte executável: `/api/v1/openapi.json`. Índice HTML local: `/api/v1/docs`. Contrato de apresentação independente de Jinja2/HTMX; serviços de aplicação compartilhados, sem chamadas HTTP internas entre web e API. Não há rotas de faturas/cálculos/relatórios implementadas nesta fase.

Consulta de admissão da Fase 2: `GET /api/v1/simulations/{id}/invoice-admission?layout_version=...`, autenticada e autorizada para dono/admin. Retorna pré-condição da unidade, distribuidora/layout, suporte, motivo e necessidade de contato, sem criar tarefa. `unit_not_saved` e `layout_not_supported` são motivos no JSON de consulta (200), não admissão de processamento. `document_upload_enabled` é sempre falso. POST nesse recurso não é permitido; nenhum endpoint multipart recebe PDFs. O serviço interno sintético, limites e códigos de comando estão em [ADMISSION](ADMISSION.md), sem apresentá-los como comandos públicos.

## Acesso

`GET /api/v1/auth/csrf` devolve csrf_token e cookie auxiliar HttpOnly. Comandos POST/PATCH/DELETE exigem Origin exatamente igual a PUBLIC_ORIGIN e X-CSRF-Token. O navegador informa Origin automaticamente; clientes HTTP precisam enviá-lo e preservar cookies. O token CSRF não é a credencial de sessão.

Login gera cookie opaco ecowatt_session (HttpOnly/SameSite=Strict), revogando a sessão anterior apresentada. Nunca enviar esse token no HTML, localStorage ou bearer improvisado. O OpenAPI declara SessionCookie nas operações privadas, CSRFHeader nos comandos e ambos **na mesma exigência** para comandos privados, sem representá-los como alternativas. Comandos públicos de acesso exigem CSRFHeader junto ao CSRFCookie auxiliar obtido no GET de CSRF. Admin usa autenticação normal e autorização de papel/titular, inclusive cota.

Cadastro/reenvio/recuperação: 202 aceita o pedido, sem comprovar entrega; SMTP disabled retorna 503 uniforme. Ativação/recuperação têm tokens de uso único; links, falhas e limitações estão em [EMAIL](EMAIL.md). Expiração/rotação/revogação e seed permanecem em [SETUP](SETUP.md).

## Respostas e erros

Todas as operações JSON atuais têm respostas tipadas. Respostas 204 não têm corpo. IDs públicos são UUIDs representados como strings; datas de criação são segundos Unix UTC, distintos de futuras datas de competência. Decimais financeiros serão strings segundo os contratos, sem float; não há endpoint financeiro fictício nesta base.

Erros devolvem `{code, message, fields, request_id}`: code estável, mensagem apropriada para exibição, fields como lista de caminhos e identificador técnico igual ao header X-Request-ID. Não devolvem valores rejeitados, senhas, tokens, conteúdo faturável ou diagnóstico do banco/SMTP. O header Allow é preservado no 405. Cliente deve tratar códigos desconhecidos sem expor corpo bruto ou assumir sucesso.

| HTTP | Códigos atuais relevantes | Ação |
| --- | --- | --- |
| 400 | invalid_token | Reabrir/solicitar novo link |
| 401 | authentication_required, invalid_credentials | Entrar novamente/conferir acesso |
| 403 | csrf_failed, forbidden | Conferir origem/CSRF ou permissão; não repetir automaticamente |
| 404 | not_found | Recurso ausente, excluído ou inacessível, sem distinguir dono alheio |
| 409 | simulation_limit_reached, simulation_revision_conflict, idempotency_conflict, unit_identity_conflict | Resolver cota/revisão/chave/unidade antes de reenviar |
| 422 | validation_error, confirmation_required, invalid_distributor | Conferir fields/formulário |
| 429 | rate_limited | Aguardar a janela; não fazer retry em loop |
| 503 | not_ready, database_unavailable, email_unavailable | Conferir disponibilidade/configuração |

Os demais códigos de operação administrativa constam nos serviços; não há promessa de enum fechado de erros para todos os clientes futuros.

## Paginação, cota e idempotência

GET de simulações e catálogo usa page>=1, page_size de 1 a 100 (padrão 20); retorna items, total, page e page_size. Simulações também retornam limit=2. A ordenação de simulações é created_at/id e a do catálogo é code. Total e página vêm da mesma transação; paginação por offset não é snapshot entre requisições diferentes.

Criar simulação: POST `/api/v1/simulations`, JSON `{}`, header Idempotency-Key com 8–128 caracteres. Dono/empresa derivam da sessão. Admin seleciona dono explicitamente em `/api/v1/admin/users/{owner_id}/simulations`.

Uma chave por ator/conteúdo permanece vinculada ao recurso: mesma chave/dono retorna o mesmo ID com 201, inclusive em concorrência; trocar dono com a mesma chave gera 409. Replay após exclusão retorna 404 e não recria. Não há expiração da chave implementada nesta fase. Toda simulação não excluída ocupa uma das duas vagas do dono, inclusive falhas e conta própria do admin. Criar terceira retorna 409; alterações/versões não criam nova vaga.

Salvar unidade e excluir exigem expected_revision atual. Excluir exige boolean JSON `confirm: true`, sem conversão de string/número. UC/distribuidora já salvas não podem ser trocadas por outra unidade na mesma simulação. Tombstone fica inacessível, libera vaga e cancela operações ativas atomicamente. O serviço interno [TASKS](TASKS.md) revoga leases e impede persistência tardia, revalidando ator/tombstone/revisão em transação curta. Não há endpoint público de tarefas nem executor de OCR nesta fase. A futura camada de processamento usa esse protocolo, sem reutilizar transação/snapshot anterior à extração.

## Cliente HTTP local

`web/static/api-client.js` fornece `EcoWattHTTP.request(path, options)` para as páginas mínimas. Usa fetch apenas em `/api/v1` na mesma origem, cookies same-origin, CSRF para comandos, timeout padrão de dez segundos e redirects recusados. Retorna objeto JSON ou null no 204. APIError preserva code/status/fields/requestId; timeout/rede não incluem payload ou diagnóstico técnico. O formulário de autenticação reutiliza esse cliente e exibe somente mensagem segura.

Não há retry automático, mesmo com chave de idempotência: timeout/falha de rede não prova que a escrita falhou. Conferir o resultado; se repetir criação, preservar a mesma chave. Não derivar chave de senha, e-mail ou conteúdo sensível. O cliente não converte strings decimais em Number. Mobile terá adaptador de credenciais próprio em fase futura, sem alterar autorização dos serviços.

## Correspondência com o pipeline futuro

O [contrato do pipeline](contracts/pipeline.md) usa códigos semânticos em maiúsculas; eles não substituem o envelope HTTP atual. Correspondências já existentes: QUOTA_EXCEEDED → 409 simulation_limit_reached; REVISION_CONFLICT → 409 simulation_revision_conflict; RESOURCE_UNAVAILABLE → 404 not_found. Os detalhes stage/resource_id/field_path/retryable/action pertencem ao erro de processamento e precisarão de representação explícita na Fase 2, sem vazar dados.

UNIT_REQUIRED, CAPACITY_UNAVAILABLE, INVALID_DOCUMENT, DUPLICATE, REVIEW_REQUIRED e MODULE_DATA_MISSING ainda não têm endpoints implementados. Não interpretar a lista documental como funcionalidade disponível nem reutilizar um erro genérico para inventar resultado de parser/cálculo.

Verificações: OpenAPI com schemas de respostas, cookie/CSRF, origem e idempotência; erros/correlação, paginação, 204 e confirmação estrita; cliente no Edge com login, paginação, replay, exclusão e falha de rede sem retry. As regressões de concorrência, acesso cruzado e sessão/tokens continuam na suíte.
