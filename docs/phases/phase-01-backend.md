# Fase 1 — Backend, banco e usuários

Objetivo: criar base local FastAPI/SQLite e acesso seguro antes do frontend completo.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 3.2–3.3 (stack/estrutura), 4.1 e 4.3–4.5 (cadastro, perfis, cota e seed), 10 (persistência e ordem de FKs), 12 (segurança), 13 (API), 15/Fase 1 (aceite). Consultar o README para o estado real dos comandos e a seção 16 para dependências externas.

## Entregas sugeridas para chats separados

1. Ambiente mínimo autorizado, pyproject/lockfile, configuração tipada e estrutura; sem Docker.
2. Modelos raiz e migrações ordenadas: empresa, usuário e dependentes; SQLite com FKs e Decimal sem float.
3. Cadastro, ativação, login, recuperação e token de sessão; autorização JSON e web.
4. Seed explícito e idempotente de admin e cliente teste; sem uso em produção.
5. Simulação/unidade, titularidade, cota transacional e exclusão; contrato para a fase de leitura.

Antes de instalar, verificar o estado atual e a autorização. Não atualizar pacotes globais por conveniência. O acabamento visual fica para a Fase 4.

Verificação: migração limpa/upgrade, seed repetido, login/ativação, acesso cruzado, revogação e concorrência de criação da terceira simulação. Aceite oficial na SPEC. Preencher comandos realmente testados no README/SETUP quando existirem.
