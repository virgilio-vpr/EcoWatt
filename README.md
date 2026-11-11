# EcoWatt

Plataforma web para leitura de faturas de energia, simulação de potenciais de economia e geração de relatórios, com área do cliente e CRM administrativo.

## Estado atual

A Fase 0 foi concluída com aceite explícito do usuário em 06/11/2026 para os contratos e o gabarito mínimo local. A **Fase 1 está concluída para desenvolvimento local**, com 68 testes: persistência, autenticação/permissões, seed, simulações/unidades, SMTP sintético, cliente no Edge e cancelamento transacional de tarefas com rejeição de resultado tardio. SMTP permanece disabled por padrão e provedor externo não homologado. Não há homologação comercial ou ambiente de produção habilitado.

A fonte dos requisitos é [EcoWatt_PROJECT_SPEC.md](EcoWatt_PROJECT_SPEC.md). O checklist de implementação fica na seção 15 e a ordem de criação das tabelas na seção 10.4.

Contrato de uso da API, autenticação, códigos, paginação e retries em [docs/API.md](docs/API.md). O OpenAPI executável declara respostas tipadas e os requisitos de cookie, CSRF e Origin. O cliente local de autenticação usa `api-client.js`, sem retry automático de escritas.

O [controle de tarefas](docs/TASKS.md) guarda somente metadados/leases, sem documentos. Não inicia workers; o coordenador e os adaptadores reais de leitura entram na Fase 2, usando a confirmação transacional já protegida contra exclusão/revisão.

Para iniciar uma tarefa, consulte [AGENTS.md](AGENTS.md), [docs/STATUS.md](docs/STATUS.md) e o [plano da fase](docs/phases/README.md). Esses arquivos orientam a leitura seletiva da SPEC e registram o ponto de retomada; não substituem os requisitos completos.

O usuário autorizou commits diretos em `virgilio-vpr/EcoWatt`, sem confirmação adicional no site. Preferir a integração GitHub, sem exigir Git instalado. Ao concluir cada entrega, revisar os arquivos, preservar alterações remotas e informar o commit realizado. Enviar somente os documentos e códigos da entrega; faturas e planilhas reais permanecem locais. Commits pela integração não sincronizam automaticamente outros arquivos da pasta local.

Os documentos da Fase 0 estão no [dicionário de faturas](docs/contracts/invoice-data.md), [contrato do pipeline](docs/contracts/pipeline.md), [matriz de acesso](docs/contracts/access.md), [inventário e dependências do corpus](docs/corpus/README.md) e [casos sintéticos](docs/corpus/synthetic-cases.md). Contratos e gabarito mínimo local foram aceitos; homologação comercial e publicação de fixtures reais continuam pendentes.

A continuação da Fase 0 inclui [conferência das planilhas](docs/corpus/workbook-review.md), [conferência inicial das faturas](docs/corpus/invoice-review.md) e [registro regulatório](docs/corpus/regulatory-review.md). Os relatórios preservam o histórico da análise; o aceite atual é limitado ao gabarito mínimo local. O [texto original de início da Fase 1](docs/phases/phase-01-start.md) é histórico; retome pelo STATUS atual.

A **Fase 2** já persiste resultados normalizados exclusivamente sintéticos (`0008_invoice_confirmation`): admissão/unidade salva, coordenador com subprocesso, valores/proveniência inicial, vínculo tarefa/fatura, revisão do conjunto e consulta/remoção JSON. GET `/api/v1/simulations/{id}/invoices` lista os dados estruturados; GET/DELETE por ID respeitam autorização e revisões. Todas as novas faturas ficam **needs_review**. **PDFs reais permanecem desabilitados**, inclusive ENEL: não há POST de upload; a confirmação é um comando JSON explícito. Contratos em [INVOICE-STORAGE](docs/INVOICE-STORAGE.md), [ADMISSION](docs/ADMISSION.md) e [COORDINATOR](docs/COORDINATOR.md); resultados em [STATUS](docs/STATUS.md). Execute a migração abaixo antes de usar a nova readiness. A [revisão JSON versionada](docs/INVOICE-REVIEW.md) já permite corrigir campos sintéticos, invalidar dependentes e consultar conferência financeira/pendências; A [confirmação/seleção versionada](docs/INVOICE-CONFIRMATION.md) já libera prontidão estrutural com uma fatura sintética válida, conferida e sem pendências; duplicatas/refaturamentos exigem escolha explícita. Complementos que precisem de consolidação permanecem bloqueados. Parser/OCR, isolamento homologado, cálculo e interface de leitura seguem pendentes; o coordenador não inicia automaticamente pela aplicação.

