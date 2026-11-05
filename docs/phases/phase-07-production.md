# Fase 7 — Preparação de produção

Objetivo: validar implantação com PostgreSQL/Docker e operação real após concluir o escopo web.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 4.5 (seed restrito), 5 (processamento/descarte), 10.3–10.5 (migração/configuração), 12 (segurança/retenção), 14 (capacidade), 15/Fase 7 (aceite) e 16–17 (dependências/fontes). Consultar SETUP/DATABASE/DEPLOYMENT quando esses documentos operacionais forem criados.

## Entregas e ordem

1. Dockerfile/Compose, PostgreSQL, volume, healthchecks e migração coordenada.
2. Testes do esquema e serviços no PostgreSQL, sem assumir portabilidade comprovada pela execução em SQLite.
3. Backup, janela sem escrita, transporte tipado, conferência de resultados e plano de retorno.
4. Segredos de produção separados do Git/build, admin real, MFA, e-mail transacional, limites e monitoramento.
5. Retenção/exclusão, restauração e piloto assistido.

Docker não é necessário nas fases locais anteriores. Esta fase descreve preparação; publicação externa deve ocorrer somente dentro da autorização aplicável. Não reutilizar contas de demonstração nem bypasses locais.

Verificação e aceite: seção 15/Fase 7, incluindo restauração real e isolamento de documentos. Registrar comandos testados e pendências operacionais sem afirmar conformidade não verificada.
