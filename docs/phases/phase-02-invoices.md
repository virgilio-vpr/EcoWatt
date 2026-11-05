# Fase 2 — Coração 1/3: leitura e armazenamento

Objetivo: transformar cada PDF admitido em dados estruturados conferíveis, com descarte do original.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 4.2–4.4 (unidade e perfis), 5 (limites, descarte e leitura explícita), 6 (pipeline/qualidade), 7 (campos), 10.1–10.4 (modelo/transações), 12 (isolamento do PDF), 13 (status/API), 14 (limites operacionais) e 15/Fase 2 (aceite).

## Entregas e ordem

1. Tabelas/migrações de faturas, medições, itens, proveniência e estado, após seus pais.
2. Salvar unidade/endereço; validar admissão apenas após essa etapa.
3. Extração textual por adaptador e validações; OCR seletivo isolado quando necessário.
4. Gravação atômica, duplicidade/refaturamento, ordenação e revisão de campos.
5. Botão “Ler fatura”, consulta de estado, remoção/cancelamento e recuperação após interrupção.

Saída para cálculo: conjunto estruturado confirmado e versionado, nunca PDF/texto bruto persistente. Não exigir 12 faturas para liberar uma primeira análise.

Verificação: corpus textual/digitalizado/híbrido, arquivos inválidos, campos desconhecidos, rollback sem órfãos, retries, limites acumulados e resultados tardios após remoção. Auditar temporários e observabilidade antes de afirmar descarte. Aceite oficial na SPEC.
