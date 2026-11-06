# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.6.

## Entrega atual

Fase 0 em andamento: contratos v0.1, 25 casos sintéticos, conferência das duas planilhas e extração textual inicial dos 12 PDFs. **Aceite pendente**: candidato real ainda não revisado/aprovado, diferenças de reconciliação, bases tributárias e vigências por confirmar. Nenhuma aplicação, ambiente da aplicação, banco ou container iniciado.

## Evidências principais

- `docs/corpus/workbook-review.md`: fórmulas/caches das oito abas, 1.201 células de fórmula com cache, aritmética recalculada em Decimal e divergências P01–P08. Sem edição dos originais.
- `docs/corpus/invoice-review.md`: 12 PDFs textuais, 24 páginas, 8.390.489 bytes; mesma unidade e classificação A4 Azul; nome ENEL Distribuição São Paulo identificado, CNPJ/mercado ainda não confirmados. Candidato local com 109 linhas selecionadas; 105 quantificadas e 4 parcelas ociosas apenas monetárias. Não houve conciliação integral de cada fatura.
- Nos dez meses sobrepostos, quantidades e preços de demanda dos dois postos coincidem com a planilha Azul. Períodos completos dos arquivos e planilhas divergem; a planilha Verde repete entradas da ponta da Azul. Usuário confirmou Verde como simulação real e PDFs agosto/2025–julho/2026 como referência principal. Segundo o usuário, a migração ao mercado livre ocorreu em agosto/2026; essa é a razão da exclusão dos dois últimos meses das planilhas. Comparar apenas os dez meses comuns; não misturar meses pós-migração no gabarito cativo. Data/condições da migração ainda não conferidas documentalmente.
- A simulação de ponta da Azul usa fator 3 de ultrapassagem, diferente da tabela atual e da SPEC; erro inativo nas entradas existentes. Redução fixa de 18% não reproduz os preços das vinte parcelas ociosas comparáveis. Não transportar essas hipóteses para o motor.
- 38 linhas ultrapassam a tolerância inicial de BRL 0.02; 35 são compatíveis com hipótese explícita de arredondamento do preço impresso, três exigem revisão específica. Não foram aprovadas por tolerância ampliada.
- `docs/corpus/regulatory-review.md`: PDF local da REN tem 183 páginas e metadados de reprodução Leis.org; leitura dirigida dos arts. 301–304, sem fixar redação consolidada/vigências. Catálogo oficial acessível e referências oficiais indexadas consultadas; HTML compilado retornou 403. Nenhuma tarifa CSV importada/aprovada.
- SPEC §8.4 esclarecida conforme o usuário: ausência confirmada de cobrança reativa não cria cenário independente de aparecimento; leitura incompleta é desconhecida; efeitos futuros não calculáveis de alterações contratuais continuam limitados.

## Ferramentas e verificações

- Python 3.13.14 e `openpyxl` já disponíveis. Bibliotecas PDF verificadas inicialmente indisponíveis. Em 06/11/2026 o usuário autorizou **somente pypdf para análise**; instalada versão 7.0.0 em `.local-tools/pypdf/`, sem dependências adicionais nem ambiente da aplicação. Instalação/leitura exigiram execução aprovada fora da sandbox por falha de acesso na tentativa restrita. Isso não autoriza instalar a stack do produto.
- Inspeção em memória; nenhum PDF, imagem ou texto bruto extraído foi gravado. Candidato estruturado e script pontual em `.local-analysis/` são locais, sem aprovação e excluídos do versionamento.
- Aritmética das planilhas, caches, comparação com campos extraídos e novos casos sintéticos conferidos. Links Markdown locais e alterações textuais revisados antes do commit. Não houve teste de aplicação, OCR, concorrência ou migração.
- `.gitignore` protege documentos reais, ferramentas de análise, candidato local, logs, bancos, caches e ambiente virtual. Exclusão do envio remoto também é feita por lista explícita de arquivos, sem depender apenas do ignore.

## Pendências e próximo passo

Revisar visualmente/manual os cabeçalhos e itens, confirmar CNPJ/mercado e competência/ciclo/dias, resolver as três exceções de precisão e conferir tributos/parcelas ociosas. Rever a simulação real da Verde com o período principal já definido e fontes tarifárias corretas, separando as linhas posteriores à migração informada pelo usuário. Completar o gabarito independente por fatura com todos os componentes e residual; aprovar com responsável identificado. Obter tarifas oficiais por distribuidora e vigência e documentar alterações aplicáveis da norma. Nenhum checkbox composto da Fase 0 foi marcado por mera disponibilidade dos materiais.

O desenvolvimento independente da Fase 1 continua possível com fixtures sintéticas, quando solicitado, sem depender da homologação comercial. Usuário sem administrador; respeitar políticas da máquina. Commits diretos em `virgilio-vpr/EcoWatt` autorizados, preservando alterações remotas; não enviar materiais reais ou ferramentas locais.

## Arquivos desta entrega

Alterados: `docs/STATUS.md`, `docs/corpus/README.md`, `docs/corpus/workbook-review.md`, `docs/corpus/invoice-review.md`. Novos/removidos: nenhum.

Registradas as respostas do usuário sobre finalidade da planilha Verde, período principal e exclusão intencional dos meses posteriores à migração informada ao mercado livre. Originais e candidato local preservados; nenhum novo teste financeiro ou aceite presumido. Conferidos consistência das decisões, links locais e lista explícita de quatro documentos para envio.

Commit: `docs: esclarece periodo do corpus e migracao ao mercado livre`. Consultar o histórico remoto para o SHA; este status integra o próprio commit.