# EcoWatt

Plataforma web para leitura de faturas de energia, simulação de potenciais de economia e geração de relatórios, com área do cliente e CRM administrativo.

## Estado atual

A Fase 0 foi concluída com aceite explícito do usuário em 06/11/2026 para os contratos e o gabarito mínimo local. A primeira entrega da Fase 1 disponibiliza FastAPI, configuração tipada, ambiente local e uv.lock, com seis testes aprovados. Migrações, autenticação e seed permanecem nas próximas entregas.

A fonte dos requisitos é [EcoWatt_PROJECT_SPEC.md](EcoWatt_PROJECT_SPEC.md). O checklist de implementação fica na seção 15 e a ordem de criação das tabelas na seção 10.4.

Para iniciar uma tarefa, consulte [AGENTS.md](AGENTS.md), [docs/STATUS.md](docs/STATUS.md) e o [plano da fase](docs/phases/README.md). Esses arquivos orientam a leitura seletiva da SPEC e registram o ponto de retomada; não substituem os requisitos completos.

O usuário autorizou commits diretos em `virgilio-vpr/EcoWatt`, sem confirmação adicional no site. Preferir a integração GitHub, sem exigir Git instalado. Ao concluir cada entrega, revisar os arquivos, preservar alterações remotas e informar o commit realizado. Enviar somente os documentos e códigos da entrega; faturas e planilhas reais permanecem locais. Commits pela integração não sincronizam automaticamente outros arquivos da pasta local.

Os documentos da Fase 0 estão no [dicionário de faturas](docs/contracts/invoice-data.md), [contrato do pipeline](docs/contracts/pipeline.md), [matriz de acesso](docs/contracts/access.md), [inventário e dependências do corpus](docs/corpus/README.md) e [casos sintéticos](docs/corpus/synthetic-cases.md). Contratos e gabarito mínimo local foram aceitos; homologação comercial e publicação de fixtures reais continuam pendentes.

A continuação da Fase 0 inclui [conferência das planilhas](docs/corpus/workbook-review.md), [conferência inicial das faturas](docs/corpus/invoice-review.md) e [registro regulatório](docs/corpus/regulatory-review.md). Os relatórios preservam o histórico da análise; o aceite atual é limitado ao gabarito mínimo local. Use o [texto para o novo chat da Fase 1](docs/phases/phase-01-start.md).

## Stack definida

- Backend: Python, FastAPI, SQLAlchemy 2 e Alembic.
- Banco atual: SQLite local, com WAL e chaves estrangeiras habilitadas.
- Leitura: pdfplumber, pypdfium2 e OCR seletivo com Tesseract.
- Cálculos: motor Python independente, com Decimal e entradas/saídas tipadas.
- Interface: Jinja2, HTMX local e Tailwind compilado, com temas claro e escuro.
- Relatórios: gráficos SVG e PDF com WeasyPrint.
- Produção futura: aplicação preparada para containers e PostgreSQL em Docker.

Não é necessário instalar ou executar Docker nesta etapa.

## Sequência de construção

1. Consolidar contratos, campos e corpus de referência, usando fixtures sintéticas quando dados reais ainda não estiverem disponíveis.
2. Criar backend, configuração e modelos. Aplicar migrações SQLite na ordem das dependências.
3. Implementar usuários, autenticação, permissões e seed idempotente de admin e cliente teste.
4. Entregar o coração 1/3: leitura textual/OCR, validação, armazenamento relacional e conferência.
5. Entregar o coração 2/3: motor de cálculo e cenários versionados.
6. Entregar o coração 3/3: relatório online/PDF e interface completa do cliente/admin.
7. Homologar cálculos, leitura, relacionamentos, concorrência e acesso.
8. Entregar geração de orçamentos no CRM.
9. Preparar produção: PostgreSQL em Docker, migração dos dados, segredos, backups e operação.

O administrador usa o mesmo fluxo de simulação do cliente, tanto na conta própria de demonstração quanto em nome de cliente selecionado no CRM, mantendo dono e autor registrados. A cota é de duas simulações por dono; recálculos e cenários são versões dentro delas.

## Preparação local

Comandos executáveis e verificados em [docs/SETUP.md](docs/SETUP.md): bootstrap local de uv 0.13.7, `uv sync --locked`, verificações e execução `python -m uvicorn ecowatt.main:create_app --factory --host 127.0.0.1 --port 8000` usando os executáveis de `.venv/Scripts`. Python 3.13. Health em `/api/v1/health`, OpenAPI em `/api/v1/openapi.json` e documentação em `/api/v1/docs`. Não há criação automática de banco ou contas. Health verifica somente o processo.

### Etapas futuras — ainda não executar

