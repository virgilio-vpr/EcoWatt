# EcoWatt

Sistema web para análise de faturas de energia do Grupo A. O repositório contém a API Laravel em `backend/`, a SPA React/TypeScript em `frontend/`, e a especificação em `docs/PROJECT_SPEC.md`.

## Atualização de EnerDiag para EcoWatt

O nome foi atualizado na interface, nos e-mails, relatórios e documentação. O ícone foi preservado; apenas os nomes dos arquivos de imagem foram atualizados. O navegador migra automaticamente o tema e a identificação do envio de faturas em andamento para as novas chaves, no mesmo domínio.

O banco e o usuário PostgreSQL desta instalação foram migrados de `enerdiag` para `ecowatt`, preservando os dados e a senha existente. Os arquivos `.env` da raiz e do backend usam `DB_DATABASE=ecowatt` e `DB_USERNAME=ecowatt`. Mantenha `DB_PASSWORD` e `APP_KEY` existentes; a mudança não exige recriar tabelas ou executar os seeders. Alterar apenas os nomes nos arquivos `.env` não renomeia um banco já existente.

O Docker Compose fixa o projeto como `ecowatt`: container `ecowatt-postgres-1` e volume `ecowatt_postgres_data`. A migração copiou o volume com o PostgreSQL parado e preservou `enerdiag_postgres_data` como cópia de recuperação offline. Os backups lógicos e das configurações ficam em `backend/storage/app/private/backups/`, sem versionamento. Após alterar configurações de conexão, reinicie servidores e trabalhadores em execução. Ao mudar a pasta, ajuste também caminhos absolutos personalizados, incluindo os executáveis OCR em `backend/.env`.

A renomeação do repositório no GitHub e a da pasta local são independentes da atualização do conteúdo. Depois de renomear o repositório para `EcoWatt` nas configurações do GitHub, atualize a origem do clone com `git remote set-url origin https://github.com/virgilio-vpr/EcoWatt.git`. Execute esse comando somente após confirmar a renomeação remota. Reabra a pasta `EcoWatt` no editor após a mudança local.

Os contatos `contato@ecowatt.example` e `noreply@ecowatt.example` são fictícios. Configure os endereços reais em `backend/resources/company-contact.json` e `MAIL_FROM_ADDRESS` antes de enviar e-mails reais. A variável `ECOWATT_TERMS_VERSION` substitui `ENERDIAG_TERMS_VERSION`, que continua aceita como compatibilidade.

## Pré-requisitos

- PHP 8.5.12 ou superior, com `pdo_pgsql`
- Composer
- Node.js 22.12 ou superior e npm
- Docker com Docker Compose e acesso ao daemon

Confira as versões no terminal:

```bash
php -v
php -m | grep pdo_pgsql
composer --version
node --version
npm --version
docker compose version
```

No Codespace deste projeto, o PHP 8.5 fica em `$HOME/.config/herd-lite/bin`. Se `php -v` mostrar uma versão anterior, ative-o nesta sessão antes dos comandos PHP e Composer:

```bash
export PATH="$HOME/.config/herd-lite/bin:$PATH"
php -v
```

## Configuração local

Na raiz do repositório, crie os arquivos de ambiente a partir dos exemplos:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Defina uma senha local para PostgreSQL em `DB_PASSWORD` nos dois arquivos. Mantenha estes valores iguais:

```dotenv
DB_CONNECTION=pgsql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=ecowatt
DB_USERNAME=ecowatt
DB_PASSWORD=sua_senha_local
```

O `.env` da raiz fornece as credenciais ao Docker Compose; `backend/.env` configura o Laravel. Não versione arquivos `.env`.

## Iniciar o banco

Na raiz do repositório:

```bash
docker compose up -d
docker compose ps
docker compose exec -T postgres pg_isready -U ecowatt -d ecowatt
```

## Instalar e iniciar a API

```bash
cd backend
composer install
php artisan key:generate
php artisan migrate
php artisan scribe:generate
php artisan serve --host=0.0.0.0
```

A API ficará disponível na porta 8000, com a documentação em `/docs` e o OpenAPI em `/docs.openapi`.

O comando `serve` mantém as dependências em OPcache para reduzir a inicialização das requisições. Os diretórios da aplicação, rotas e configurações ficam fora desse cache, de modo que alterações nesses arquivos aparecem imediatamente. Reinicie a API após instalar ou atualizar dependências com Composer. A primeira requisição após iniciar o servidor aquece o cache e pode levar mais tempo.

