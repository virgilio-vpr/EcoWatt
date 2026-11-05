# Estado do EcoWatt

Atualizado em 05/11/2026. Referência: SPEC versão 3.5.

## Entrega atual

Preparação documental concluída. Ambiente do projeto e implementação ainda não iniciados. Nenhuma fase de implementação está marcada como concluída na SPEC.

## Concluído

- SPEC e README organizados, com backend primeiro e três fases centrais: leitura/armazenamento, simulação e relatório.
- Criados AGENTS.md, este status e mapas de leitura para as fases 0–8.
- Definido versionamento por commits manuais no site do GitHub; sem dependência de Git local.

## Verificações realizadas

- Estrutura dos planos e referências de seções conferidas nesta entrega; nenhuma dependência instalada, banco criado ou aplicação executada.
- Inspeção anterior, em 04/11/2026: Python 3.13.14 funcional, SQLite 3.50.4 pelo Python, pip/venv disponíveis e extensões Python/SQLite no VS Code.
- Nessa inspeção, Git CLI, uv, Tesseract e dependências principais do projeto não foram encontrados; Pango/GObject não carregaram. Isso é histórico, não garantia do estado atual. Revalidar ferramentas específicas antes do uso.

## Pendências e restrições

- Usuário sem administrador; possibilidade de instalações locais sujeita às políticas da máquina. Não houve teste de instalação.
- Instalações continuam pendentes de autorização para a preparação do ambiente; este trabalho trata somente de documentação.
- Corpus real ENEL, fórmulas originais e dados externos da seção 16 da SPEC ainda não foram entregues/validados neste trabalho. Usar fixtures sintéticas identificadas para desenvolver, sem alegar homologação.
- README descreve passos previstos; ainda não existem pyproject.toml, lockfile, migrações, seed ou comandos de execução do EcoWatt.
- Em 05/11/2026, o usuário autorizou o envio inicial pela integração GitHub para `virgilio-vpr/EcoWatt`, branch `main`, sem Git local. README inicial publicado no commit `c4c7ab09a71e819787227dd62e66a3507c8a9f7c`; este status acompanha o envio dos demais documentos. Consultar o histórico remoto para identificar o commit desta entrega. Envios futuros continuam manuais, salvo nova autorização explícita.

## Próximo passo

Quando solicitado, preparar ambiente local mínimo e iniciar a [Fase 1](phases/phase-01-backend.md), verificando antes os contratos da [Fase 0](phases/phase-00-contracts.md). Definir versões, dependências e configuração sem administrador, sem Docker e sem instalar recursos fora do escopo autorizado. A falta de corpus real não bloqueia a base com dados sintéticos.

## Arquivos da última entrega

- `AGENTS.md`: instruções e regras essenciais.
- `docs/STATUS.md`: este resumo.
- `docs/phases/README.md` e `phase-00-*.md` a `phase-08-*.md`: planos e referências.
- `README.md`: mapa atualizado da documentação de apoio.

Mensagem sugerida para commit manual: `docs: adiciona orientacoes do agente e planos por fase`.