1. Instalar a versão de Python definida futuramente em `pyproject.toml` e o gerenciador `uv`.
2. Instalar os recursos nativos necessários ao Tesseract, ao português do OCR e ao WeasyPrint, conforme o sistema operacional. As versões e instruções verificadas deverão ser registradas em `docs/SETUP.md`.
3. Criar o ambiente virtual e instalar as dependências declaradas e fixadas pelo projeto.
4. Preparar o `.env` de desenvolvimento a partir do `.env.example`, usando somente configuração local e valores sintéticos. O arquivo SQLite deverá ficar em diretório local de dados.
5. Executar as migrações Alembic até a revisão atual, antes de criar usuários ou iniciar o processamento de faturas.
6. Executar o seed de desenvolvimento para criar `admin@ecowatt.test` e `cliente@ecowatt.test`, com senhas locais que atendam à política da SPEC. Repetir o seed não deve duplicar nem sobrescrever contas existentes.
7. Iniciar a API com Uvicorn e o coordenador de processamento pelo procedimento que será definido na implementação. Executar a compilação local de CSS quando necessário.
8. Conferir health/readiness e o OpenAPI. As URLs, os comandos executáveis e as versões deverão ser preenchidos aqui assim que esses recursos existirem.
9. Validar login e permissões com ambas as contas antes de testar faturas.

O seed não roda automaticamente ao iniciar o servidor e deve recusar execução em produção. Somente as contas sintéticas locais podem usar confirmação de e-mail prévia para testes; o cadastro normal exige ativação.

## Uso previsto

1. Acessar a landing page, cadastrar empresa/responsável e confirmar o e-mail.
2. Entrar com e-mail e senha.
3. Criar uma simulação, respeitando o máximo de duas por perfil.
4. Informar distribuidora, identificador da unidade/MTE, titular e endereço do ponto de conexão. Confirmar a cópia do endereço da empresa ou informar o endereço da cabine/subestação quando diferente, inclusive em rua adjacente, e salvar.
5. Anexar um PDF e clicar em **Ler fatura**. Aguardar extração e persistência dos campos faturáveis. Conferir nome e endereço extraídos: manter os coincidentes e confirmar/corrigir divergências sem substituir automaticamente o cadastro da empresa ou o ponto de conexão. Conferir também o mercado sugerido por identificação explícita ou pelos itens TE/TUSD; ausência em leitura incompleta permanece desconhecida.
6. Repetir até 12 faturas. A lista fica em ordem de ciclo/competência e permite remoção. PDFs originais não são arquivados; somente dados estruturados são persistidos.
7. Clicar em **Simular** após ao menos uma fatura válida e conferida, sem arquivos pendentes. Para histórico mais sólido, recomenda-se uma sequência de 12 competências.
8. Consultar economia, gráficos, premissas e memória de cálculo; baixar relatório PDF.
9. No CRM, o administrador pode consultar clientes/leads, executar simulações e novos cenários, corrigir dados com auditoria e gerar orçamento para posterior encaminhamento manual por e-mail.

## Configuração e versionamento

Nesta etapa, `.env` e `.env.example` de desenvolvimento podem ser commitados, conforme decisão do projeto. Devem conter apenas valores locais/sintéticos e credenciais exclusivas de demonstração. Credenciais reais de serviços e tokens pessoais ficam fora desses arquivos versionados.

Não versionar banco SQLite, faturas, dados reais de clientes, logs, temporários ou ambiente virtual. Antes de produção, separar segredos reais do Git e do contexto de build e usar a configuração da hospedagem. Adicionar um arquivo ao ignore futuramente não remove conteúdo já registrado no histórico.

## Migração futura para PostgreSQL e Docker

Preservar modelos e migrações portáveis desde o início. A validação executada agora é em SQLite; a validação PostgreSQL será requisito da preparação de produção.

Antes da migração:

1. Preparar `deploy/docker/` com Dockerfile, Compose, PostgreSQL, volume persistente e healthchecks.
2. Validar criação limpa e upgrade das migrações no PostgreSQL.
3. Fazer backup consistente do SQLite e interromper escritas durante a transferência.
4. Transportar dados de forma tipada, validando contagens, FKs, decimais, sequências de IDs quando aplicáveis e resultados dos relatórios.
5. Executar testes de integração e documentar retorno ao ambiente anterior.
6. Provisionar administrador real, sem fixtures/bypass de desenvolvimento, e habilitar controles de produção.

Mudar `DATABASE_URL` não transfere dados entre bancos. As instruções executáveis de migração serão registradas em `docs/DATABASE.md`; implantação e restauração ficarão em `docs/DEPLOYMENT.md`.

## Documentação a manter

| Arquivo | Conteúdo |
| --- | --- |
| `README.md` | Entrada do projeto, início rápido e fluxo de uso |
| `EcoWatt_PROJECT_SPEC.md` | Requisitos, arquitetura e critérios de aceite |
| `AGENTS.md` | Orientações curtas do agente e regras essenciais |
| `docs/STATUS.md` | Entrega corrente, verificações, pendências e próximo passo |
| `docs/phases/README.md` | Mapa dos planos de fase e orientação para novos chats |
| `docs/phases/phase-*.md` | Referências e ordem de execução de cada fase |
| `docs/SETUP.md` | Instalação local, comandos e solução de problemas, quando implementados |
| `docs/DATABASE.md` | Modelo relacional, migrações, seed e transporte dos dados |
| `docs/DEPLOYMENT.md` | Docker/PostgreSQL, configuração de produção, backups e restauração |

AGENTS.md, STATUS.md, SETUP.md e os planos por fase estão disponíveis. DATABASE.md e DEPLOYMENT.md continuam planejados; seus conteúdos operacionais serão escritos e verificados junto à implementação correspondente. Marcar checkboxes somente após cumprir os critérios de aceite, registrando limitações conhecidas.
