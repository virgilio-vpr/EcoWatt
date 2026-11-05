# Fase 6 — Orçamentos no CRM

Objetivo: emitir proposta comercial ligada a cliente e execução, para encaminhamento posterior pelo administrador.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 4.4 (CRM), 10.1 e 10.4 (tabelas/FKs/versões), 11 (origem da execução), 12 (autorização), 13 (API) e 15/Fase 6 (aceite).

## Entregas e ordem

1. Modelo de orçamento, revisão e itens, após cliente/simulação/execução de origem.
2. Serviços, preços, condições e validade; mudanças auditadas e revisões preservadas.
3. Emissão/consulta de PDF, estados e registro de envio manual.
4. Acesso do cliente somente aos documentos publicados para ele.

Geração não envia e-mail automaticamente. Orçamento não modifica o diagnóstico de origem. Tratar exclusão/retenção e FKs conforme política da simulação, sem deixar dados derivados esquecidos.

Verificação: autorização, vínculo à revisão, totais/versões, download privado e transições de estado. Aceite oficial na SPEC.
