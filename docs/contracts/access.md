# Titularidade e autorização — contrato v0.1

Referência: SPEC §§4.3–4.5, 10.4 e 12. Matriz para implementação e testes, sem alegar controles já disponíveis.

`owner_id` é a conta responsável pela cota; `company_id` é sua empresa; `created_by`/`updated_by` são autores. Titular da ligação é dado da unidade e não concede acesso. Admin cria em nome de cliente explicitamente selecionado ou da própria empresa de demonstração. A titularidade não muda ao editar, recalcular ou assumir atendimento.

| Operação/recurso | Cliente | Admin |
| --- | --- | --- |
| Perfil e empresa | Apenas próprios | Consulta/gestão autorizada e auditada |
| Criar simulação | Próprio dono/empresa derivados da sessão | Própria conta ou cliente selecionado; dono e autor separados |
| Ler, conferir, editar, calcular, remover fatura | Somente simulação própria | Fluxo completo do dono selecionado, correções com justificativa |
| Status, relatório, PDF, exportação, versões | Somente próprios e não excluídos | Acesso administrativo auditável |
| Excluir simulação | Própria, com confirmação | Gestão auditada, sem contornar revogação/cota |
| Pedir contato | Próprio, ação explícita | Consulta e gestão no CRM; sem mensagem automática |
| CRM, notas internas, leads e orçamentos | Sem acesso a dados internos | Exclusivo; emitir orçamento não envia mensagem |
| Tarifas, regras, importações | Sem alteração privilegiada | Gestão validada, autoria e versões |
| Perfil privilegiado, dono ou empresa alheia no payload | Rejeitado | Somente operações administrativas explícitas; sem transferência implícita |

Aplicar a mesma decisão de autorização no serviço de aplicação para JSON, HTML, fragmentos HTMX, downloads e consulta de jobs. ID imprevisível e menu oculto não substituem verificação. Respostas do cliente excluem notas internas e dados de outros clientes. Conta bloqueada/sessão revogada não mantém acesso por link de PDF. MFA admin é requisito antes de produção; confirmação de e-mail e sessões revogáveis seguem a SPEC, sem bypass geral derivado do seed.

## Cota e concorrência

No máximo duas simulações não excluídas por `owner_id`, incluindo rascunho, processamento, concluída, parcial e falha. Empresas/unidades adicionais não ampliam a cota. A própria conta admin também tem cota dois. Admin não a contorna ao agir por cliente.

Criar exige autorização, reserva/verificação transacional por dono e idempotência. Duas criações simultâneas com uma vaga livre produzem uma única nova simulação; a outra recebe conflito de cota. Retry da mesma operação retorna a simulação original. Versões/cenários dentro da mesma unidade/conjunto não ocupam vaga; nova unidade/conjunto independente exige nova simulação.

Excluir revoga acesso a todas as versões/PDFs, cancela jobs e libera vaga na mesma operação lógica. Trabalho tardio não reativa dados. Limpeza física, retenção, backups e vínculos comerciais seguem política explícita; não preservar dados derivados acessíveis por esquecimento de FK.

## Casos de revisão e futuros testes

| Caso | Resultado esperado |
| --- | --- |
| Cliente A consulta IDs de B em JSON, HTMX, job ou PDF | Nenhum dado de B devolvido |
| Cliente injeta owner/company/role de terceiro | Rejeição, nenhuma mudança de titularidade |
| Admin cria para B | Dono B, empresa B, autor admin, cota de B |
| Admin cria terceira para B | Recusada mesmo com privilégios administrativos |
| Admin cria terceira própria | Recusada pela própria cota |
| Duas criações concorrentes, uma vaga | Uma criação, um conflito; nunca três ativas |
| Retry de criação bem-sucedida | Mesmo ID, sem nova vaga |
| Recalcular/corrigir | Nova revisão/run na mesma simulação; resultado anterior histórico |
| Tentar trocar UC em versão para contornar cota | Exigir nova simulação independente |
| Excluir e receber callback tardio | Vaga livre, recurso inacessível, nenhuma recriação |

Nenhum desses testes de aplicação foi executado nesta fase documental.
