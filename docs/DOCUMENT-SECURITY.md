# Segurança documental — preparação do adaptador

A Fase 2 tem orçamento de rasterização e backend experimental nativo do
Windows, exercitados somente com programas/buffers sintéticos. Nenhuma rota
recebe documentos; não há renderer/parser/OCR integrado. Admissão e
`normalized-invoice-v1` continuam sintéticos, inclusive ENEL. Upload/leitura
real permanecem bloqueados; nenhum critério integral de §15 foi concluído.
WSL e containers estão fora da solução neste ambiente, por restrição de
instalação informada pelo usuário. AppContainer é uma API já existente do
Windows; não houve instalação de infraestrutura ou mudança de política.

## Backend nativo Windows e alcance da evidência

`src/ecowatt/windows_isolation.py` usa ctypes/Win32, sem dependência nova,
ORM ou HTTP. É selecionável pelo coordenador exclusivamente sintético via
`WindowsExecutor`; o modo padrão `spawn` não tem essas garantias. Recebe executável interno e SID
de perfil previamente provisionado; não tem endpoint ou ingresso de documentos.

Cada processo nasce suspenso em AppContainer, sem capacidades solicitadas,
sem herança de handles por padrão; no IPC, herda somente stdin/stdout/NUL
pela lista explícita `PROC_THREAD_ATTRIBUTE_HANDLE_LIST`. Ambiente limitado a SystemRoot/WINDIR/LOCALAPPDATA
(necessário ao perfil) e diretório inicial Windows. Não herda PATH, proxies,
credenciais ou ambiente da API. O Job é atribuído atomicamente na criação
por PROC_THREAD_ATTRIBUTE_JOB_LIST, evitando órfão suspenso se o pai morrer
entre criação e atribuição. Antes de retomar a thread, o pai confere vínculo
ao Job e token efetivo: SID exato, AppContainer, integridade
baixa, sem elevação, sem capacidades e sem privilégios habilitados além de
SeChangeNotifyPrivilege, quando presente. Erro/divergência encerra o processo
suspenso, sem fallback. Isso rejeita capacidades implícitas observadas ao usar
diretamente a identidade de pacote do Python da Microsoft Store.

O Job sem nome/handle herdável e sem permissão de breakaway limita memória
comprometida agregada a até 1.000.000.000 bytes, CPU agregada em modo usuário
a 30 segundos por padrão, taxa de CPU a 25% do sistema e até quatro processos,
incluindo launchers/descendentes. Políticas internas conservadoras, sem
benchmark documental. Ajustes explícitos aceitam CPU até 180 segundos/100%,
parede até 180 segundos; memória/processos não excedem esses tetos. O SO pode
arredondar memória para baixo por páginas. Não é limite de RSS nem proteção
contra swap/dumps.

O supervisor externo `windows_supervisor.py` é armado e confirma prontidão
antes de ResumeThread. Recebe cópias limitadas de quatro handles: Job apenas
para término, pai apenas para espera, evento de parada apenas para espera e
evento de prontidão apenas para sinalizar. Não recebe bytes, nomes de arquivo,
credenciais ou ambiente da API. Espera morte do pai, parada explícita ou prazo;
encerra o Job se o pai morrer ou o prazo vencer, mesmo com todas as threads
do host suspensas. Uma thread no host encerra a árvore se o supervisor morrer.

O supervisor também possui handle do Job: o fechamento isolado do handle do
host já não aciona sozinho KILL_ON_JOB_CLOSE. `close()` termina o Job
explicitamente antes de sinalizar/recolher o supervisor; morte dos dois fecha
o último handle no kernel. Erros de preparo não retomam o filho nem fazem
fallback. Suspensão simultânea do host/supervisor ou falha de kernel não estão
cobertas. No Windows moderno, a espera de prazo não inclui suspensão energética
do computador; não é promessa de prazo rígido durante sleep/hibernação.

Verificação anterior (11/11/2026): **26 testes aprovados em 50,48 s**, Windows 11 build 26200,
Python 3.13.14. Token sem capacidades/elevação, memória do pai e canário de
arquivo negados; variáveis-canário não herdadas. Serviços sintéticos locais
TCP/UDP IPv4/IPv6 são alcançáveis antes/depois fora do isolamento; dentro dele
não ocorre conexão TCP ou entrega de datagrama. O Windows também pode
descartar silenciosamente: timeout isolado não conta como prova; receptores
e controles positivos são conferidos. Não foram exercitados DNS, Internet,
LAN externa, proxy, IPC/COM/brokers ou ataques de kernel. Essas superfícies
continuam exigindo revisão antes da homologação.

