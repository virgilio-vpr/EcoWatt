# Fase 2 — Coração 1/3: leitura e armazenamento

Objetivo: transformar cada PDF admitido em dados estruturados conferíveis, com descarte do original.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 4.2–4.4 (unidade, suporte ao layout e perfis), 5 (limites, descarte e leitura explícita), 6 (pipeline/qualidade), 7 (campos e demandas medidas por posto Azul/Verde), 8.6 (dependências de preço/mercado para o contrato, sem implementar o motor nesta fase), 10.1–10.4 (modelo/transações), 12 (isolamento do PDF), 13 (status/API), 14 (limites operacionais) e 15/Fase 2 (aceite).

## Entregas e ordem

1. Tabelas/migrações de faturas, medições, itens, proveniência e estado, após seus pais.
2. Salvar unidade/endereço; validar admissão apenas após essa etapa. No cabeçalho da anexação/leitura, identificar distribuidora/suporte ao layout e oferecer contato para não suportados, conforme §4.2; catálogo ANEEL não habilita parser.
3. Extração textual por adaptador e validações; OCR seletivo isolado quando necessário. Incluir demandas ativas medidas por posto no quadro de medição Azul/Verde, distintas da contratação, e preservar mercado/evidências por ciclo para o recorte ACL (§§7.1–7.3).
4. Gravação atômica, duplicidade/refaturamento, ordenação e revisão de campos.
5. Botão “Ler fatura”, consulta de estado, remoção/cancelamento e recuperação após interrupção.

Saída para cálculo: conjunto estruturado confirmado e versionado, nunca PDF/texto bruto persistente. Não exigir 12 faturas para liberar uma primeira análise.

Verificação: corpus textual/digitalizado/híbrido, arquivos inválidos, campos desconhecidos, rollback sem órfãos, retries, limites acumulados e resultados tardios após remoção. Auditar temporários e observabilidade antes de afirmar descarte. Aceite oficial na SPEC.
