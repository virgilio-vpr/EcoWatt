# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.6.

## Entrega atual

Fase 0 em andamento: contratos v0.1, 25 casos sintéticos, conferência das duas planilhas e gabarito textual local de dezembro/2025 preparado para revisão e reconciliação monetária preliminar dos 12 PDFs. **Aceite pendente**: candidato real ainda não revisado/aprovado, diferenças de reconciliação, bases tributárias e vigências por confirmar. Nenhuma aplicação, ambiente da aplicação, banco ou container iniciado.

## Evidências principais

- `docs/corpus/workbook-review.md`: fórmulas/caches das oito abas, 1.201 células de fórmula com cache, aritmética recalculada em Decimal e divergências P01–P08. Sem edição dos originais.
- `docs/corpus/invoice-review.md`: 12 PDFs textuais, 24 páginas, 8.390.489 bytes; mesma unidade e classificação A4 Azul; nome ENEL Distribuição São Paulo identificado, CNPJ/mercado ainda não confirmados. Candidato local com 109 linhas selecionadas; 105 quantificadas e 4 parcelas ociosas apenas monetárias. O recorte inicial não conciliava os totais. A continuação reconheceu 135 linhas financeiras e residual zero nos 12 totais, sem confirmar cobertura visual ou tributos.
- Nos dez meses sobrepostos, quantidades e preços de demanda dos dois postos coincidem com a planilha Azul. Períodos completos dos arquivos e planilhas divergem; a planilha Verde repete entradas da ponta da Azul. Usuário confirmou Verde como simulação real e PDFs agosto/2025–julho/2026 como referência principal. Segundo o usuário, a migração ao mercado livre ocorreu em agosto/2026; essa é a razão da exclusão dos dois últimos meses das planilhas. Comparar apenas os dez meses comuns; não misturar meses pós-migração no gabarito cativo. Data/condições da migração ainda não conferidas documentalmente.
- A simulação de ponta da Azul usa fator 3 de ultrapassagem, diferente da tabela atual e da SPEC; erro inativo nas entradas existentes. Redução fixa de 18% não reproduz os preços das vinte parcelas ociosas comparáveis. Não transportar essas hipóteses para o motor.
- 38 linhas ultrapassam a tolerância inicial de BRL 0.02; 35 são compatíveis com hipótese explícita de arredondamento do preço impresso, três exigem revisão específica. Não foram aprovadas por tolerância ampliada.
- `docs/corpus/regulatory-review.md`: PDF local da REN tem 183 páginas e metadados de reprodução Leis.org; leitura dirigida dos arts. 301–304, sem fixar redação consolidada/vigências. Catálogo oficial acessível e referências oficiais indexadas consultadas; HTML compilado retornou 403. Nenhuma tarifa CSV importada/aprovada.
- SPEC §8.4 esclarecida conforme o usuário: ausência confirmada de cobrança reativa não cria cenário independente de aparecimento; leitura incompleta é desconhecida; efeitos futuros não calculáveis de alterações contratuais continuam limitados.

- `docs/corpus/representative-review.md`: dezembro/2025 conferido textualmente nos treze itens, com transcrição separada dos valores e aritmética em Decimal. Competência explícita identificada; datas do ciclo ainda candidatas por rótulos não confirmados visualmente. CNPJ derivável da chave NF3e é candidato; mercado permanece documentalmente desconhecido.
- Novo rascunho local inclui bandeiras, COSIP, colunas tributárias e residuais. Setembro/2025 tem divergências relevantes entre quadro tributário e itens. PIS/COFINS difere entre quadro, soma dos itens e coluna TOTAL. Nenhuma tolerância ampliada ou ausência promovida a zero confirmado.

## Ferramentas e verificações

- Python 3.13.14 e `openpyxl` já disponíveis. Bibliotecas PDF verificadas inicialmente indisponíveis. Em 06/11/2026 o usuário autorizou **somente pypdf para análise**; instalada versão 7.0.0 em `.local-tools/pypdf/`, sem dependências adicionais nem ambiente da aplicação. Instalação/leitura exigiram execução aprovada fora da sandbox por falha de acesso na tentativa restrita. Isso não autoriza instalar a stack do produto.
- Inspeção em memória; nenhum PDF, imagem ou texto bruto extraído foi gravado. Candidato estruturado e script pontual em `.local-analysis/` são locais, sem aprovação e excluídos do versionamento.
- Aritmética das planilhas, caches, comparação com campos extraídos e novos casos sintéticos conferidos. Links Markdown locais e alterações textuais revisados antes do commit. Não houve teste de aplicação, OCR, concorrência ou migração.
- `.gitignore` protege documentos reais, ferramentas de análise, candidato local, logs, bancos, caches e ambiente virtual. Exclusão do envio remoto também é feita por lista explícita de arquivos, sem depender apenas do ignore.

- Continuação: leitura do pypdf existente por execução aprovada fora da sandbox após ImportError restrito; nenhuma instalação. Duas páginas da representativa inspecionadas textualmente, sem renderização. Treze valores confrontados com transcrição separada, somas, subtotais, diferenças de demanda e composição da energia em Decimal; 135 itens e 12 resíduos zero na ampliação. Rascunhos locais `representative-review.md` e `full-invoice-review.json`, script `reconcile_full.py`, todos ignorados e não aprovados.

## Pendências e próximo passo

Revisar visualmente as duas páginas de dezembro/2025 com o gabarito local, confirmar identidade/mercado e rótulos de ciclo, resolver três produtos e divergências tributárias. Em seguida conferir setembro/2025, com ociosidade somente monetária e diferenças relevantes no quadro tributário; revisar as exceções especiais de novembro/2025, março/2026 e abril/2026 e completar cada gabarito. A reconciliação monetária preliminar não homologa os demais campos. Conferir Verde apenas nos dez meses comuns, com fontes corretas e separação pós-migração. Obter tarifas oficiais por vigência, fechar regras aplicáveis e aprovação com responsável identificado. Nenhum checkbox da SPEC foi marcado.

O desenvolvimento independente da Fase 1 continua possível com fixtures sintéticas, quando solicitado, sem depender da homologação comercial. Usuário sem administrador; respeitar políticas da máquina. Commits diretos em `virgilio-vpr/EcoWatt` autorizados, preservando alterações remotas; não enviar materiais reais ou ferramentas locais.

## Arquivos desta entrega

Novo: `docs/corpus/representative-review.md`. Alterados: `docs/STATUS.md`, `docs/corpus/README.md`, `docs/corpus/invoice-review.md`. Removidos: nenhum. Artefatos reais e ferramentas locais excluídos do envio.

Verificações: transcrição e aritmética da representativa, contagem/reconciliação da série, pendências tributárias explícitas, links e varredura dos quatro documentos públicos antes do commit. Nenhum teste da aplicação executado; nenhuma dependência instalada ou aplicação implementada. SPEC e aceite permanecem inalterados.

Commit desta entrega: `docs: prepara revisao da fatura representativa e reconciliacao da serie`. Consultar histórico remoto para o SHA; este status integra o próprio commit.