Alocações até MemoryError exercitam quota reduzida; loop é encerrado pelo
orçamento de CPU antes do watchdog. Tentativas de exceder processos/escapar
do Job são recusadas. A prova de morte abrupta abre handles dos PIDs observados
da árvore estável antes de TerminateProcess no host e aguarda término de todos,
incluindo launchers. Falhas injetadas em atribuição/token comprovam que
ResumeThread não é chamado. Nenhum teste usa PDF, OCR ou credenciais reais.

`tests/run_windows_isolation.ps1` provisiona/remove perfil sintético por usuário
com `tests/windows_profile.ps1`, sem administrador, firewall ou ExecutionPolicy
novos. Prepara cópias locais do Python/bibliotecas já instalados, fora da
identidade MSIX; não baixa/instala dependências. Cópias ficam em
`.local-analysis/pytest/` (controlador em `isolation-controller/` e fixtures em
`isolation/`); somente bibliotecas/worker copiados recebem ACL RX do perfil.
Originais, ACLs do projeto/venv e credenciais não são alterados. Artefatos
sintéticos locais ficam ignorados, fora do envio. Perfil é removido em finally;
morte abrupta do runner inteiro pode deixar perfil/cópias sintéticos. Janitor
independente e limpeza documental continuam pendentes.

Primitivas documentadas pela Microsoft: [lista de handles](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[espera/prazo](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitformultipleobjects),
[AppContainer](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer),
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[limites de Job](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information)
e [taxa de CPU](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information).

## Integração sintética e IPC limitado

`Coordinator(..., windows_executor=WindowsExecutor(...))` usa o backend
AppContainer/Job sem fallback para spawn em caso de erro. SID, runtime e script
são provisionados pelo chamador interno confiável, nunca por payload HTTP.
Não há configuração pública nem processo de provisionamento documental.
`read_synthetic` continua aceitando somente `Sample`; todos os layouts reais
e o recebimento de bytes arbitrários permanecem bloqueados.

`document_ipc.py` transporta frames com comprimento uint32 em ordem de rede.
Entrada: cabeçalho JSON fechado de até 512 bytes e fixture de até 10.000.000
bytes. Saída: um único frame JSON, até 1.024 bytes para recibo ou 262.144 para
resultado normalizado; EOF obrigatório, sem bytes extras. Comprimentos inválidos
são recusados antes da alocação do payload. Pipes anônimos são os únicos canais;
stderr vai a NUL. Não há pickle, spool ou conteúdo em argv/env/banco/logs.

Threads de I/O permitem que o coordenador continue verificando prazo,
heartbeat, cancelamento e fencing enquanto o pipe bloqueia. Saída parcial
que não fecha continua sujeita a timeout; saída excedente/malformada encerra
o Job. No encerramento, a árvore termina antes de recolher threads, liberar
capacidade e limpar buffers. Schema, versão/hash/bytes/páginas, revisão,
titularidade e lease continuam revalidados antes da persistência atômica.
Resultados normalizados permanecem inventados e `needs_review`.

## Swap/dumps, scratch RAM e ingresso

`python -m ecowatt.document_environment` faz auditoria conservadora e somente
leitura de indicadores do Registro; não imprime caminhos/conteúdo e nunca
autoriza processamento. Consulta local de 12/11/2026: CrashDumpEnabled=3,
EncryptPagingFile desconhecido/ausente e chave LocalDumps presente. Presença
da chave pode incluir configuração por executável; não prova coleta efetiva
para o worker. Ausência/negação tampouco prova proteção. Permanecem bloqueios
para dumps de processo/sistema e swap protegido. Não houve mudança de Registro,
WER, pagefile, privilégios, EDR, firewall ou política organizacional.

`windows_memory.RamScratch` fornece buffers nativos sem arquivo, quota total
máxima de 4.000.000 bytes (cobrando páginas inteiras), acesso sob trava e limpeza
antes de liberar. Usa VirtualAlloc/VirtualLock; falha de lock é erro fechado,
sem fallback para disco ou memória paginável. A quota não garante que o SO
conseguirá travá-la. Não é diretório/filesystem RAM nem está integrado ao
parser/coordenador. A cópia retornada por `read`, buffers Python, IPC e futuras
bibliotecas não ficam protegidos por esse lock; dumps também não são excluídos.
Não mudar working set/privilégios para contornar falha. Bibliotecas que
exigirem nomes de arquivo continuam bloqueadas sem filesystem RAM homologado.

`memory_ingress.memory_body` é uma primitiva ASGI interna, sem rota, com teto
de corpo total (inclusive envelope futuro), verificação de Content-Length,
contagem de chunks, recusa de content-encoding e limpeza no sucesso, erro ou
cancelamento. Não chama Request.form/UploadFile/SpooledTemporaryFile. Testes
injetam mensagens ASGI inventadas e vedam temporários de arquivo. Isso prova
somente o coletor: falta parser multipart incremental limitado e integração
autenticada após reserva/capacidade, limites de duração/concorrência e auditoria
do servidor/proxy efetivamente usados. Um chunk já chega alocado pelo servidor;
o coletor não limita memória/retensão anterior do ASGI/proxy.

Fontes Microsoft: [VirtualLock e pagefile](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtuallock)
e [dumps locais WER](https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps).

Verificação de 12/11/2026: runner Win32 **42 aprovados em 233,88 s**
(15 testes de política e 27 probes nativos). Inclui árvore após morte e
suspensão completa do host, morte do supervisor, falha de preparo sem resume,
RAM/quota/lock recusado, recibo/publicação normalizada, cancelamento por
exclusão, timeout, falha sem fallback, frame excedente, bytes extras,
hash divergente e resposta truncada que trava. Suíte geral: **375 aprovados,
31 omitidos em 248,04 s** (27 probes explícitos e quatro omissões anteriores).
Regressão do coordenador depois da classificação de timeout: **32 aprovados
em 27,39 s**. Compilação src/tests aprovada. Estes resultados não medem
renderer/OCR, tráfego externo, COM/brokers, arquivos temporários de bibliotecas
ou persistência em proxy. Só fixtures e buffers inventados foram usados.
Runner realocado para `.local-analysis/pytest/isolation-controller/`, com cache
central habilitado, revalidado em quatro casos (host suspenso, scratch/lock
recusado e publicação normalizada): **quatro aprovados, 38 desmarcados em
24,48 s**. Ao final não restaram processos Python nem diretórios de perfis
EcoWatt.Synthetic em Packages. Cópias antigas do controlador foram preservadas.

## Contrato executável de pixels e buffers

`src/ecowatt/document_limits.py` não depende de ORM, HTTP, bibliotecas de PDF
ou OCR. O futuro adaptador deverá criar um `RasterBudget` por documento,
com a quantidade de páginas medida pelo parser dentro do isolamento. Aceita
somente 1–10 páginas conhecidas, como inteiro estrito.

Antes de **cada** alocação pelo renderer, chamar `reserve` com página
indexada a partir de 1, dimensões finais em pixels, canais e stride (bytes
por linha, incluindo padding). Dimensões precisam incluir escala, UserUnit,
rotação e recorte efetivos; não usar tamanho declarado pelo navegador nem
confundir pontos PDF com pixels. O adaptador futuro deverá calcular esses
valores de forma conservadora e verificar o mesmo tamanho na biblioteca.

`RasterPolicy` define tetos conservadores iniciais de preparação:

| Limite | Valor inclusivo |
| --- | --- |
| Lado da imagem | 10.000 pixels |
| Pixels acumulados por página | 20.000.000 |
| Pixels acumulados por documento | 60.000.000 |
| Bytes de raster acumulados por documento | 240.000.000 |
| Operações de rasterização por documento | 32 |

Os valores não vêm de benchmark ou homologação. Não ampliam os limites de
arquivos/bytes/páginas de [ADMISSION](ADMISSION.md). Alteração exige política
explícita e validação; não há configuração pública que os amplie.

São suportadas amostras de oito bits em gray, RGB ou RGBA. A quota de bytes
usa `stride × altura`, e não apenas pixels. Regiões, mudanças de DPI e
repetições consomem novamente os orçamentos da página e do documento; falha
do renderer ou do OCR não restitui a reserva. Não recriar o orçamento entre
essas tentativas. Uma reserva recusada não altera os contadores. O objeto é
interno, de uso sequencial; não aceitar orçamento/alocação do cliente ou de
IPC como autorização.

Depois da renderização e antes do OCR, usar `RasterAllocation.verify` para
confrontar geometria, canais, stride, contiguidade e quantidade real de bytes.
`memoryview.nbytes` evita confundir número de elementos com bytes, sem criar
cópia do buffer. Divergência é erro técnico fechado; não reduzir DPI, truncar
ou aceitar silenciosamente. O chamador deverá descartar o buffer e encerrar
o trabalho diante de qualquer erro. Os testes usam somente números e buffers
inventados, sem alocar imagens nos limites grandes.

O contrato **ainda não é consumido por um adaptador**, porque não existe um
renderer autorizado. Verificação posterior não impede uma biblioteca de
alocar demais antes de retornar. Os contadores medem trabalho reservado,
não RAM residente, cópias, imagens embutidas descomprimidas, memória do OCR
ou recursos de parser textual. Limites físicos de SO continuam obrigatórios.

## Barreiras restantes

O backend nativo tem provas sintéticas de SO, mas não há homologação de
processamento documental, produção ou desempenho. Bibliotecas PDF/OCR não
foram instaladas. Falta de administrador não foi tratada como impossibilidade.

| Garantia de §5/§12 | Evidência atual e condição antes de documentos |
| --- | --- |
| Pixels/bytes de raster | Planejamento e confronto sintéticos testados; falta integração com renderer e teste de expansão real sintética. |
| Rede e privilégios | Backend selecionável no coordenador sintético, token conferido antes de executar e probes locais/canário. Falta revisão ampliada de superfícies/ambiente. |
| CPU/RAM | Job impõe CPU/memória comprometida agregadas; exaustão sintética testada. Falta benchmark e integração ao parser/OCR. |
| Descendentes e morte do pai | Backend opcional integrado; supervisor externo e fechamento explícito do Job. Modo spawn padrão permanece somente sintético. |
| Tempo/watchdog | Supervisor armado antes de resume; probes de morte/suspensão completa do host. Falta integração/benchmark do parser/OCR; sem garantia de falha global do SO. |
| Swap/dumps | Auditoria somente leitura aponta bloqueios; falta política efetiva verificada para todos os processos/cópias. |
| Temporários | Scratch nativo com quota/lock, sem arquivos; não é filesystem RAM nem protege bibliotecas futuras. Integração e limpeza documental/janitor pendentes. |
| Framework/proxy | Coletor ASGI em memória testado isoladamente; falta multipart, integração autenticada com capacidade e auditoria do servidor/proxy. Nenhum upload habilitado. |
| Parser/proveniência | Não instalados nem implementados; faltam contrato documental versionado, páginas/regiões, confronto texto/OCR e homologação do layout específico. |

A solução local segue Windows nativo, sem WSL/containers. Lease/fencing
protegem persistência e não substituem garantias de SO. Nenhuma configuração
do backend libera documentos no coordenador existente.

## Próximo passo verificável

Resolver política de swap/dumps e RAM para bibliotecas/cópias e ampliar revisão
de superfícies (IPC/COM/brokers, perfis graváveis e ambiente). Completar multipart
sem spool com capacidade/reserva e verificar servidor/proxy, mantendo bloqueio
de documentos. O executor Windows já é selecionável no coordenador sintético.
Depois das garantias integrais de §5/§12, integrar renderer ao
orçamento/proveniência documental versionada. Ingresso sem spool e homologação
de layout seguem cumulativos. Seleção local não envia; leitura futura exige
“Ler fatura”. Fase 2 permanece aberta.

Probes Windows autorizados, a partir da raiz, sem instalação:

```powershell
.\tests\run_windows_isolation.ps1
```

Runner habilita explicitamente os probes; suíte comum os omite. Quando
habilitados, indisponibilidade/falha de SO é erro, nunca skip. A CI executa
o runner como etapa própria.

Verificação focal, sem instalação ou inicialização da aplicação:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_document_limits.py -q -p no:cacheprovider
```