Em `/simulations/{id}/invoices`, o cabeçalho permite consultar suporte à versão de layout para a distribuidora cadastrada, via HTMX ou GET sem JavaScript. A consulta não envia arquivos nem inicia leitura. Upload e leitura real permanecem desabilitados, inclusive quando há suporte interno sintético. O canal de solicitação de contato ainda está pendente.

## Stack definida

A preparação de segurança documental está em
[docs/DOCUMENT-SECURITY.md](docs/DOCUMENT-SECURITY.md): orçamento de pixels/bytes
testado com buffers sintéticos, ainda sem renderer ou sandbox homologado. WSL
está fora da solução por decisão do usuário. Upload/leitura real seguem bloqueados.

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

Comandos de instalação em [docs/SETUP.md](docs/SETUP.md). Com `.venv` preparado e dependências sincronizadas pelo uv.lock, na raiz:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
$env:SEED_ADMIN_PASSWORD='LocalAdmin!12'
$env:SEED_CLIENT_PASSWORD='LocalClient!34'
try {
  .\.venv\Scripts\python.exe -m ecowatt.seed
} finally {
  Remove-Item Env:SEED_ADMIN_PASSWORD
  Remove-Item Env:SEED_CLIENT_PASSWORD
}
.\.venv\Scripts\python.exe -m uvicorn ecowatt.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

As senhas acima são exclusivamente sintéticas, usadas na conferência local. Contas: `admin@ecowatt.test` e `cliente@ecowatt.test`; seed repetido preserva senhas/dados existentes. O `.env` versionado mantém os campos de senha vazios. Banco em `data/ecowatt.sqlite3`, ignorado pelo versionamento.

Health `/api/v1/health` verifica o processo; readiness `/api/v1/ready` exige banco migrado. OpenAPI `/api/v1/openapi.json`; índice HTML local `/api/v1/docs`, sem Swagger/CDN. Login mínimo no navegador em `/auth/login`; cadastro em `/auth/register`. Páginas `/account` e `/simulations/{id}` exigem a mesma sessão da API; fragmentos HTMX também passam pela autorização. Para cliente HTTP, obtenha `/api/v1/auth/csrf`, preserve cookies e envie `Origin` e `X-CSRF-Token` nos comandos. Exemplo em [SETUP](docs/SETUP.md), SMTP e consumo dos links em [EMAIL](docs/EMAIL.md).

O seed nunca roda no startup e recusa ambientes fora de desenvolvimento/teste. Cadastro normal não recebe bypass de ativação. Com e-mail desabilitado, cadastro/reenvio/recuperação respondem 503 sem criar contas inacessíveis. Nenhum OCR, motor, worker, relatório, CRM ou interface completa foi antecipado.

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

Mudar `DATABASE_URL` não transfere dados entre bancos. Modelo e comandos locais estão em [docs/DATABASE.md](docs/DATABASE.md); transporte de dados e implantação/restauração continuam pendentes para produção.

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

AGENTS.md, STATUS.md, SETUP.md, DATABASE.md e os planos por fase estão disponíveis. DEPLOYMENT.md e instruções de transporte de dados continuam planejados. Marcar checkboxes somente após cumprir os critérios de aceite, registrando limitações conhecidas.
