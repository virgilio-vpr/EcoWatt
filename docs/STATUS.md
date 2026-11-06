# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.7.

## Entrega atual

Fase 0 em andamento: contratos v0.1, 25 casos sintéticos, conferência das duas planilhas e gabarito textual local de dezembro/2025 preparado para revisão e reconciliação monetária preliminar dos 12 PDFs. **Aceite pendente**: candidato real ainda não revisado/aprovado, campos ausentes, cobertura visual e fontes/vigências por confirmar. Nenhuma aplicação, ambiente da aplicação, banco ou container iniciado.

## Evidências principais

- `docs/corpus/workbook-review.md`: fórmulas/caches das oito abas, 1.201 células de fórmula com cache, aritmética recalculada em Decimal e divergências P01–P08. Sem edição dos originais.
- `docs/corpus/invoice-review.md`: 12 PDFs textuais, 24 páginas, 8.390.489 bytes; mesma unidade e classificação A4 Azul; nome ENEL Distribuição São Paulo identificado, CNPJ/mercado ainda não confirmados. Candidato local com 109 linhas selecionadas; 105 quantificadas e 4 parcelas ociosas apenas monetárias. O recorte inicial não conciliava os totais. A continuação reconheceu 135 linhas financeiras e residual zero nos 12 totais, sem confirmar cobertura visual ou tributos.
- Nos dez meses sobrepostos, quantidades e preços de demanda dos dois postos coincidem com a planilha Azul. Períodos completos dos arquivos e planilhas divergem; a planilha Verde repete entradas da ponta da Azul. Usuário confirmou Verde como simulação real e PDFs agosto/2025–julho/2026 como referência principal. Segundo o usuário, a migração ao mercado livre ocorreu em agosto/2026; essa é a razão da exclusão dos dois últimos meses das planilhas. Comparar apenas os dez meses comuns; não misturar meses pós-migração no gabarito cativo. Data/condições da migração ainda não conferidas documentalmente.
- A simulação de ponta da Azul usa fator 3 de ultrapassagem, diferente da tabela atual e da SPEC; erro inativo nas entradas existentes. Usuário esclareceu a regra desejada: preço ocioso LEI ESTADUAL = preço da demanda contratada × 0,82, na ponta, fora de ponta e demanda única. O candidato dos PDFs ainda diverge dessa relação; conferir preço-base/precisão sem substituir o observado. O fator 3 de ultrapassagem continua sem validação.
- Histórico: 38 produtos superavam BRL 0.02. Usuário autorizou tolerância monetária por item de até BRL 0.99 inclusive; os 105 produtos quantificados passam nessa política, com diferenças preservadas.
- `docs/corpus/regulatory-review.md`: PDF local da REN tem 183 páginas e metadados de reprodução Leis.org; leitura dirigida dos arts. 301–304, sem fixar redação consolidada/vigências. Catálogo oficial acessível e referências oficiais indexadas consultadas; HTML compilado retornou 403. Nenhuma tarifa CSV importada/aprovada.
- SPEC §8.4 esclarecida conforme o usuário: ausência confirmada de cobrança reativa não cria cenário independente de aparecimento; leitura incompleta é desconhecida; efeitos futuros não calculáveis de alterações contratuais continuam limitados.

- `docs/corpus/representative-review.md`: dezembro/2025 conferido textualmente nos treze itens, com transcrição separada dos valores e aritmética em Decimal. Competência explícita identificada; datas do ciclo ainda candidatas por rótulos não confirmados visualmente. CNPJ derivável da chave NF3e é candidato; mercado permanece documentalmente desconhecido.
- Novo rascunho local inclui bandeiras, COSIP, colunas tributárias e residuais. Setembro/2025 tem divergências relevantes entre quadro tributário e itens. PIS/COFINS difere entre quadro, soma dos itens e coluna TOTAL. A tolerância monetária foi ampliada explicitamente pelo usuário para BRL 0.99; ausência não foi promovida a zero confirmado.

## Ferramentas e verificações

- Python 3.13.14 e `openpyxl` já disponíveis. Bibliotecas PDF verificadas inicialmente indisponíveis. Em 06/11/2026 o usuário autorizou **somente pypdf para análise**; instalada versão 7.0.0 em `.local-tools/pypdf/`, sem dependências adicionais nem ambiente da aplicação. Instalação/leitura exigiram execução aprovada fora da sandbox por falha de acesso na tentativa restrita. Isso não autoriza instalar a stack do produto.
- Inspeção em memória; nenhum PDF, imagem ou texto bruto extraído foi gravado. Candidato estruturado e script pontual em `.local-analysis/` são locais, sem aprovação e excluídos do versionamento.
- Aritmética das planilhas, caches, comparação com campos extraídos e novos casos sintéticos conferidos. Links Markdown locais e alterações textuais revisados antes do commit. Não houve teste de aplicação, OCR, concorrência ou migração.
- `.gitignore` protege documentos reais, ferramentas de análise, candidato local, logs, bancos, caches e ambiente virtual. Exclusão do envio remoto também é feita por lista explícita de arquivos, sem depender apenas do ignore.

