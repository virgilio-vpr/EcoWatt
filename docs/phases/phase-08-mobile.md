# Fase 8 — Evolução mobile

Objetivo: reutilizar os serviços REST em um app, sem copiar o motor e sem alterar os limites do cliente.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 3.2–3.3 (camadas), 4.3 (cota/isolamento), 5.4 (faturas), 12 (segurança), 13 (contrato/autenticação mobile) e 15/Fase 8 (aceite).

## Entregas e ordem

1. Quando esta evolução for solicitada, definir a stack do app e seu escopo; não antecipar uma escolha inexistente na SPEC.
2. Autenticação com tokens revogáveis e armazenamento seguro, preservando autorização dos serviços.
3. Dados da unidade, leitura incremental, revisão e resultados pelo contrato REST.
4. Conferir a mesma cota em acesso simultâneo web/app.

Não iniciar app, dependências mobile ou fluxo de tokens dedicado como parte da base web. A web mantém a autenticação prevista para ela.

Verificação: expiração/revogação, acesso cruzado, concorrência de cota, idempotência e retomada de envios. Aceite oficial na SPEC.
