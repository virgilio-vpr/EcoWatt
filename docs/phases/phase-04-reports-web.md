# Fase 4 — Coração 3/3: relatório e interface

Objetivo: apresentar a execução calculada e concluir jornadas web do cliente/admin sem duplicar o motor.

## Leitura dirigida

Na [SPEC](../../EcoWatt_PROJECT_SPEC.md): 3.3 (camadas), 4 (jornadas), 5.4 (leitura e progresso), 8.8 (cenário manual), 11 (relatório/gráficos), 12 (HTML/CSRF/autorização), 13 (telas/temas/Tailwind) e 15/Fase 4 (aceite).

## Entregas sugeridas

1. Dados de relatório e séries compartilhadas pela web/PDF; geração autenticada de PDF.
2. Layouts/macros Jinja2, HTMX local, Tailwind compilado e temas claro/escuro.
3. Landing page e acesso; painel e etapas de unidade, leitura, conferência e resultado.
4. Atual/simulado na mesma escala, quadro de reativos, economia em R$ e memória de cálculo.
5. CRM essencial, notas internas, edição auditada e fluxo completo de simulação do admin.

Separar leitura JSON dos fragmentos HTML, mantendo serviços compartilhados. Não enviar notas internas a rotas de cliente. Respostas antigas de prévia não podem substituir cenário mais recente.

Verificação: jornada em celular/desktop, acessibilidade, dois temas, séries equivalentes no PDF, cota e acesso cruzado. Testar módulos parciais, estados de erro e revisões desatualizadas. Aceite oficial na SPEC; orçamento fica na Fase 6.
