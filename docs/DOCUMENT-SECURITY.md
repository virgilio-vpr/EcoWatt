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
ORM ou HTTP. Não é usado pelo coordenador. Recebe executável interno e SID
de perfil previamente provisionado; não tem endpoint ou ingresso de documentos.

Cada processo nasce suspenso em AppContainer, sem capacidades solicitadas,
sem herança de handles, com ambiente limitado a SystemRoot/WINDIR/LOCALAPPDATA
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

KILL_ON_JOB_CLOSE encerra a árvore quando o kernel fecha o último handle,
inclusive por morte abrupta do pai. wait/close encerram descendentes restantes.
Watchdog de thread encerra o Job ao prazo sem polling do coordenador; não é
supervisor externo. Suspensão completa do pai, GIL travado ou falha de SO ainda
exigem outra barreira. Não há garantia de prazo rígido nesses casos.

Verificação local final: **26 testes aprovados em 50,48 s**, Windows 11 build 26200,
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
`.local-analysis/`; somente bibliotecas/worker copiados recebem ACL RX do perfil.
Originais, ACLs do projeto/venv e credenciais não são alterados. Artefatos
sintéticos locais ficam ignorados, fora do envio. Perfil é removido em finally;
morte abrupta do runner inteiro pode deixar perfil/cópias sintéticos. Janitor
independente e limpeza documental continuam pendentes.

Primitivas documentadas pela Microsoft: [AppContainer](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer),
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[limites de Job](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information)
e [taxa de CPU](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information).

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
| Rede e privilégios | Backend confere token antes de executar; probes locais/canário. Falta integração ao coordenador e revisão ampliada de superfícies/ambiente. |
| CPU/RAM | Job impõe CPU/memória comprometida agregadas; exaustão sintética testada. Falta benchmark e integração ao parser/OCR. |
| Descendentes e morte do pai | Backend testado com morte abrupta/handles de descendentes; coordenador ainda usa spawn anterior. |
| Tempo/watchdog | Thread independente do polling testada; falta supervisor externo para host suspenso/GIL travado. |
| Swap/dumps | Não auditados; falta política efetiva verificada no ambiente de processamento. |
| Temporários | Esta entrega não cria temporários documentais; bibliotecas futuras devem funcionar em memória ou em RAM com quota/permissões e limpeza verificadas. |
| Framework/proxy | Não há upload; falta implementar ingresso sem spool e verificar framework e proxy efetivamente usados. Ausência de endpoint não homologa o futuro ingresso. |
| Parser/proveniência | Não instalados nem implementados; faltam contrato documental versionado, páginas/regiões, confronto texto/OCR e homologação do layout específico. |

A solução local segue Windows nativo, sem WSL/containers. Lease/fencing
protegem persistência e não substituem garantias de SO. Nenhuma configuração
do backend libera documentos no coordenador existente.

## Próximo passo verificável

Completar supervisor externo, swap/dumps, temporários RAM e revisão ampliada
de superfícies; integrar backend/IPC limitado ao coordenador antes do adaptador
documental. Depois das garantias integrais de §5/§12, integrar renderer ao
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