- Continuação: leitura do pypdf existente por execução aprovada fora da sandbox após ImportError restrito; nenhuma instalação. Duas páginas da representativa inspecionadas textualmente, sem renderização. Treze valores confrontados com transcrição separada, somas, subtotais, diferenças de demanda e composição da energia em Decimal; 135 itens e 12 resíduos zero na ampliação. Rascunhos locais `representative-review.md` e `full-invoice-review.json`, script `reconcile_full.py`, todos ignorados e não aprovados.

## Decisão atual de preço e escopo

Conferência adicional em Decimal: relação de 82% compatível com a tolerância inicial de BRL 0.02 nas duas parcelas ociosas da representativa e em 17 das 20 parcelas comparáveis. Exceções remanescentes: REAL-LOCAL-03, REAL-LOCAL-06 e REAL-LOCAL-12, fora de ponta. As quatro parcelas sem quantidade/preço não foram inventadas. Diferença nas últimas casas do preço não implica por si só falha monetária. Gabarito local v0.2 teve a codificação corrigida e o roteiro tributário retirado das pendências.

SPEC 3.7: impostos separados estão fora da análise da simulação; usar preços cheios com impostos incorporados, sem novo acréscimo ou dedução. Exceção explícita para formação do preço ocioso LEI ESTADUAL: preço da demanda contratada × 0,82, na ponta, fora de ponta e demanda única. Divergências tributárias registradas acima são documentais e deixam de ser bloqueios por si só. Gabarito local mantém o observado e a divergência para a regra informada; nenhum candidato foi aprovado.

## Pendências e próximo passo

Revisar visualmente as duas páginas de dezembro/2025 com o gabarito local, confirmar identidade/mercado e rótulos de ciclo, conferir a cobertura dos itens e os campos ausentes. Em seguida conferir setembro/2025, com ociosidade somente monetária; completar cada gabarito; diferenças monetárias antes especiais agora passam no limite autorizado. A reconciliação monetária preliminar não homologa os demais campos. Conferir Verde apenas nos dez meses comuns, com fontes corretas e separação pós-migração. Obter tarifas oficiais por vigência, fechar regras aplicáveis e aprovação com responsável identificado. Nenhum checkbox da SPEC foi marcado.

O desenvolvimento independente da Fase 1 continua possível com fixtures sintéticas, quando solicitado, sem depender da homologação comercial. Usuário sem administrador; respeitar políticas da máquina. Commits diretos em `virgilio-vpr/EcoWatt` autorizados, preservando alterações remotas; não enviar materiais reais ou ferramentas locais.

## Arquivos desta entrega

Novos/removidos: nenhum documento público. Alterados: `EcoWatt_PROJECT_SPEC.md`, `docs/contracts/invoice-data.md`, `docs/contracts/pipeline.md`, `docs/corpus/README.md`, `docs/corpus/workbook-review.md`, `docs/corpus/invoice-review.md`, `docs/corpus/representative-review.md`, `docs/corpus/synthetic-cases.md`, `docs/STATUS.md`. Gabarito local ajustado sem envio. Artefatos reais e ferramentas locais excluídos do envio.

Verificações desta alteração: coerência da relação de 82% por posto/demanda única, ausência de nova tributação sobre preço cheio, links e lista explícita dos nove documentos públicos e fronteiras ±BRL 0.99/±BRL 1.00 em Decimal. Conferências financeiras anteriores preservadas; nenhum novo teste da aplicação, leitura de PDF ou homologação. Nenhuma dependência instalada ou aplicação implementada. Aceite permanece pendente.

Commit desta entrega: `docs: ajusta precos de ociosidade e tolerancia monetaria`. Consultar histórico remoto para o SHA; este status integra o próprio commit.


## Tolerância monetária atual — decisão do usuário em 06/11/2026

Diferença absoluta de até BRL 0.99 por item, inclusive, aceita na reconciliação entre cálculo e valor faturado. Reavaliação em Decimal: 105 de 105 produtos quantificados e 20 de 20 parcelas ociosas pela relação de 82% passam. As quatro parcelas ociosas somente monetárias não tiveram quantidade/preço inventados. Resultados e pendências acima relativos a BRL 0.02 são históricos e ficam superados quanto ao aceite monetário. Não há pendência de impostos separados na simulação com preços cheios. Permanecem cobertura visual, identidade/mercado, campos necessários ausentes, fontes dos cenários alternativos e aprovação do gabarito. Diferenças e valores observados são preservados; os 12 residuais do total continuam zero, sem ajuste. A tolerância não altera kW, gatilho de ultrapassagem ou validação dos campos. Fronteiras ±0.99 aceitas e ±1.00 recusadas verificadas em Decimal.
