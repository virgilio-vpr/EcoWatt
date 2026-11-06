# Estado do EcoWatt

Atualizado em 06/11/2026. Referência: SPEC versão 3.8.

## Entrega atual

Fase 0 em andamento; contratos documentais v0.1 e 25 casos sintéticos, sem aplicação implementada. Gabarito textual local de dezembro/2025 preparado para revisão; reconciliação preliminar dos 12 PDFs com 135 itens financeiros e residual zero nos 12 totais. Aceite e gabarito real continuam pendentes, sem aprovação presumida.

## Decisões preservadas

- Referência principal: PDFs agosto/2025–julho/2026. Planilhas comparadas somente nos dez meses comuns, outubro/2025–julho/2026. Verde é simulação real a conferir. Migração ao mercado livre em agosto/2026 informada pelo usuário, ainda sem conferência documental de data/condições.
- Preço cheio com impostos incorporados; impostos separados fora da análise. Demanda ociosa LEI ESTADUAL: preço da demanda contratada × 0,82, na ponta, fora de ponta e demanda única.
- Tolerância monetária por item até BRL 0.99 inclusive, autorizada pelo usuário. Em Decimal, 105/105 produtos quantificados e 20/20 parcelas ociosas comparáveis passam; quatro parcelas somente monetárias não tiveram quantidade/preço inventados. Diferenças e residuais preservados. Fronteiras ±0.99/±1.00 verificadas anteriormente.
- Fator 3 de ultrapassagem na simulação de ponta da planilha continua divergente da regra proposta; não acionado nas entradas existentes. Não transportar esse fator para o motor.
- Ausência confirmada de cobrança reativa não cria cenário independente de surgimento; medição não equivale a cobrança. Efeitos futuros sem dados permanecem condicionados.

## Dados da empresa, conexão e mercado

Cadastro da empresa antes da simulação; unidade salva antes do upload, como já previsto. Nome/titular e endereço podem ser extraídos e apresentados para conferência: manter os coincidentes, confirmar/corrigir divergentes. Endereço da empresa, endereço impresso na fatura e endereço confirmado da cabine/subestação no ponto de conexão são distintos. Rua adjacente pode explicar diferença para a mesma UC/distribuidora, com confirmação registrada. Não sobrescrever cadastro, valor extraído ou snapshot automaticamente.

Mercado sugerido por identificação explícita ou indícios TE/TUSD por ciclo. Ausência de cobrança corrente de energia ativa TE com leitura completa e rede/TUSD identificada sugere livre; presença sugere cativo. Inferência documentada com fontes Enel/CPFL em `docs/corpus/regulatory-review.md`. Leitura parcial, agrupamento ambíguo ou conflito mantém desconhecido. Confirmação tem origem/ator/data; UFER TE e histórico não classificam o fornecimento. Corpus local não reclassificado automaticamente; mercado livre continua fora do cálculo cativo completo.

## Evidências e ferramentas

- `docs/corpus/workbook-review.md`: oito abas, 1.201 fórmulas com cache e divergências P01–P08. Caches e reprodução aritmética não homologam hipóteses.
- `docs/corpus/invoice-review.md` e `representative-review.md`: 12 PDFs textuais, 24 páginas; representativa com 13 itens, transcrição separada e conferência Decimal. Nome ENEL SP identificado, CNPJ derivado da chave NF3e ainda candidato. Cobertura visual, rótulos do ciclo e mercado documental por conferir.
- `docs/corpus/regulatory-review.md`: REN local de 183 páginas, reprodução Leis.org; arts. 301–304 consultados, sem consolidação/vigências homologadas. Nenhum CSV tarifário importado/aprovado.
- Python e openpyxl existentes; pypdf 7.0.0 instalado anteriormente exclusivamente para análise em `.local-tools/pypdf/`, com autorização do usuário. Leitura exigiu execução aprovada fora da sandbox. Nada instalado nesta entrega.
- Originais preservados. Sem PDF, imagem ou texto bruto gravado pela análise; rascunhos estruturados e scripts locais em `.local-analysis/`, ignorados e fora do envio. Gabarito local v0.2 com preços/tolerância atualizados, sem revisor aprovado.

## Verificações desta entrega

Revisão documental de fluxo, campos, proveniência e indícios de mercado; fontes primárias Enel/CPFL consultadas. Links locais, codificação, consistência das regras e lista explícita de seis arquivos públicos conferidos. Nenhum novo teste financeiro, leitura de PDF, teste da aplicação, instalação ou container. Nenhum checkbox da SPEC marcado.

## Pendências e próximo passo

Conferir visualmente as duas páginas da representativa e seus cabeçalhos; confirmar identidade, mercado por ciclo e endereço do ponto de conexão com o responsável. Completar gabaritos, inclusive agosto/setembro com parcelas somente monetárias; obter preços/fontes para conferir a Verde nos dez meses comuns e vigências aplicáveis. Aprovação exige responsável/data; achados de impostos separados não são bloqueios. Autorização e procedimento de anonimização para fixtures públicas continuam pendentes. Fase 1 com fixtures sintéticas permanece possível quando solicitada.

## Arquivos e commit

Alterados: `EcoWatt_PROJECT_SPEC.md`, `README.md`, `docs/contracts/invoice-data.md`, `docs/contracts/pipeline.md`, `docs/corpus/regulatory-review.md`, `docs/STATUS.md`. Novos/removidos: nenhum. Materiais reais e ferramentas locais fora do envio.

Commit desta entrega: `docs: distingue empresa ponto de conexao e indicios de mercado`. Consultar histórico remoto para o SHA; este status integra o próprio commit.
