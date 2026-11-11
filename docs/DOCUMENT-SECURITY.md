# Segurança documental — preparação do adaptador

Esta entrega da Fase 2 implementa somente o orçamento de rasterização de
§5.1, com testes sintéticos. Não implementa um sandbox, renderer, parser ou
OCR; nenhuma rota recebe documentos. A admissão e `normalized-invoice-v1`
continuam exclusivamente sintéticos, inclusive para ENEL. Catálogo tarifário
não habilita adaptador. Nenhum critério integral de §15 é concluído aqui.

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

## Ambiente conferido e limites da evidência

Em 11/11/2026 foram executadas verificações de leitura no Windows 11,
Python 3.13.14 e ambiente virtual existente. `pdfplumber`, `pypdfium2`,
Pillow e `win32job` não estão instalados nesse ambiente; Docker não foi
encontrado no PATH. Nenhuma dependência foi instalada. A inspeção inicial
mostrou WSL não instalado; por decisão explícita do usuário, **WSL está fora
da solução** e não deve ser instalado ou usado. Não foram iniciados containers.

Ausência de administrador não demonstra que todas as primitivas de
isolamento Windows sejam impossíveis. O bloqueio concreto atual é a
ausência de uma implementação de confinamento integrada e de evidências
de suas garantias. Não alterar políticas organizacionais nem instalar
componentes para tentar suprir esse bloqueio sem autorização específica.

| Garantia de §5/§12 | Evidência atual e condição antes de documentos |
| --- | --- |
| Pixels/bytes de raster | Planejamento e confronto sintéticos testados; falta integração com renderer e teste de expansão real sintética. |
| Rede e privilégios | Spawn herda ambiente; falta confinamento verificado, inclusive tentativas de rede e acesso indevido a arquivos/credenciais. |
| CPU/RAM | Contadores da aplicação não impõem limites físicos; falta backend de SO e testes de exaustão. |
| Descendentes e morte do pai | Encerramento controlado existe; falta prova de encerramento de toda a árvore após falha abrupta. |
| Tempo/watchdog | Polling do coordenador existe; falta watchdog independente que interrompa também parser/OCR travado. |
| Swap/dumps | Não auditados; falta política efetiva verificada no ambiente de processamento. |
| Temporários | Esta entrega não cria temporários documentais; bibliotecas futuras devem funcionar em memória ou em RAM com quota/permissões e limpeza verificadas. |
| Framework/proxy | Não há upload; falta implementar ingresso sem spool e verificar framework e proxy efetivamente usados. Ausência de endpoint não homologa o futuro ingresso. |
| Parser/proveniência | Não instalados nem implementados; faltam contrato documental versionado, páginas/regiões, confronto texto/OCR e homologação do layout específico. |

O ambiente adequado pode ser Windows com confinamento comprovado ou outro
ambiente expressamente autorizado. Esta entrega não escolhe infraestrutura,
não solicita instalação e não certifica produção. Lease/fencing protegem a
persistência; não substituem contenção de processos ou de memória.

## Próximo passo verificável

Implementar e testar um backend de isolamento no ambiente autorizado, ainda
com programas/documentos exclusivamente sintéticos. Demonstrar rede negada,
privilégio mínimo, CPU/RAM/tempo e término da árvore sob morte abrupta do pai;
verificar swap/dumps e temporários. Só então integrar um renderer específico
ao orçamento, testar geometria/expansão e definir a versão documental da
proveniência sem alterar retroativamente o contrato sintético. Ingresso sem
spool e homologação de layout continuam condições cumulativas antes de
qualquer upload/leitura real. A seleção local continua sem envio; a ação
futura deverá exigir “Ler fatura”.

Verificação focal, sem instalação ou inicialização da aplicação:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_document_limits.py -q -p no:cacheprovider
```
