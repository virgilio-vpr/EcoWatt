# Ambiente local — Fase 1, entrega 1

Verificado em 06/11/2026 no Windows: Python 3.13.14, SQLite 3.50.4, uv 0.13.7. Use Python 3.13; outras versões ainda não foram validadas.

Na raiz, sem administrador ou ativação de scripts:

```powershell
python -m venv --without-pip .venv
python -m pip --python .venv install uv==0.13.7 --index-url https://pypi.org/simple
.\.venv\Scripts\uv.exe sync --locked --index-url https://pypi.org/simple
.\.venv\Scripts\python.exe -m uvicorn ecowatt.main:create_app --factory --host 127.0.0.1 --port 8000
```

O bootstrap com `venv`/ensurepip falhou nesta máquina. Foi usado pip do Python existente direcionado ao ambiente virtual, sem instalar pacotes globalmente. O fluxo `--without-pip` dispensa ensurepip. Acesso a PyPI, caches e temporários deve respeitar as políticas da máquina. Nenhuma alteração de ExecutionPolicy é necessária.

`uv.lock` fixa versões transitivas e hashes; `sync --locked` recusa divergência com pyproject. uv é ferramenta local de bootstrap, fixada acima; não é dependência da aplicação. Referência: [sincronização uv](https://docs.astral.sh/uv/concepts/projects/sync/).

O `.env` já contém valores sintéticos. `Settings` lê `.env` da pasta corrente, com prioridade das variáveis de ambiente. Execute na raiz. `DATA_DIR=data` reserva o diretório ignorado; `DATABASE_URL=sqlite:///data/ecowatt.sqlite3` reserva a conexão futura. A base não cria diretório, banco ou contas. Chaves e senhas de seed estão vazias e reservadas para entregas seguintes. Ambiente aceita development/test, e-mail somente disabled e banco somente SQLite nesta etapa. Produção será preparada em fase própria.

Health: `/api/v1/health`; OpenAPI: `/api/v1/openapi.json`; documentação: `/api/v1/docs`. Health é liveness, sem alegar disponibilidade de banco/migrações. A documentação interativa padrão depende dos assets externos do Swagger; não é a interface web do produto.

```powershell
.\.venv\Scripts\uv.exe lock --check
.\.venv\Scripts\uv.exe pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src
```

Resultados: lock atualizado, pacotes compatíveis, seis testes aprovados e compilação sem erros. Subida real Uvicorn verificada em loopback na porta 8765, consultando health/OpenAPI via HTTP; processo encerrado após a verificação. Os testes não usam faturas ou credenciais reais. O sandbox bloqueou caches/temporários; a execução autorizada fora dele passou, sem privilégios administrativos.

Dependências instaladas: FastAPI 0.162.0, Pydantic Settings 2.16.2, Uvicorn 0.54.0, HTTPX 0.28.1 e pytest 9.2.0; árvore completa em uv.lock. SQLAlchemy 2/Alembic serão adicionados com modelos/migrações na próxima entrega. Não há WAL/FKs, DecimalType, autenticação, seed, readiness do banco ou processamento de faturas implementados ainda. `db` e `web` reservam camadas separadas; não instalar OCR, PDF ou frontend agora.

PostgreSQL/Docker continuam na preparação de produção; nenhuma execução de container. Trocar DATABASE_URL futuramente não transfere dados. Decimais persistidos/JSON devem seguir os contratos, sem passagem por float.