No WSL, arquivos em `/mnt/c` exigem acesso ao sistema de arquivos do Windows. Para desenvolvimento com menor latência também na instalação, compilação e testes, prefira manter o projeto no sistema de arquivos Linux, por exemplo `~/projetos/ecowatt`, e abri-lo com o VS Code conectado ao WSL. O PostgreSQL pode continuar no Docker Desktop.

Em outro terminal, mantenha o processamento das simulações ativo:

```bash
cd backend
php artisan queue:work database --queue=default --tries=3 --timeout=300
```

As faturas já salvas são calculadas diretamente pela API ao clicar em Simular relatório. O trabalhador processa o envio do relatório por e-mail e as importações pelo fluxo antigo em lote. Após alterar código do backend, reinicie o trabalhador. O `DB_QUEUE_RETRY_AFTER` deve ser maior que o timeout de 300 segundos; o padrão é 360 segundos.

## Instalar e iniciar o frontend

Em outro terminal, na raiz do repositório:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

O Vite ficará disponível na porta 5173.

## Verificações e auditorias

Na pasta `backend/`:

```bash
php artisan test
./vendor/bin/pint
composer audit
```

Na pasta `frontend/`:

```bash
npm run test
npm run lint
npm run build
npm audit
```

## OCR de faturas — etapa 11.5

O seletor aceita PDF, PNG e JPEG. PDFs mantêm a leitura nativa pelo Smalot; Tesseract local apoia leituras incompletas e processa imagens. Instale no Ubuntu/Debian antes de iniciar a API e o worker:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-por tesseract-ocr-eng poppler-utils util-linux python3 python3-pil
tesseract --version
tesseract --list-langs
pdftoppm -v
```

Validação executada com Tesseract 5.3.4 e Poppler 24.02.0. Idiomas: `por+eng`; [opções oficiais do Tesseract](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html). `prlimit` (util-linux) limita recursos dos subprocessos. Python 3 com Pillow separa os quadros ENEL por suas bordas azuis e amplia cada quadro dentro do limite de 20 MP; não reconhece nem altera números. Configure `OCR_PYTHON` se o interpretador não estiver em `/usr/bin/python3`. Não há dependência nova de Composer/npm. Em instalações fora do PATH, configure `OCR_TESSERACT`, `OCR_PDFTOPPM` e `OCR_PDFINFO` no `backend/.env`, apontando para executáveis. Reinicie API/worker após mudar a configuração.

Nesta estação, os pacotes foram instalados sem sudo em `backend/storage/ocr-local/`, com executáveis wrapper em `bin/` e os caminhos de OCR/Python já configurados no `.env` local. Esse diretório é ignorado pelo Git e não depende de `/tmp`; não o copie para produção. Instale os pacotes do sistema em produção.

Para conferir uma fatura local imediatamente, sem iniciar banco ou frontend:

```bash
cd backend
php artisan invoices:inspect tests/Fixtures/ocr/invoice.png
php artisan invoices:inspect tests/Fixtures/ocr/scanned.pdf
php artisan invoices:inspect tests/Fixtures/ocr/hybrid.pdf
php artisan invoices:inspect '../docs/1_Fatura - Janeiro_26.pdf'
```

O comando mostra todos os campos, a soma e a diferença, sem salvar documentos ou registros. Código de saída 0 indica fechamento; 2 indica diferença para revisão; 1 indica falha de leitura/validação. O JSON contém os dados da fatura escolhida: execute apenas no seu terminal privado.

Para testar o leitor sem banco de produção:

```bash
cd backend
vendor/bin/phpunit tests/Feature/InvoiceDocumentReaderTest.php tests/Feature/LocalInvoiceOcrTest.php tests/Unit/InvoiceImageUploadTest.php tests/Feature/ProvidedInvoiceDocumentsTest.php
```

`LocalInvoiceOcrTest` executa o motor real: PNG, JPEG, PDF digitalizado, PDF com texto, PDF híbrido e imagem ENEL com quadros coloridos devem produzir os mesmos 11 itens de `tests/Fixtures/ocr/expected.txt`, total R$ 1.189,75, crédito DIC -R$ 10,25, ICMS e medições de 40/50 kW. A ausência do motor pula os casos de integração que dependem do motor real, sendo explicitada no resultado; os testes de falha e timeout continuam obrigatórios. Os PDFs privados em `docs/` são opcionais e não devem ser versionados. Nos originais com texto, janeiro/2026 fecha R$ 15.737,88 e dezembro/2025 R$ 13.174,31, unidade MTE0015497.

Para teste manual com a instalação normal, inicie banco, API e frontend conforme as seções anteriores e abra `http://localhost:5173`. Entre na conta, inicie um envio com ENEL SP e selecione uma fixture por vez; as fixtures representam o mesmo mês e unidade, portanto remova a fatura salva antes de experimentar o formato seguinte. Confira os itens e impostos em “Ver itens”; documentos duplicados e meses repetidos continuam bloqueados. Depois experimente as faturas reais de `docs/`.

