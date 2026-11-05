# Estado do EcoWatt

Atualizado em 05/11/2026. Referência: SPEC versão 3.5.

## Entrega atual

Fase 0: proposta documental de contratos e casos sintéticos preparada. Aplicação e ambiente não iniciados. Fase 0 ainda não aceita: foram recebidos 12 PDFs e duas planilhas para análise local, mas faltam conferência do conteúdo, condições de uso/anonimização do corpus, gabarito aprovado e fixação das fontes regulatórias/tarifárias. Nenhuma fase ou critério composto da seção 15 foi marcado como concluído.

## Entregue

- Dicionário v0.1: tipos, unidades, obrigatoriedade, estados, proveniência, validações e campos desconhecidos.
- Contratos v0.1 entre leitura, persistência, motor e relatório, com revisão, idempotência e descarte.
- Matriz de acesso, separação dono/empresa/autor/titular e cota transacional de duas simulações, inclusive admin.
- Inventário local, pacote necessário para homologação, dúvidas e dependências com encaminhamento.
- Vinte casos sintéticos documentais, com entradas e esperados de aritmética, normalização, pendências e bloqueios. Não são testes de aplicação ou evidência comercial.

## Verificações realizadas

- Leitura dirigida da SPEC e ampliação para §§4–6, 8.1–8.2, 8.6–8.7, 10–12 e 17 pelas dependências dos contratos.
- Inventário atualizado: 12 PDFs em `docs/faturas`, sem hashes SHA-256 repetidos; nomes sugerem agosto/2025 a julho/2026, ainda sem conferência dos cabeçalhos. Duas planilhas em `docs/planilhas`: Azul com 5 abas/769 células com fórmulas e Verde com 3 abas/432 células com fórmulas, sem vínculos externos de workbook identificados. Estrutura XLSX lida em memória com recursos existentes; conteúdo financeiro ainda não validado.
- Recebido `docs/ANEEL/REN 1000.pdf`: presença, tamanho (3.919.570 bytes) e SHA-256 conferidos; identificação do hash em `docs/corpus/README.md`. Conteúdo, consolidação e aplicabilidade ainda não verificados; PDF permanece local.
- Conferidos destinos dos links Markdown locais e aritmética dos casos S01–S08 por PowerShell/.NET Decimal, sem instalar recursos ou executar aplicação.
- Nenhuma consulta regulatória externa, validação de parser/OCR, teste de concorrência, autorização ou persistência foi executado. Esses comportamentos estão especificados para testes futuros.

## Pendências e decisões preservadas

- Contratos são proposta para revisão; não há aprovação humana presumida. Questões D01–D08 e evidências necessárias: `docs/corpus/README.md`.
- PDFs e planilhas recebidos; ENEL SP A4 Azul, CNPJ/layout reais, correspondência das planilhas, tarifas por vigência, tributos, perdas e restrições contratuais ainda não conferidos/validados. Imagens descritas na SPEC não são fixtures homologadas.
- Sem administrador; instalações locais sujeitas às políticas da máquina. Esta entrega não instala dependências, cria ambiente, banco ou inicia containers/aplicação.
- Inspeção de ferramentas de 04/11/2026 é histórica; não comprova disponibilidade atual. Revalidar somente o necessário quando houver tarefa de ambiente.
- README contém passos futuros, sem pyproject, lockfile, migrações, seed ou comandos operacionais implementados.
- Em 05/11/2026, o usuário autorizou commits diretos em virgilio-vpr/EcoWatt sem confirmação no site, removendo a exigência de commit manual. Preferir integração GitHub e preservar alterações remotas. Não enviar `debug.log`, corpus real, banco, ambiente ou caches.

## Próximo passo

Conferir primeiro cabeçalho e linhas de uma fatura, depois a série e a correspondência das fórmulas das planilhas; construir gabarito estruturado sem publicar dados pessoais. Revisar contratos v0.1 e condições de uso do corpus, sem bloquear desenvolvimento independente. Quando autorizado em nova tarefa, iniciar a [Fase 1](phases/phase-01-backend.md), preparando ambiente local sem administrador/Docker e implementando modelos, autenticação, titularidade e cota com fixtures sintéticas. Homologação real permanece pendente.

## Arquivos da última entrega

Alterados: `docs/corpus/README.md` e `docs/STATUS.md` para registrar o recebimento da referência regulatória. Novos/removidos: nenhum documento. O PDF REN 1000 permanece local e não integra o commit. Nenhum aceite de homologação foi marcado.
