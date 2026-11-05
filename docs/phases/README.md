# Planos por fase

Estes planos apontam para as partes necessárias da [SPEC](../../EcoWatt_PROJECT_SPEC.md); não substituem requisitos nem repetem seu checklist. O progresso oficial de implementação fica na seção 15 da SPEC. O [STATUS](../STATUS.md) registra a entrega corrente e as verificações mais recentes.

| Fase | Plano | Dependência de entrada |
| --- | --- | --- |
| 0 | [Contratos e corpus](phase-00-contracts.md) | Requisitos atuais e amostras disponíveis |
| 1 | [Backend, banco e usuários](phase-01-backend.md) | Contratos mínimos; fixtures sintéticas permitidas |
| 2 | [Leitura e armazenamento](phase-02-invoices.md) | Usuários, permissões, esquema e migrações |
| 3 | [Simulação](phase-03-calculation.md) | Contrato estruturado; fixtures permitem desenvolvimento antes de concluir o leitor |
| 4 | [Relatório e interface](phase-04-reports-web.md) | Execução reproduzível e serviços autenticados |
| 5 | [Homologação](phase-05-validation.md) | Fluxo integrado e corpus conferido |
| 6 | [Orçamentos](phase-06-quotes.md) | CRM, cliente e revisão de simulação |
| 7 | [Produção](phase-07-production.md) | Escopo web homologado, incluindo orçamentos |
| 8 | [Mobile](phase-08-mobile.md) | API estável e pedido explícito dessa evolução |

## Como dividir os chats

Use um chat por entrega verificável; uma fase pode ocupar vários chats. Continue correções e testes da mesma entrega no chat atual. Antes de trocar, peça a atualização do STATUS com o ponto de retomada. O novo chat deve consultar os arquivos, sem depender do histórico de outros chats.

Modelo de solicitação:

> Implemente [entrega específica] da Fase [número]. Consulte AGENTS.md, docs/STATUS.md e docs/phases/[arquivo]. Leia as seções indicadas da SPEC e os arquivos necessários, ampliando a consulta quando houver dependências. Faça as verificações aplicáveis, atualize o status e informe os arquivos alterados e realize o commit direto no GitHub conforme a autorização em AGENTS.md.

Uma referência não carrega automaticamente seu conteúdo: o agente deve abrir os trechos necessários antes de implementar. Em caso de ambiguidade, ler mais contexto é preferível a inventar uma regra.
