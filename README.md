# EcoWatt

Sistema web para análise de faturas de energia do Grupo A. O repositório contém a API Laravel em `backend/`, a SPA React/TypeScript em `frontend/`, e a especificação em `docs/PROJECT_SPEC.md`.

## Roteiro de continuidade

A fonte da verdade é [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md); as instruções de execução ficam em [docs/AGENT.md](docs/AGENT.md).

Em 21/11/2026, a **Fase 11 foi encerrada no escopo local entregue até 11.5**. Em 26/11/2026, a **Fase 12 foi encerrada no escopo entregue até 12.2**, preservando medições e transferindo tarefas pendentes. O próximo passo é **13.1 — diagnóstico e avaliação tecnológica**. Fase 13: extração inteligente, adaptativa e multimodal, com Plano B preferencial condicionado à prova de conceito 13.2 e aprovação explícita. Fase 14: desempenho, concorrência e controle operacional (incluindo protocolo único e limites de custos). Fase 15: implantação e pendências finais. Os detalhes e testes ficam no [spec](docs/PROJECT_SPEC.md). Nenhuma dessas novas tarefas foi implementada nesta revisão documental.

No estado atual, o envio individual lê cada documento durante a requisição e o cálculo das faturas salvas também ocorre pela API. O OCR permite uma leitura por vez por host/volume e pode responder que está ocupado. A fila `database` já existe para o fluxo antigo em lote e o e-mail do fluxo atual. A tarefa 12.1 entregou a instrumentação opcional e a linha de base sintética documentadas abaixo. A tarefa 12.2 validou a cópia para o sistema de arquivos Linux do WSL. As próximas fases preveem LLM sob demanda para layouts desconhecidos ou falhas de leitura, padrões declarativos homologados reutilizados por PDF/OCR, biblioteca central sem dados pessoais, leitura assíncrona, concorrência controlada, eliminação de trabalho repetido, avaliação do cálculo, cache, testes com 1/3/5 usuários simultâneos e preparação de desempenho para produção. A leitura atual continua operacional; cálculos permanecem determinísticos. Essas próximas tarefas permanecem pendentes; não houve teste de carga que comprove cinco usuários simultâneos.

Para retomar em outro chat:

> Leia docs/AGENT.md e a seção 0 de docs/PROJECT_SPEC.md. Inicie exclusivamente a Fase 13 pela tarefa 13.1, seguindo as referências e os critérios de teste; preserve o trabalho local existente e as regras de cálculo.

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

No WSL, arquivos em `/mnt/c` exigem acesso ao sistema de arquivos do Windows. Para desenvolvimento com menor latência também na instalação, compilação e testes, prefira manter o projeto no sistema de arquivos Linux, por exemplo `~/projetos/EcoWatt`, e abri-lo com o VS Code conectado ao WSL. O PostgreSQL pode continuar no Docker Desktop.

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

## OCR de faturas — entrega local da etapa 11.5

A Fase 11 está encerrada nesse recorte. As instruções abaixo descrevem a instalação e as limitações locais atuais; a evolução adaptativa pertence à Fase 13, otimizações à Fase 14 e implantação/validação final à Fase 15, conforme o [spec](docs/PROJECT_SPEC.md).

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

## Desempenho — tarefa 12.1

A instrumentação é opcional: `PERFORMANCE_METRICS_ENABLED=true` no backend ativa eventos `performance_stage` no logger configurado. Reinicie API e workers após mudar a configuração. O padrão é desativado. Os eventos medem atendimento HTTP dentro da aplicação PHP, validação do upload, contagem de páginas, extração nativa, leitura completa, OCR e seus subprocessos (motor, metadados, renderização, preparação e reconhecimento), transações de persistência, cálculo e geração de PDF. Cada operação recebe um identificador aleatório; etapas aninhadas compartilham esse identificador, sem associá-lo ao cliente ou à fatura. Nenhum dado da requisição, SQL, binding, caminho, texto de exceção ou saída de processo é incluído nesses eventos.

Os tempos e contadores das etapas são inclusivos: não some pai e filhos. `cpu_ms` mede o processo PHP; `child_cpu_ms`, filhos encerrados, incluindo OCR, em sistemas com `getrusage`. `php_peak_bytes` é o pico acumulado do processo PHP e `child_peak_rss_kib` é o maior RSS acumulado dos filhos no Linux; esses picos não são o consumo exclusivo da etapa nem a soma da memória simultânea. Reutilização de processos mantém os picos anteriores. Consultas são contadas por etapa, com tempo e agrupamento por SHA-256 do SQL parametrizado e tabela de uma lista fixa; os primeiros 64 grupos são detalhados, mas o total inclui todos. Consultas que falham antes de emitir `QueryExecuted` não entram nessa contagem.

