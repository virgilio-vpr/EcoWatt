# Ambiente local — Fase 1

Verificado em 06/11/2026: Windows, Python 3.13.14, SQLite 3.50.4, uv 0.13.7, SQLAlchemy 2.0.57 e Alembic 1.20.1. Outras versões de Python e PostgreSQL não foram validadas. Dependências e hashes estão no uv.lock.

## Instalação local

Na raiz, sem administrador ou ativação de scripts:

```powershell
python -m venv --without-pip .venv
python -m pip --python .venv install uv==0.13.7 --index-url https://pypi.org/simple
.\.venv\Scripts\uv.exe sync --locked --index-url https://pypi.org/simple
```

O ensurepip falhou na preparação inicial; o fluxo sem pip e bootstrap direcionado ao `.venv` foi conferido. Não há instalação global ou mudança de ExecutionPolicy. Acesso ao PyPI/caches/temporários deve respeitar a política da máquina; no agente, essas operações precisaram executar fora do sandbox, sem privilégios administrativos.

## Banco, seed e execução

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
$env:SEED_ADMIN_PASSWORD='LocalAdmin!12'
$env:SEED_CLIENT_PASSWORD='LocalClient!34'
try {
  .\.venv\Scripts\python.exe -m ecowatt.seed
  .\.venv\Scripts\python.exe -m ecowatt.seed
} finally {
  Remove-Item Env:SEED_ADMIN_PASSWORD
  Remove-Item Env:SEED_CLIENT_PASSWORD
}
.\.venv\Scripts\python.exe -m uvicorn ecowatt.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

As duas contas são exclusivamente sintéticas: admin@ecowatt.test e cliente@ecowatt.test. Senhas acima são exemplos locais realmente utilizados na verificação desta entrega. Se já existirem, o seed não altera senha, confirmação, papel ou empresa. Senhas só são exigidas para contas ausentes e passam pela política normal. As contas de fixture têm confirmação prévia registrada; cadastro público nunca recebe esse bypass. O seed não roda no startup e recusa ambientes fora de development/test.

O `.env` versionado mantém senhas e chaves vazias, e-mail disabled e apenas configuração sintética. Execute da raiz para carregar `.env`. Ambiente tem prioridade sobre arquivo. DATA_DIR reserva `data/`; o caminho efetivo do banco é DATABASE_URL. Somente Alembic prepara o diretório pai; app/seed não criam esquema automaticamente. SQLite, WAL/SHM, `.venv`, caches e dist ficam fora do Git. Não configurar arquivo em compartilhamento de rede; URLs UNC/URI são recusadas.

PUBLIC_ORIGIN define a origem exata dos comandos e dos futuros links de ativação; o cabeçalho Host não define links. HTTP só é aceito em loopback. COOKIE_SECURE=false no `.env` atende exclusivamente ao loopback HTTP; o padrão do código é true. Cookies são HttpOnly/SameSite=Strict, sem Domain, caminho `/`. Não há modo de produção habilitado nesta base.

## API e inspeção

- `/api/v1/health`: processo vivo, não verifica armazenamento.
- `/api/v1/ready`: arquivo local existente e revisão Alembic atual; não cria banco ausente e não afirma disponibilidade de e-mail.
- `/api/v1/openapi.json`: contrato de operações e erros.
- `/api/v1/docs`: índice HTML local, sem Swagger/CDN ou scripts inline.
- `/account`, `/account/simulations` e `/simulations/{id}`: inspeção autenticada, também em fragmentos HTMX. Há layout, macro e parcial; acabamento, formulários completos, Tailwind e seletor de temas ficam para a Fase 4.

Login é pela API nesta entrega. Exemplo Python/HTTPX verificado com servidor em execução (preserva cookie jar):