Também é possível usar o ambiente isolado de desenvolvimento já existente, com SQLite e caixa de e-mail local, sem PostgreSQL ou envios reais:

```bash
cd frontend
npm run build
OCR_PYTHON="$PWD/../backend/storage/ocr-local/bin/python3" OCR_TESSERACT="$PWD/../backend/storage/ocr-local/bin/tesseract" OCR_PDFTOPPM="$PWD/../backend/storage/ocr-local/bin/pdftoppm" OCR_PDFINFO="$PWD/../backend/storage/ocr-local/bin/pdfinfo" node e2e/serve.mjs
```

Abra `http://127.0.0.1:18762`, cadastre uma conta e obtenha o código em `http://127.0.0.1:18764/messages`. Dados desse ambiente são apagados ao encerrá-lo com Ctrl+C. Os caminhos dos executáveis são necessários nessa alternativa porque ela não carrega o `.env` do projeto. Para instalação global, omita as variáveis. Node 24+ é necessário para esse servidor.

Limites: 20 MB/arquivo, 120 MB/simulação, 12 arquivos e 600 páginas totais; imagens entre 300 e 10.000 pixels por lado, até 20 MP. OCR: até 4 páginas/arquivo, 40 segundos por tentativa, uma leitura concorrente por volume, uma thread e até 768 MiB de espaço de endereçamento por subprocesso. O proxy precisa permitir ao menos 60 segundos por requisição. Lotes com muitas páginas que exigem OCR podem atingir o orçamento de 240 segundos; prefira o envio sequencial nesses casos. PDFs maiores continuam aceitos para leitura nativa suficiente, mas precisam ser separados se exigirem OCR.

A fatura `docs/7_Fatura - Julho_26.pdf` é um PDF inteiramente digitalizado, incluindo verso informativo; na validação local, o reconhecimento excedeu 40 segundos. O texto obtido em tentativas isoladas perdeu dígitos e vírgulas em tabelas, portanto a importação permanece bloqueada. A mensagem distingue timeout de falha do motor e da etapa de reconhecimento; os logs registram apenas etapa, motivo e código de saída, sem texto da fatura.

A imagem local `docs/Code_Generated_Image.png` é reconhecida com referência 01/2026, unidade MTE0015497, demanda contratada 57,000 kW e demandas medidas de ponta/fora de ponta de 40,488/51,072 kW. Os 13 itens fecham R$ 15.737,88; preços e impostos são conferidos com o PDF nativo de janeiro. Rótulos Mês/Ano separados de seus valores por textos de outras colunas são associados somente dentro do cabeçalho delimitado; emissão e vencimento não substituem a referência. Na fonte OCR, pontos e vírgulas decimais são interpretados na escala declarada de cada coluna, sem completar dígitos; a leitura nativa permanece estrita.

Limitações: o leitor continua específico para layouts ENEL suportados; fotos inclinadas, tabelas densas, fontes pequenas e baixa nitidez podem não ser reconhecidas. Não se reconstituem vírgulas ou números presumidos. Divergências entre fontes bloqueiam a importação; diferenças no fechamento impedem simulação e exigem nova cópia. Se somente o apoio OCR falhar, a leitura nativa estruturada fica disponível com aviso para conferência. Não há edição manual de números nesta etapa. Documentos são apagados em `finally`, inclusive timeout; interrupção abrupta do worker é coberta por `php artisan invoices:clean-temporary-files` (agendado diariamente, órfãos com mais de uma hora). O lock privado de concorrência permanece fora da pasta dos documentos.