Jobs registram tentativas e resultado. Na fila `database`, `queue_wait_ms` mede o tempo desde `available_at` até o início do atendimento, descontando o atraso programado; a precisão do timestamp da fila é de um segundo. Outras filas deixam o campo nulo. O tempo do job inclui sua execução, sem a espera. Interrupção abrupta do processo pode impedir o evento final: ausência de evento final não comprova sucesso.

Metas iniciais para comparação, definidas antes de avaliar ganhos: upload nativo aquecido p95 ≤ 2 s; cálculo aquecido de até 12 meses p95 ≤ 3 s; geração de PDF aquecida p95 ≤ 1 s; consultas leves p95 ≤ 500 ms durante processamento; espera de job pronto com worker ocioso p95 ≤ 2 s. Manter o limite de OCR de 40 s por documento, sem reduzir a qualidade. Meta inicial de vazão para a tarefa 14.9 (transferida de 12.8): concluir os 60 documentos sintéticos de cinco usuários em até 10 minutos, preservando integridade e ausência de erros inesperados. São metas a validar no ambiente documentado, sem garantia de capacidade; a amostra de 12.1 é sequencial e pequena, não estima p95 nem demonstra concorrência.

A amostra reproduzível usa SQLite em memória, contas sintéticas, e-mail falso e temporários isolados; exercita as fixtures nativa, PNG/OCR, digitalizada e híbrida, com três jornadas de importação/cálculo/PDF por formato e uma passagem pelo worker `database`. Confira também igualdade dos campos normalizados, crédito negativo e limpeza. Execute em `backend/`:

```bash
ECOWATT_RUN_BASELINE=1 vendor/bin/phpunit tests/Feature/PerformanceBaselineTest.php
```

O resultado contém uma linha JSON `ECOWATT_BASELINE=` com ambiente e medições reais. O primeiro uso de cada formato é separado das duas repetições aquecidas na mesma aplicação; isso não esvazia caches de disco nem representa início frio do sistema operacional. Para medir inicialização PHP/aplicação, execute o comando em processos novos e use `/usr/bin/time -v`, registrando o tempo total separadamente; esse tempo inclui PHPUnit, preparação, asserções e inicialização e não deve ser apresentado como latência HTTP. Use os mesmos comandos e fixtures ao comparar ambientes na 12.2.

Referência medida em 21/11/2026: [dados por etapa e hashes das fixtures](docs/performance-baseline-12.1.json). Ambiente WSL2, kernel 6.18.58.1, Xeon E5-2678 v3, 24 CPUs lógicas visíveis e 7.858 MiB de RAM no WSL; projeto em `/mnt/c`, PHP 8.5.12/Laravel 13.38.0, OPcache CLI desativado, SQLite em memória e OCR local Tesseract 5.3.4/Poppler 24.02.0, uma thread. Métricas capturadas em memória pelo teste; escrita em disco do logger e transporte HTTP não foram medidos. A inicialização da aplicação levou **6.128,793 ms**, separada das etapas abaixo; o comando completo levou 60,35 s, incluindo bootstrap, banco de teste, asserções e todas as jornadas. CPU total observada pelo `time`: 18,21 s em usuário e 4,22 s em sistema; RSS máximo observado: 140.560 KiB. Pico PHP reportado pelas etapas: 71,50 MiB. Não havia limite de memória PHP nesse processo CLI; os limites próprios dos subprocessos OCR permaneceram ativos.

| Formato | Método confirmado | Upload no primeiro uso (ms) | Upload aquecido, duas repetições (ms) | Leitura aquecida (ms) |
|---|---|---:|---:|---:|
| PDF nativo | nativo | 1.142,085 | 136,386–137,341 | 70,847–72,685 |
| PNG | OCR | 1.874,760 | 1.814,411–1.816,172 | 1.723,746–1.725,931 |
| PDF digitalizado | OCR | 3.890,654 | 3.855,075–3.882,181 | 3.764,742–3.793,671 |
| PDF híbrido | híbrido | 3.230,717 | 3.229,364–3.259,509 | 3.159,113–3.189,855 |