```python
import httpx

with httpx.Client(base_url="http://127.0.0.1:8000") as client:
    csrf = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    headers = {"Origin": "http://127.0.0.1:8000", "X-CSRF-Token": csrf}
    response = client.post("/api/v1/auth/login", headers=headers,
                           json={"email": "cliente@ecowatt.test", "password": "LocalClient!34"})
    response.raise_for_status()
    headers["X-CSRF-Token"] = response.json()["csrf_token"]
    assert client.get("/api/v1/me").json()["role"] == "client"
    assert client.get("/account").status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
```

Todos os POST/PATCH/DELETE exigem Origin e CSRF. O token CSRF é independente da credencial da sessão e deve ser atualizado após login. O token de sessão fica apenas no cookie HttpOnly; banco guarda SHA-256 de tokens aleatórios de 256 bits. Expiração padrão: 30 minutos por inatividade, 12 horas absoluta. Login substitui/revoga a sessão anterior apresentada; logout, redefinição, bloqueio e revogação geral invalidam sessões. Sessão expirada não impede obter novo CSRF e entrar de novo.

Listagens usam page/page_size (até 100). Criar simulação exige `Idempotency-Key` de 8–128 caracteres e JSON `{}`; cliente não escolhe dono/empresa. Admin seleciona dono em `/api/v1/admin/users/{owner_id}/simulations`. PATCH de unidade e DELETE usam expected_revision. A exclusão exige `confirm=true`. O catálogo seeded é explicitamente sintético, sem habilitar parser ou tarifas.

## Ativação e recuperação

Regras implementadas e testadas com MemoryMailer injetado: registro pendente e atômico, confirmação de e-mail/senha, hash Argon2id, ativação em 24h, recuperação em 30min, finalidade/uso único, reenvio invalidando token anterior e mensagens neutras. Links usam fragmento para não colocar tokens no access log. Não há inbox HTTP, token em logs ou disparo externo.

O runtime usa DisabledMailer. Cadastro, reenvio e recuperação retornam `503 email_unavailable` uniformemente enquanto faltar adaptador/provedor; não criam conta presa ou fingem envio. As telas para consumir links também não foram construídas. Definir o meio de entrega local e o provedor real continua pendente; esta limitação impede declarar a Fase 1 encerrada. Somente o seed sintético permite login imediato agora.

Limites persistidos SQLite: janela de uma hora, 10 tentativas por e-mail/finalidade e 50 por IP/finalidade; não há bloqueio permanente de conta por tentativa externa. Não confiar em X-Forwarded-For nesta configuração. Argon2id: 64 MiB, t=3, p=4; mediana local de hash+verificação 85,3ms em três amostras. Recalibrar no host e implementar rate limit de borda/MFA antes da produção. Rehash é aplicado no login quando necessário, conforme [argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/api.html).

## Verificações

```powershell
.\.venv\Scripts\uv.exe lock --check
.\.venv\Scripts\uv.exe pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src migrations
.\.venv\Scripts\uv.exe build --wheel
```

Resultado local: 40 testes aprovados, dependências compatíveis, lock atualizado e compilação sem erros. Migrações limpas/upgrade preservando dados, downgrade seguro em descartável, seed repetido, FKs, rollback, decimais, sessões/tokens, CSRF, acesso JSON/HTML/HTMX e concorrência foram conferidos. Uvicorn real em loopback: readiness, login admin/cliente, perfil, account, docs e logout; processo encerrado após o teste. Wheel construído, templates conferidos no artefato local ignorado. Workflow Windows/SQLite adicionado; seu resultado remoto deve ser consultado no GitHub, não inferido do teste local.

HTMX 2.0.11 é servido localmente, com licença e SRI em static/vendor. Não há eval, scripts processados em fragmentos ou CSS inline automático. Os testes conferem autorização do fragmento e disponibilidade do asset; interação visual no navegador ainda não foi testada.

Não instalar OCR, PDF ou Node agora. Nenhum container. Próximos passos e limites de retenção/worker estão em STATUS e DATABASE. Não usar clientes/faturas reais nesta base.
