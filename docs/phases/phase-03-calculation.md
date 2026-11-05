# Fase 3 — Coração 2/3: simulação

Objetivo: calcular custos e candidatos com entradas tipadas e resultados reproduzíveis, sem depender da apresentação.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 7 (contrato), 8 (regras dos módulos efetivamente implementados), 9 (catálogo/tarifas), 10.2 (Decimal/snapshots), 13 (execuções/prévias), 14 (desempenho) e 15/Fase 3 (aceite). Consultar 11.1–11.2 apenas para o formato das séries consumidas pelo relatório.

## Entregas e ordem

1. Motor puro e contrato de entrada/saída, com fixtures independentes do leitor.
2. Demanda regular/ultrapassagem e ociosidade; depois otimização e restrições por posto/conjunto.
3. Reativos observados, comparação de modalidade e bases equivalentes de preços/tributos.
4. Cenários encadeados, candidato manual, prévias e execuções congeladas com versões.

Validar apenas os módulos cujos dados/fontes estão disponíveis; bloquear ou condicionar os demais. Não usar hipótese oculta para completar uma análise.

Verificação: fronteiras, precisão, ausência versus zero, não duplicação, reconciliação e referência independente. Conferir custo adicional em candidatos desfavoráveis. Aceite oficial na SPEC; não alegar homologação regulatória só por passar testes sintéticos.