Os uploads são chamadas sintéticas ao kernel Laravel, incluindo validação e persistência. O primeiro formato também carrega classes pela primeira vez; os demais primeiros usos já compartilham a aplicação carregada. Cálculos aquecidos de **um mês** levaram 13,410–13,993 ms; geração de PDF aquecida, 40,708–43,654 ms. O job nativo do fluxo em lote levou 292,799 ms, com espera observada de 996,451 ms, incluindo a imprecisão de até um segundo do timestamp. Todos os 13 fluxos concluíram sem erro; os 12 fluxos individuais preservaram os campos normalizados e descartaram os originais. Esses dados não validam ainda as metas para 12 meses ou cinco usuários.

Mapa inicial de chamadas e consultas para as próximas tarefas:

- `InvoiceUploadValidator::validate` conta páginas e `ImportInvoiceIntoSimulation::handle` volta a contá-las. Cada PDF individual provoca duas análises de contagem e uma extração Smalot; PDFs com OCR ainda consultam `pdfinfo`. Não foi aplicado reaproveitamento nesta tarefa.
- `LocalInvoiceOcr::extractDocument` consulta a versão do Tesseract em cada leitura. Na amostra aquecida, renderizar os PDFs digitalizados custou 1,39–1,40 s e reconhecê-los, 1,90–1,92 s; no híbrido, 0,97–0,98 s e 1,70–1,73 s, respectivamente. Esses são os principais custos das jornadas aquecidas medidas.
- O upload individual fez 31 consultas: inclui verificações prévias, sua repetição dentro do lock e inserção individual dos 11 itens. Essas repetições protegem a consistência; eventual otimização precisa manter a mesma proteção. A etapa de cálculo individual fez oito consultas, seis com o formato de parâmetros regulatórios e duas de tarifas. O agrupamento por SQL não compara bindings: formatos repetidos podem buscar chaves/vigências diferentes e não comprovam redundância.
- `RegulatoryParameterService` já reutiliza resoluções na instância; `TariffService` consulta por resolução. `ReportTariffMigrationService` e o motor chamam a calibração, e otimização/conciliação chamam o faturamento várias vezes. O mapa registra os pontos a investigar, sem introduzir cache ou mudar os cálculos.

Para repetir apenas um formato em um processo novo, acrescente `ECOWATT_BASELINE_SCENARIO=native.pdf` (ou `invoice.png`, `scanned.pdf`, `hybrid.pdf`). O campo `application_boot_ms` registra a inicialização da aplicação nesse processo separadamente do primeiro uso e das repetições aquecidas. O ambiente medido contém o OCR configurado localmente; outra instalação precisa dos executáveis e idiomas descritos na seção de OCR.

## Cópia para o WSL — tarefa 12.2

**Concluída em 22/11/2026, após autorização explícita.** A pasta ativa é `/home/vpr/projetos/EcoWatt`, em ext4 no Linux do WSL. A origem em `/mnt/c/users/virgi/documents/projetos/ecowatt` foi preservada; seus servidores foram parados. PostgreSQL permanece no mesmo container e volume. API e frontend de desenvolvimento foram iniciados a partir da cópia, nas portas 8000 e 5173. Os 19 jobs existentes continuam pendentes; o worker foi validado em uma fila PostgreSQL vazia e nos cenários E2E com SMTP/SQLite isolados.

Os comandos de cópia abaixo registram o procedimento e servem para novas instalações. A pasta de destino existente é bloqueada pela ferramenta; para outra cópia, escolha um novo nome. O padrão continua sendo apenas apresentar o plano.

A ferramenta [docs/wsl_workspace.py](docs/wsl_workspace.py) usa Python 3 e `findmnt` (util-linux). Por padrão, ela apenas faz o inventário e apresenta um plano, sem criar o destino, iniciar processos ou acessar o banco. Na raiz do projeto:

```bash
python3 docs/wsl_workspace.py --destination "$HOME/projetos/EcoWatt"
```

O plano informa a quantidade de arquivos, o sistema de arquivos de destino, locks do Git, originais pendentes e as **chaves** de OCR a ajustar. Não imprime segredos ou conteúdo dos arquivos. Para esta instalação, os wrappers em `backend/storage/ocr-local/bin/` localizam o runtime por caminhos relativos; a pasta `backend/storage/ocr-local/` precisa acompanhar a cópia inteira.

A cópia e os hashes usam até oito operações de I/O em paralelo. O modo explícito de cópia preserva `.git` (incluindo index/staging), arquivos alterados, não rastreados e ignorados, dependências, documentos privados e backups. O destino é privado, com permissões 0700 nos diretórios e 0600 nos arquivos de ambiente. Somente os valores de `OCR_TESSERACT`, `OCR_PDFTOPPM`, `OCR_PDFINFO`, `OCR_PYTHON` e `OCR_LOCK_PATH` que começam com o caminho absoluto da origem são redirecionados no **backend/.env copiado**; caminhos externos são mantidos. Variações de maiúsculas/minúsculas no caminho Windows são aceitas quando apontam comprovadamente para o mesmo diretório. `APP_KEY`, credenciais do banco e as demais linhas dos arquivos de ambiente são preservadas. Valores com aspas e finais de linha são conservados. Outros caminhos absolutos personalizados exigem revisão privada no destino.

