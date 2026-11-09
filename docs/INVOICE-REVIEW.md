# Revisão versionada — quinta entrega sintética da Fase 2

Este documento preserva o contrato e os limites da quinta entrega. A [sexta entrega](INVOICE-CONFIRMATION.md) acrescenta confirmação/seleção e prontidão estrutural, com política financeira observed-financial-v2. Referências abaixo à ausência de confirmação/prontidão descrevem o marco anterior.

Escopo: revisão JSON de campos existentes em faturas `synthetic / invoice-v0.3`, invalidação de dependentes e conferência financeira observada. Não recebe arquivos, cria itens, altera postos/vínculos de medição, resolve refaturamentos, confirma a fatura inteira ou habilita cálculo. Faturas continuam `needs_review`. PDFs reais e layouts comerciais continuam desabilitados; catálogo tarifário não habilita parser nem fallback ENEL.

## Comando e versões

`POST /api/v1/simulations/{id}/invoices/{invoice_id}/reviews` exige sessão dono/admin, Origin/CSRF e `Idempotency-Key` (8–128 caracteres). Corpo fechado:

```json
{
  "expected_revision": 1,
  "expected_dataset_revision": 2,
  "expected_invoice_revision": 1,
  "reason_code": "synthetic_correction",
  "edits": [{
    "path": "header.invoice_total",
    "expected_version": 1,
    "field": {"value": "18.76", "state": "confirmed", "unit": "BRL", "origin": "user"}
  }]
}
```

Até 64 campos distintos por comando. Caminhos vêm do GET estruturado, incluindo IDs reais de itens/medições; somente campos do registro normalizado são editáveis. `field` segue Value de normalized-invoice-v1: Decimal string, cobertura/estado/unidade, hipótese e regra quando necessárias. Não aceita texto bruto, autoria/dono declarados, PDF/OCR, float, NaN, perda de escala ou mudança para outra UC. Ausência permanece NULL/sentinel semântico, nunca zero. Estados estimados e inaplicabilidade conservam suas exigências. A justificativa do comando fica na auditoria; motivo específico do campo, quando informado, fica na proveniência.

Dentro de uma única transação de escrita: revalidar ator ativo, dono/admin, tombstone e as três revisões; conferir versão de cada campo; validar o estado conjunto de unidades e períodos; atualizar colunas e criar proveniência `version + 1`; invalidar dependentes transitivos; registrar validações, contador e recibo. `Invoice.revision` e `Simulation.dataset_revision` avançam uma vez por comando, mesmo com várias edições. `Invoice.dataset_revision` identifica a última alteração dessa fatura. `Simulation.revision` não avança, e tarefas independentes admitidas para a mesma unidade não são canceladas. Não há execuções econômicas nesta fase para invalidar; a futura execução deverá exigir a revisão atual do conjunto.

Valores, autores, datas, justificativas e dependências das versões anteriores são imutáveis pelo serviço. Mudança, inclusive reconfirmação do mesmo valor, invalida transitivamente os derivados/estimativas que apontem para aquele caminho, mesmo por versão antiga. Cada dependente não corrigido no mesmo lote recebe nova versão missing/NULL, regra `dependency-invalidation-v1`, motivo `dependency_changed` e vínculos concretos às entradas que ficaram obsoletas; a versão anterior retém seu valor e método original. Não recalcular silenciosamente ou reaproveitar valor obsoleto.

`field.inputs` neste comando contém **IDs de proveniência**, não os apelidos locais da publicação inicial. Exige versões atuais da mesma fatura e entradas fora do conjunto alterado/inválido nesse comando. Autorreferência, referência estrangeira/obsoleta, duplicação e ciclos são recusados. Para derivar a partir de uma entrada corrigida, confirmar a correção e enviar novo comando com seus IDs atuais. Dependente explicitamente corrigido no lote pode receber valor conferido pelo usuário, com autoria/justificativa; não pode continuar derivando da entrada antiga.

Recibo: `invoice_id`, `invoice_revision`, `dataset_revision`, `invalidated_paths`. Auditoria estruturada guarda hashes da chave/pedido e recibo, sem payload livre. Chave tem escopo ator/fatura/operação. Retry idêntico devolve o recibo histórico sem reaplicar, inclusive depois de outra revisão; não declara que essa revisão ainda é atual. Conteúdo diferente retorna 409/idempotency_conflict. Exclusão/tombstone/ator inativo ou perda de acesso impedem replay. Conflitos de unidade/conjunto/fatura/campo retornam 409 com códigos próprios; o cliente deve consultar novamente, sem sobrescrita automática.

## Conferência financeira e pendências

`GET /api/v1/simulations/{id}/invoice-readiness` exige a mesma autorização. Retorna revisões atuais de unidade/conjunto, política `observed-financial-v1`, pendências e verificações por fatura. Não cria tarefas nem modifica o conjunto. Números financeiros saem como strings.

- Produto quantidade × preço cheio observado, sem reaplicar impostos; diferença assinada = observado − esperado; passa até BRL 0.99 inclusive por item. Base de preço não confirmada gera pendência. Quantidade/preço ausente gera aviso de produto indisponível, sem reconstrução; valor monetário ausente bloqueia fechamento.
- Soma das linhas com sinal contra TOTAL do quadro. Residual deve ser zero nesta fatia: residual não zero fica pendente, sem usar tolerância de item para apagá-lo. Classificação/aceite de residual ainda não existe. Subtotal/residual declarados, quando presentes, também são confrontados. Cobertura parcial continua impedindo confirmação integral, mesmo se os valores coincidirem.
- Total a pagar é informação separada: diferença para o quadro gera aviso, sem parcela artificial nem bloqueio financeiro automático. Não equivale a auditoria de boleto/tributos.
- Operações Decimal usam contexto suficiente e não arredondam valores. Memória além de Numeric(38,18) gera `validation_numeric_range` bloqueante, com memória indisponível explícita; valores originais permanecem intactos na proveniência. Não há truncamento silencioso.

Cada revisão acrescenta memória das validações em invoice_validations com política `observed-financial-v1:r<N>`. Registros anteriores, inclusive review_required inicial, não são apagados. A consulta calcula as verificações do estado atual, não reapresenta validação antiga como válida. Não há novas tabelas/migração: head permanece `0007_invoice_publications`.

`ready_for_calculation` permanece **false**: confirmação integral e resolução de duplicidade/refaturamento ainda pendentes são motivos explícitos, mesmo se as finanças passarem. A consulta também identifica conjunto vazio, unidade não salva, faturas em revisão, bloqueios financeiros, admissões queued/running e reservas não removidas sem publicação, incluindo falha/expiração/cancelamento. Não ignora arquivo problemático. Seleções locais ainda não enviadas pertencem à futura interface e não podem ser conhecidas por este backend. Não exigir doze contas nem declarar suficiência dos módulos econômicos.

Próxima entrega: confirmação versionada do mínimo crítico, duplicidade lógica/refaturamento com escolha explícita, prontidão efetiva e invalidação quando unidade/conjunto mudar. Segurança documental §5/§12 e adaptador homologado precedem qualquer recebimento real; Edge verifica regressão web, sem provar segurança PDF ou correção financeira comercial. Ressalvas da Fase 0 permanecem.
