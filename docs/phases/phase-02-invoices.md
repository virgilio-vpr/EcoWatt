# Fase 2 — Coração 1/3: leitura e armazenamento

Objetivo: transformar cada PDF admitido em dados estruturados conferíveis, com descarte do original.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 4.2–4.4 (unidade, suporte ao layout e perfis), 5 (limites, descarte e leitura explícita), 6 (pipeline/qualidade), 7 (campos e demandas medidas por posto Azul/Verde), 8.6 (dependências de preço/mercado para o contrato, sem implementar o motor nesta fase), 10.1–10.4 (modelo/transações), 12 (isolamento do PDF), 13 (status/API), 14 (limites operacionais) e 15/Fase 2 (aceite).

## Entregas e ordem

1. Tabelas/migrações de faturas, medições, itens, proveniência e estado, após seus pais.
2. Salvar unidade/endereço; validar admissão apenas após essa etapa. No cabeçalho da anexação/leitura, identificar distribuidora/suporte ao layout e oferecer contato para não suportados, conforme §4.2; catálogo ANEEL não habilita parser.
3. Extração textual por adaptador e validações; OCR seletivo isolado quando necessário. Incluir demandas ativas medidas por posto no quadro de medição Azul/Verde, distintas da contratação, e preservar mercado/evidências por ciclo para o recorte ACL (§§7.1–7.3).
4. Gravação atômica, duplicidade/refaturamento, ordenação e revisão de campos.
5. Botão “Ler fatura”, consulta de estado, remoção/cancelamento e recuperação após interrupção.

Saída para cálculo: conjunto estruturado confirmado e versionado, nunca PDF/texto bruto persistente. Não exigir 12 faturas para liberar uma primeira análise.

Segunda entrega: admissão sintética, consulta JSON de suporte, unidade salva, reservas acumuladas/capacidade em `0005_invoice_admissions` e TASKS. Terceira entrega: liderança/fencing em `0006_coordinator_lease`, fila RAM limitada, subprocesso sintético, timeout, cancelamento/descarte controlados e recuperação de conteúdo perdido. [ADMISSION](../ADMISSION.md) e [COORDINATOR](../COORDINATOR.md) definem contratos e barreiras restantes: garantias de SO/framework/proxy (§5/§12), resultado faturável/proveniência, vínculo fatura/tarefa, remoção do grafo e cabeçalho visual/contato. Nenhum layout documental ou recebimento de PDF habilitado. Os critérios completos de aceite continuam abertos na SPEC.

Quarta entrega: [resultado normalizado/persistência sintética](../INVOICE-STORAGE.md), vínculo em `0007_invoice_publications`, valores/proveniência v1, dependências, revisão do conjunto separada da unidade e GET/DELETE JSON com remoção atômica do grafo. O resultado inventado do subprocesso nunca vira ready. Restam as barreiras documentais de segurança, adaptador específico homologado, revisão operacional versionada, validação financeira, duplicidade lógica/refaturamento, prontidão e interface. Não copiar critérios de aceite para este plano; seção 15 segue aberta.

Verificação: corpus textual/digitalizado/híbrido, arquivos inválidos, campos desconhecidos, rollback sem órfãos, retries, limites acumulados e resultados tardios após remoção. Auditar temporários e observabilidade antes de afirmar descarte. Aceite oficial na SPEC.

Primeira entrega implementada em 09/11/2026: esquema `0004_invoices` e regressões sintéticas de persistência pelo protocolo TASKS. Detalhes do modelo, escalas, FKs e limites em [DATABASE](../DATABASE.md). O esquema não homologa layout nem implementa extração, revisão ou liberação de cálculo.

Quinta entrega: [revisão JSON versionada](../INVOICE-REVIEW.md) de campos existentes, dependentes transitivos invalidados, memória financeira observada e consulta de pendências do conjunto. Somente synthetic/invoice-v0.3; sem nova migração, PDFs, cálculo ou interface completa. Confirmação integral, duplicidade lógica/refaturamento com escolha explícita e prontidão efetiva são a próxima fatia. Nenhum critério integral adicional da seção 15 foi marcado.

Sexta entrega: [confirmação/seleção versionada](../INVOICE-CONFIRMATION.md), migração 0008_invoice_confirmation, prontidão estrutural com uma fatura sintética confirmada e escolhas explícitas para conflitos. Mantém histórico e limitações por módulo, rejeita revisões antigas e não inclui alternativa silenciosamente após remoção. Períodos distintos precisam não sobrepor; complementos que exijam consolidação continuam bloqueados.

Sétima entrega: interface HTML/HTMX de lista, detalhe, correção, confirmação e escolha de conflitos, usando os serviços/API existentes. Fluxo validado no Edge com fixtures sintéticas: estados tipados, remoção de valor em estado missing, conflito de revisão, CSRF, confirmação e seleção explícita; sem nova migração. Próximo passo: interface autenticada para remoção/acompanhamento somente onde já há serviço, sem fingir progresso. Upload e leitura real dependem das garantias integrais de §5/§12 e de adaptador homologado. Critérios completos da seção 15 continuam abertos.