Os `.gitignore` das pastas de runtime são preservados e os diretórios vazios necessários ao Laravel são preparados. Caches PHP gerados em `backend/bootstrap/cache`, dados de cache/sessões/views/testes em `backend/storage/framework`, `frontend/dist` e o lock padrão do OCR são regenerados no destino. A pasta de documentos temporários não é copiada; a ferramenta bloqueia a execução enquanto houver originais nela. Links internos são preservados, com redirecionamento dos links absolutos para a cópia. Links externos, `.env` vinculado por symlink, worktrees com `.git` externo e locks do Git exigem revisão antes de copiar. Não há sobrescrita de destino existente. Arquivos regulares são conferidos por SHA-256, e a origem é verificada novamente; alterações durante a operação invalidam a cópia. Uma cópia incompleta é mantida para inspeção e não é reutilizada automaticamente.

### Antes da cópia real

1. Confirme o destino novo e espaço suficiente para todo o projeto, incluindo dependências, OCR e backups (`df -h "$HOME"` e `du -sh .`). Confira que o plano aponta para um sistema Linux local suportado, como `ext4`.
2. Aguarde a conclusão dos envios e dos jobs, interrompa os servidores e o worker de forma ordenada e pause as gravações do editor e de outras ferramentas. A origem permanece disponível para retomada. A confirmação `--source-paused` não interrompe processos por conta própria.
3. Preserve um backup lógico e confira que ele pode ser listado. Execute o bloco abaixo na origem, verificando o sucesso antes de continuar. Ele grava somente em `backend/storage/app/private/backups/`, com permissões privadas; não altera o banco.

```bash
(
  set -euo pipefail
  umask 077
  mkdir -p backend/storage/app/private/backups
  ecowatt_backup="backend/storage/app/private/backups/wsl-$(date +%Y%m%d-%H%M%S).dump"
  docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$ecowatt_backup"
  test -s "$ecowatt_backup"
  docker compose exec -T postgres pg_restore --list < "$ecowatt_backup" > /dev/null
)
```

4. Registre localmente o commit, o `git status --short`, o container/volume em uso e o resultado de `php artisan db:show --counts` em `backend/`. Mantenha esses registros e backups privados. O Compose fixa `name: ecowatt` e o volume `ecowatt_postgres_data`; a mesma configuração na cópia deve apontar para esse banco existente. A etapa não recria tabelas, não roda seeders, não restaura o dump e não remove volumes.
5. Depois da autorização do destino, execute a cópia a partir da raiz original. O diretório pai pode ser criado; a pasta final precisa continuar inexistente. Só use `--source-paused` depois de cumprir o passo 2.

```bash
mkdir -p "$HOME/projetos"
python3 docs/wsl_workspace.py \
  --destination "$HOME/projetos/EcoWatt" \
  --copy --source-paused
```

O resultado deve conter `"mode": "copied"` e `"verified": true`. Isso verifica a cópia dos arquivos; funcionamento da aplicação e desempenho ainda precisam dos passos seguintes. Em falha, preserve a origem e revise o destino incompleto antes de escolher uma nova pasta.

### Verificação no destino

Abra a pasta Linux com o editor conectado ao WSL. Antes de executar a aplicação, confira o mesmo commit e estado local do Git, a existência dos backups, os executáveis de OCR e os caminhos personalizados; mantenha segredos fora de saídas compartilhadas. Confirme PHP 8.5.12+, Node 24+ e os mesmos idiomas/versões do OCR. As dependências acompanham a cópia; reinstalações, se necessárias, devem respeitar os lockfiles existentes.

Em `backend/`, confira o banco somente em leitura com `php artisan db:show --counts` e compare os registros anteriores. Em `docker compose ps`, confirme o mesmo serviço PostgreSQL. A chave da aplicação e as credenciais permanecem as existentes. Inicie API, frontend e worker pelos comandos de desenvolvimento deste README, com a origem parada; confira a navegação e a disponibilidade dos dados já existentes. Para a jornada sintética sem e-mail real ou alteração do banco restaurado, use o teste E2E isolado.

Execute no destino, nesta ordem, com cada comando aprovado antes do próximo:

```bash
cd backend
php artisan test --compact
ECOWATT_RUN_BASELINE=1 /usr/bin/time -v vendor/bin/phpunit tests/Feature/PerformanceBaselineTest.php
cd ../frontend
npm run test
npm run test:e2e
```

O E2E inicia API, frontend compilado e worker reais com SQLite e SMTP temporários. Os caminhos locais do OCR podem ser passados como no roteiro de OCR deste README. `scribe:generate`, executado pela suíte, pode atualizar arquivos gerados; compare com o estado registrado e preserve o trabalho local.

Compare o JSON `ECOWATT_BASELINE=` com [a referência da 12.1](docs/performance-baseline-12.1.json), mantendo as mesmas fixtures, versões, OPcache, limites e número de workers. Execute as medições sem outras suítes simultâneas; separe bootstrap, primeiro uso e repetições aquecidas. Registre tempos por etapa, CPU, memória e eventual ganho ou ausência dele. O teste usa um disco temporário exclusivo dentro do projeto, portanto acompanha o sistema de arquivos do destino.

Somente após validar arquivos, dados existentes, API, OCR, worker, testes/build e comparação de desempenho, considere a instalação copiada aprovada. A pasta e o banco originais permanecem disponíveis. A recuperação consiste em parar os processos da cópia e retomar a origem, que utiliza o mesmo banco preservado; mudanças futuras no banco precisam de avaliação própria e não são desfeitas por alternar pastas.

Teste automatizado da ferramenta, com projetos e segredos sintéticos em `/tmp`, sem copiar esta instalação nem acessar PostgreSQL:

```bash
cd backend
vendor/bin/phpunit tests/Unit/WslWorkspaceCopyTest.php
```

### Resultados da validação e comparação

Foram aprovados 384 testes da API (mais a amostra opcional executada separadamente), 137 testes do frontend, os dois cenários E2E com 1 e 12 faturas, build e ESLint. Os testes reais de OCR também passaram. Os estados e contagens do banco foram conferidos antes e depois; os arquivos de ambiente e o backup foram verificados sem exibir segredos. A cópia inicial conferiu a integridade de 27.079 entradas, incluindo arquivos e links; os quatro `.gitignore` de runtime foram preservados na cópia e na ferramenta.

A validação encontrou dois problemas nos testes existentes: a espera de um segundo não cobria o lote completo de 12 arquivos no frontend, e o E2E reutilizava uma fixture de cálculo cujo total não fechava. A espera específica agora cobre a conclusão do lote, e o E2E usa `enel-e2e-balanced-blue.txt`, conferida pelo leitor em decimal: total R$ 95.042,77, medições de 221,760/269,641 kW e reativos de R$ 54,42. O arquivo de referência anterior, os valores dos clientes, o leitor e as regras de cálculo foram preservados.

Medições em processos PHP novos, executadas em sequência nas duas pastas, com as mesmas fixtures, versões e opções da 12.1. Foram três jornadas por formato: primeiro uso e duas repetições aquecidas. Dados por etapa, CPU/memória, ambiente e hashes em [docs/performance-comparison-12.2.json](docs/performance-comparison-12.2.json).

| Cenário | Mediana aquecida em `/mnt/c` (ms) | Mediana aquecida no Linux (ms) | Redução observada |
|---|---:|---:|---:|
| Upload de PDF nativo | 151,472 | 26,264 | 82,66% |
| Upload de PNG/OCR | 1.929,311 | 1.265,607 | 34,40% |
| Upload de PDF digitalizado | 4.138,775 | 2.655,360 | 35,84% |
| Upload de PDF híbrido | 3.414,275 | 2.210,229 | 35,27% |

O bootstrap da aplicação passou de 6.303,867 para 162,128 ms. O comando completo da amostra passou de 66,64 para 20,11 s; CPU em usuário, de 19,40 para 18,20 s; CPU em sistema, de 6,54 para 1,83 s. O RSS máximo observado foi de 140.636 para 141.748 KiB. Esses valores incluem o processo de teste e seus filhos; as definições de picos e etapas inclusivas continuam as da 12.1.

A amostra é sequencial, com banco sintético em memória e sem transporte HTTP; não calcula p95 nem comprova capacidade concorrente. Os caches do sistema operacional não foram esvaziados. O frontend usa agora a observação nativa de arquivos prevista no Vite para pastas Linux; a preparação de produção e os testes de carga permanecem nas tarefas seguintes. Para continuar, abra `/home/vpr/projetos/EcoWatt` no editor conectado ao WSL e siga pela **12.3**.
